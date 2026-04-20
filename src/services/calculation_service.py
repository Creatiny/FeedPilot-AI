"""
FeedSales AI - CalculationService

配方成本计算服务，整合配方和价格，支持私有优先
import sys as _sys
from pathlib import _Path
if _Path(__file__).parent.parent not in _sys.path:
    _sys.path.insert(0, str(_Path(__file__).parent.parent))
"""

import logging
from typing import Dict, List, Optional
from ..database.pool import DatabasePool
from .formula_service import FormulaService
from .price_service import PriceService
from ..result_types import ServiceResult

logger = logging.getLogger(__name__)


# 默认价格（当找不到价格时使用）
DEFAULT_PRICES = {
    'Corn': 180.00,
    'Soybean meal': 350.00,
    'Fish meal': 1800.00,
    'Wheat': 200.00,
    'Limestone': 120.00,
    'Premix': 450.00,
    'Dicalcium phosphate': 650.00,
    'Salt': 150.00,
    'L-Lysine': 1200.00,
    'Methionine': 2500.00,
}


class CalculationService:
    """配方成本计算服务"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self.formula_service = FormulaService(db_pool)
        self.price_service = PriceService(db_pool)
    
    def calculate_cost(self, user_id: str, formula_name: str) -> ServiceResult:
        """
        计算配方成本（优化版，避免 N+1 查询）
        
        Args:
            user_id: 用户 ID
            formula_name: 配方名称
            
        Returns:
            ServiceResult: 包含成本详情
        """
        # 1. 获取配方
        formula_result = self.formula_service.get_formula(user_id, formula_name)
        if not formula_result.success:
            return ServiceResult(
                success=False,
                error_code=formula_result.error_code,
                error_message=formula_result.error_message
            )
        
        formula = formula_result.data
        formula_source = formula_result.source
        
        # 2. 批量获取价格（优化 N+1 问题）
        ingredients = formula.get('ingredients', [])
        ingredient_codes = [ing['ingredient_code'] for ing in ingredients]
        
        # 批量查询价格
        prices = self._batch_get_prices(user_id, ingredient_codes)
        
        # 3. 计算成本
        details = []
        total_cost = 0.0
        price_sources = {}
        missing_prices = []
        
        for ingredient in ingredients:
            name = ingredient['name']
            code = ingredient['ingredient_code']
            ratio = ingredient['ratio']  # 百分比
            
            # 从批量结果中获取价格
            price_info = prices.get(code)
            
            if price_info:
                price = price_info['price']
                price_source = price_info['source']
            else:
                # 使用默认价格
                price = self._get_default_price(name)
                price_source = 'default'
                missing_prices.append(name)
            
            # 计算该成分的成本贡献
            cost = price * ratio / 100.0
            total_cost += cost
            
            details.append({
                'name': name,
                'ingredient_code': code,
                'ratio': ratio,
                'price': price,
                'cost': round(cost, 2),
                'price_source': price_source
            })
            
            price_sources[code] = price_source
        
        return ServiceResult(
            success=True,
            data={
                'formula_name': formula_name,
                'animal_type': formula.get('animal_type'),
                'stage_type': formula.get('stage_type'),
                'total_cost': round(total_cost, 2),
                'currency': 'USD',
                'unit': 'ton',
                'details': details,
                'price_sources': price_sources,
                'missing_prices': missing_prices,
                'formula_source': formula_source
            }
        )
    
    def _batch_get_prices(self, user_id: str, ingredient_codes: List[str]) -> Dict:
        """
        批量获取原料价格（优化 N+1 查询）
        
        Args:
            user_id: 用户 ID
            ingredient_codes: 原料代码列表
            
        Returns:
            Dict: {ingredient_code: {price, source}}
        """
        results = {}
        
        # 批量查询私有价格
        private_prices = self.price_service._batch_get_private_prices(user_id, ingredient_codes)
        
        # 批量查询公共价格（仅查询私有价格未覆盖的）
        missing_codes = [code for code in ingredient_codes if code not in private_prices]
        public_prices = self.price_service._batch_get_public_prices(missing_codes)
        
        # 合并结果（私有优先）
        for code in ingredient_codes:
            if code in private_prices:
                results[code] = {
                    'price': private_prices[code]['price'],
                    'source': 'private'
                }
            elif code in public_prices:
                results[code] = {
                    'price': public_prices[code]['price'],
                    'source': 'public'
                }
        
        return results
    
    def compare_formulas(self, user_id: str, names: List[str]) -> ServiceResult:
        """
        对比多个配方成本
        
        Args:
            user_id: 用户 ID
            names: 配方名称列表
            
        Returns:
            ServiceResult: 包含对比结果
        """
        results = []
        
        for name in names:
            result = self.calculate_cost(user_id, name)
            if result.success:
                results.append({
                    'name': name,
                    'total_cost': result.data['total_cost'],
                    'formula_source': result.data['formula_source']
                })
        
        if not results:
            return ServiceResult(
                success=False,
                error_code='E002',
                error_message='No formulas found'
            )
        
        # 排序（按成本）
        results.sort(key=lambda x: x['total_cost'])
        
        return ServiceResult(
            success=True,
            data={
                'formulas': results,
                'total': len(results)
            }
        )
    
    def _get_default_price(self, ingredient_name: str) -> float:
        """获取默认价格"""
        for key, price in DEFAULT_PRICES.items():
            if key.lower() in ingredient_name.lower():
                return price
        return 300.00  # 通用默认值

    def generate_quote(self, user_id: str, formula_name: str,
                       customer_name: str, margin_percent: float = 0.0) -> ServiceResult:
        """
        生成报价单

        Args:
            user_id: 用户 ID
            formula_name: 配方名称
            customer_name: 客户名称
            margin_percent: 利润率（%），默认0

        Returns:
            ServiceResult: 包含完整报价单数据
        """
        # 1. 计算配方成本
        cost_result = self.calculate_cost(user_id, formula_name)
        if not cost_result.success:
            return ServiceResult(
                success=False,
                error_code=cost_result.error_code,
                error_message=f"Cannot generate quote: {cost_result.error_message}"
            )

        cost_data = cost_result.data
        base_cost = cost_data['total_cost']

        # 2. 获取客户信息（用于报价单显示）
        from .customer_service import CustomerService
        customer_svc = CustomerService(self.db_pool)
        customer_result = customer_svc.get_customer(user_id, customer_name)

        customer_info = None
        if customer_result.success:
            c = customer_result.data
            customer_info = {
                'name': c.get('name', customer_name),
                'phone': c.get('phone'),
                'address': c.get('address'),
                'animal_type': c.get('animal_type'),
                'scale': c.get('scale'),
            }
        else:
            # 客户不存在，但报价单仍可生成
            customer_info = {'name': customer_name, 'phone': None}

        # 3. 计算报价
        margin_amount = base_cost * (margin_percent / 100.0)
        quote_price = base_cost + margin_amount

        # 4. 生成报价单
        from datetime import datetime, date
        quote_date = date.today().isoformat()
        quote_number = f"Q-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        quote = {
            'quote_number': quote_number,
            'quote_date': quote_date,
            'customer': customer_info,
            'formula': {
                'name': formula_name,
                'animal_type': cost_data.get('animal_type'),
                'stage_type': cost_data.get('stage_type'),
            },
            'base_cost_per_ton': base_cost,
            'margin_percent': margin_percent,
            'margin_amount': round(margin_amount, 2),
            'quote_price_per_ton': round(quote_price, 2),
            'currency': 'USD',
            'unit': 'ton',
            'ingredients': cost_data.get('details', []),
            'price_sources': cost_data.get('price_sources', {}),
            'formula_source': cost_data.get('formula_source', 'unknown'),
            'validity_days': 30,
            'notes': f"Quote valid for 30 days. Margin: {margin_percent}%. "
                     f"Generated automatically by FeedSales AI.",
        }

        # 5. 保存报价历史（可选）
        try:
            self._save_quote_history(user_id, quote)
        except Exception as e:
            logger.warning(f"Failed to save quote history: {e}")

        return ServiceResult(
            success=True,
            data=quote,
            source='quote_generated'
        )

    def _save_quote_history(self, user_id: str, quote: Dict) -> None:
        """保存报价历史"""
        import json
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO calculation_history
                (owner_open_id, formula_name, total_cost, cost_per_ton, ingredients_json, data_source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                quote['formula']['name'],
                quote['base_cost_per_ton'],
                quote['quote_price_per_ton'],
                json.dumps({
                    'quote_number': quote['quote_number'],
                    'customer': quote['customer']['name'],
                    'margin': quote['margin_percent'],
                    'ingredients': [d['name'] for d in quote['ingredients']]
                }),
                'quote_generation'
            ))
            conn.commit()