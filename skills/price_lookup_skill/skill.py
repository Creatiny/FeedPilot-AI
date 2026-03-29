"""
FeedSales AI - 价格查询技能

查询原料价格，支持私有优先 (v1.7)
"""

import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PriceLookupSkill:
    """价格查询技能"""
    
    def __init__(self, price_repo=None, price_service=None):
        """
        初始化技能
        
        Args:
            price_repo: 价格仓库 (legacy)
            price_service: PriceService 实例 (v1.7+)
        """
        self.price_repo = price_repo
        self.price_service = price_service
    
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
            
            # 检测操作类型
            action = self._detect_action(message)
            
            if action == 'set':
                return self._handle_set_price(user_id, message)
            elif action == 'list':
                return self._handle_list_prices(user_id)
            else:
                return self._handle_query_price(user_id, message)
            
        except Exception as e:
            logger.error(f"价格查询失败：{e}")
            return self._error(f"查询失败：{str(e)}")
    
    def _detect_action(self, message: str) -> str:
        """检测操作类型"""
        if re.search(r'(设置|更新|修改).*价格', message):
            return 'set'
        if re.search(r'(列出|所有|全部).*价格', message):
            return 'list'
        return 'query'
    
    def _handle_query_price(self, user_id: str, message: str) -> Dict[str, Any]:
        """处理价格查询"""
        ingredient = self._extract_ingredient(message)
        if not ingredient:
            return self._error("未找到原料名称，请明确指定原料")
        
        if self.price_service:
            result = self.price_service.get_price(user_id, ingredient)
            if result.success:
                return self._success({
                    'ingredient_name': result.data['ingredient_name'],
                    'price': result.data['price'],
                    'currency': result.data.get('currency', 'USD'),
                    'unit': result.data.get('unit', 'ton'),
                    'source': result.source
                })
            else:
                # 使用默认价格
                price = self._get_default_price(ingredient)
                return self._success({
                    'ingredient_name': ingredient,
                    'price': price,
                    'currency': 'USD',
                    'unit': 'ton',
                    'source': 'default'
                })
        
        # Legacy mode
        if self.price_repo:
            price_data = self.price_repo.get_latest_price(user_id, f"ING_{ingredient}")
            if price_data:
                return self._success(price_data)
        
        # 默认价格
        price = self._get_default_price(ingredient)
        return self._success({
            'ingredient_name': ingredient,
            'price': price,
            'source': 'default'
        })
    
    def _handle_set_price(self, user_id: str, message: str) -> Dict[str, Any]:
        """处理设置私有价格"""
        ingredient = self._extract_ingredient(message)
        if not ingredient:
            return self._error("未找到原料名称")
        
        # 提取价格数字
        match = re.search(r'(\d+(?:\.\d+)?)', message)
        if not match:
            return self._error("未找到价格数字")
        
        price = float(match.group(1))
        
        if self.price_service:
            result = self.price_service.set_private_price(user_id, ingredient, price)
            if result.success:
                return self._success({
                    'message': f'已设置 {ingredient} 私有价格为 ${price}/ton'
                })
            else:
                return self._error(result.error_message)
        
        return self._error("价格服务未初始化")
    
    def _handle_list_prices(self, user_id: str) -> Dict[str, Any]:
        """处理列出价格"""
        if self.price_service:
            # 列出公共价格
            public = self.price_service.list_public_prices()
            # 列出私有价格
            private = self.price_service.list_private_prices(user_id)
            
            all_prices = []
            seen = set()
            
            for p in private.data.get('prices', []):
                key = p['ingredient_name']
                if key not in seen:
                    p['source'] = 'private'
                    all_prices.append(p)
                    seen.add(key)
            
            for p in public.data.get('prices', []):
                key = p['ingredient_name']
                if key not in seen:
                    p['source'] = 'public'
                    all_prices.append(p)
                    seen.add(key)
            
            return self._success({
                'prices': all_prices,
                'total': len(all_prices)
            })
        
        return self._error("价格服务未初始化")
    
    def _extract_ingredient(self, message: str) -> Optional[str]:
        """从消息中提取原料名称"""
        # 英文原料名映射
        ingredient_map = {
            'corn': 'Corn, grain',
            'corn, grain': 'Corn, grain',
            'soybean': 'Soybean meal, 48%',
            'soybean meal': 'Soybean meal, 48%',
            'fish meal': 'Fish meal, 65%',
            'wheat': 'Wheat middlings',
            'limestone': 'Limestone, ag',
            'premix': 'Premix, swine',
            'dicalcium': 'Dicalcium phosphate',
            'salt': 'Salt, white',
            'lysine': 'L-Lysine HCl',
            'methionine': 'DL-Methionine',
            # 中文映射
            '玉米': 'Corn, grain',
            '豆粕': 'Soybean meal, 48%',
            '鱼粉': 'Fish meal, 65%',
            '小麦': 'Wheat middlings',
            '石粉': 'Limestone, ag',
            '预混料': 'Premix, swine',
            '磷酸氢钙': 'Dicalcium phosphate',
            '盐': 'Salt, white',
            '赖氨酸': 'L-Lysine HCl',
            '蛋氨酸': 'DL-Methionine',
        }
        
        message_lower = message.lower()
        for key, value in ingredient_map.items():
            if key in message_lower:
                return value
        
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
