"""
FeedSales AI - 价格查询技能

查询原料价格
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PriceLookupSkill:
    """价格查询技能"""
    
    def __init__(self, price_repo=None):
        """
        初始化技能
        
        Args:
            price_repo: 价格仓库
        """
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
            logger.info(f"执行价格查询 (用户：{user_id})")
            
            # 从消息中提取原料名称
            ingredient = self._extract_ingredient(message)
            if not ingredient:
                return self._error("未找到原料名称，请明确指定原料")
            
            # 查询价格
            price_data = self.price_repo.get_latest_price(user_id, f"ING_{ingredient}")
            
            if not price_data:
                # 使用默认价格
                price = self._get_default_price(ingredient)
                price_data = {
                    'ingredient_name': ingredient,
                    'price': price,
                    'source': 'default'
                }
            
            logger.info(f"价格查询完成：{ingredient}")
            return self._success(price_data)
            
        except Exception as e:
            logger.error(f"价格查询失败：{e}")
            return self._error(f"查询失败：{str(e)}")
    
    def _extract_ingredient(self, message: str) -> Optional[str]:
        """从消息中提取原料名称"""
        import re
        
        # 匹配常见原料（英文名称，北美市场）
        ingredients = ['Corn', 'Soybean meal', 'Fish meal', 'Wheat', 'Limestone', 
                       'Premix', 'Dicalcium phosphate', 'Salt', 'L-Lysine', 'Methionine']
        for ingredient in ingredients:
            if ingredient.lower() in message.lower():
                return ingredient
        
        return None
    
    def _get_default_price(self, ingredient: str) -> float:
        """获取默认价格（USD/ton）"""
        default_prices = {
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
        return default_prices.get(ingredient, 300.00)
    
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
def create_skill(price_repo):
    """创建技能实例"""
    return PriceLookupSkill(price_repo)
