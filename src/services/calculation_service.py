"""
FeedSales AI - CalculationService

配方成本计算服务，整合配方和价格，支持私有优先
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from ..database.pool import DatabasePool
from .formula_service import FormulaService
from .price_service import PriceService

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


@dataclass
class ServiceResult:
    """服务返回结果"""
    success: bool
    data: Optional[Dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class CalculationService:
    """配方成本计算服务"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self.formula_service = FormulaService(db_pool)
        self.price_service = PriceService(db_pool)
    
    def calculate_cost(self, user_id: str, formula_name: str) -> ServiceResult:
        """
        计算配方成本
        
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
        
        # 2. 计算成本
        details = []
        total_cost = 0.0
        price_sources = {}
        missing_prices = []
        
        for ingredient in formula.get('ingredients', []):
            name = ingredient['name']
            ratio = ingredient['ratio']  # 百分比
            
            # 获取价格（私有优先）
            price_result = self.price_service.get_price(user_id, name)
            
            if price_result.success:
                price = price_result.data['price']
                price_source = price_result.source
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
                'ratio': ratio,
                'price': price,
                'cost': round(cost, 2),
                'price_source': price_source
            })
            
            price_sources[name] = price_source
        
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
                error_message='没有找到任何配方'
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