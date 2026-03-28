"""
FeedSales AI - 配方成本计算技能

计算饲料配方成本
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FormulaCostSkill:
    """配方成本计算技能"""
    
    def __init__(self, db_pool=None, formula_repo=None, price_repo=None):
        """
        初始化技能
        
        Args:
            db_pool: 数据库连接池
            formula_repo: 配方仓库
            price_repo: 价格仓库
        """
        self.db_pool = db_pool
        self.formula_repo = formula_repo
        self.price_repo = price_repo
    
    async def execute(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            user_id: 用户 ID
            message: 用户消息
            
        Returns:
            Dict: 执行结果
        """
        try:
            logger.info(f"执行配方成本计算 (用户：{user_id})")
            
            # 从消息中提取配方名称
            formula_name = self._extract_formula_name(message)
            if not formula_name:
                return self._error("未找到配方名称，请明确指定配方")
            
            # 获取配方数据
            formula = self.formula_repo.get_formula(user_id, formula_name)
            if not formula:
                return self._error(f"配方不存在：{formula_name}")
            
            # 计算成本
            cost_data = self._calculate_cost(formula)
            
            logger.info(f"配方成本计算完成：{formula_name}")
            return self._success(cost_data)
            
        except Exception as e:
            logger.error(f"配方成本计算失败：{e}")
            return self._error(f"计算失败：{str(e)}")
    
    def _extract_formula_name(self, message: str) -> Optional[str]:
        """从消息中提取配方名称"""
        import re
        
        # 简单匹配：计算 xxx 的成本
        match = re.search(r'计算 (.*?) 的成本', message)
        if match:
            return match.group(1).strip()
        
        # 匹配：xxx 配方
        match = re.search(r'(.*?配方)', message)
        if match:
            return match.group(1).strip()
        
        return None
    
    def _calculate_cost(self, formula: Dict) -> Dict[str, Any]:
        """计算配方成本"""
        ingredients = formula.get('ingredients', [])
        total_cost = 0.0
        cost_details = []
        
        for ingredient in ingredients:
            ingredient_name = ingredient.get('name')
            ratio = ingredient.get('ratio', 0)
            
            # 获取价格（简化版，使用默认价格）
            price = self._get_default_price(ingredient_name)
            
            # 计算成本
            cost = price * ratio / 100.0
            total_cost += cost
            
            cost_details.append({
                'name': ingredient_name,
                'ratio': ratio,
                'price': price,
                'cost': cost
            })
        
        return {
            'formula_name': formula.get('name'),
            'cost_per_ton': round(total_cost, 2),
            'cost_per_kg': round(total_cost / 1000, 2),
            'ingredients': cost_details
        }
    
    def _get_default_price(self, ingredient_name: str) -> float:
        """获取默认价格"""
        default_prices = {
            '玉米': 2800.00,
            '豆粕': 4200.00,
            '豆油': 6500.00,
            '小麦': 2700.00,
            '鱼粉': 9000.00,
            '预混料': 3200.00,
        }
        return default_prices.get(ingredient_name, 3000.00)
    
    def _success(self, data: Dict) -> Dict[str, Any]:
        """成功响应"""
        return {
            'success': True,
            'data': data
        }
    
    def _error(self, message: str) -> Dict[str, Any]:
        """错误响应"""
        return {
            'success': False,
            'error': message
        }


# 技能工厂函数
def create_skill(db_pool, formula_repo, price_repo):
    """创建技能实例"""
    return FormulaCostSkill(db_pool, formula_repo, price_repo)
