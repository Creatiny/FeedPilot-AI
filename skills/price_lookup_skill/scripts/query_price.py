"""
FeedSales AI - Price Lookup Skill

Query ingredient prices. Supports auto-adding missing ingredients.
Uses PriceService (v1.7 architecture).

Auto-initializes Service layer if not injected.
"""

import logging
import re
import os
import sys
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# 自动初始化 Service 层
def _init_services():
    """初始化 Service 层（用于 OpenClaw 环境）"""
    try:
        # workspace-feedsales 目录 (scripts -> skill -> skills -> workspace-feedsales)
        workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        # 添加项目根目录到 sys.path 以便导入 utils
        if workspace not in sys.path:
            sys.path.insert(0, workspace)
        
        # 直接用 sqlite3 连接，避免相对导入问题
        import sqlite3
        from src.utils.ingredient_codes import generate_ingredient_code
        
        db_path = os.path.join(workspace, 'data', 'feed_sales.db')
        
        class SimplePriceService:
            """简化版 PriceService，用于技能直接查询"""
            
            def _generate_ingredient_code(self, ingredient_name: str) -> str:
                """废弃：使用共享的 generate_ingredient_code 函数"""
                return generate_ingredient_code(ingredient_name)
            
            def get_price(self, user_id: str, ingredient_name: str):
                # 将 ingredient_name 转换为 ingredient_code（按设计文档：精确匹配）
                ingredient_code = generate_ingredient_code(ingredient_name)
                
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT ingredient_code, ingredient_name, price, currency, unit, source, price_date
                    FROM ingredient_prices
                    WHERE owner_open_id = ? AND ingredient_code = ?
                    ORDER BY price_date DESC
                    LIMIT 1
                ''', ('system_public', ingredient_code))
                
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return _ServiceResult(
                        success=True,
                        data=dict(row),
                        source='public'
                    )
                else:
                    return _ServiceResult(
                        success=False,
                        error_code='E002',
                        error_message=f"原料 '{ingredient_name}' ({ingredient_code}) 价格不存在"
                    )
            
            def list_public_prices(self):
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT ingredient_code, ingredient_name, price, currency, unit, source, price_date
                    FROM ingredient_prices
                    WHERE owner_open_id = 'system_public'
                    ORDER BY ingredient_name
                ''')
                
                prices = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                return _ServiceResult(
                    success=True,
                    data={'prices': prices, 'total': len(prices)}
                )
        
        return SimplePriceService()
    except Exception as e:
        logger.warning(f"Service auto-init failed: {e}")
        return None


# ServiceResult 类型定义（避免相对导入）
class _ServiceResult:
    """服务返回结果"""
    def __init__(self, success: bool, data=None, source=None, error_code=None, error_message=None):
        self.success = success
        self.data = data
        self.source = source
        self.error_code = error_code
        self.error_message = error_message


class PriceLookupSkill:
    """Ingredient price lookup skill with auto-add support"""
    
    INGREDIENT_KEYWORDS = [
        "Corn", "Soybean meal", "Wheat", "Barley", "Rice",
        "Fish meal", "DDGS", "Canola meal", "Cottonseed meal",
        "Dicalcium phosphate", "Limestone", "Salt",
        "L-Lysine", "DL-Methionine", "Premix",
        "Alfalfa", "Corn silage", "Grass hay", "Molasses",
    ]
    
    def __init__(self, price_service=None):
        """
        Initialize skill
        
        Args:
            price_service: PriceService instance (optional, will auto-init if None)
        """
        if price_service is None:
            price_service = _init_services()
        self.price_service = price_service
    
    async def execute(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Execute skill - lookup ingredient prices
        
        Args:
            user_id: User ID
            message: Message with ingredient name
            
        Returns:
            Dict with price data
        """
        try:
            logger.info(f"PriceLookupSkill.execute: {message[:50]}...")
            
            if not self.price_service:
                return self._error("PriceService not initialized")
            
            # Find ingredient name
            ingredient = self._find_ingredient(message)
            
            if ingredient:
                # Single ingredient query
                result = self.price_service.get_price(user_id, ingredient)
                
                if result.success:
                    data = result.data
                    return self._success({
                        'ingredient': data.get('ingredient_name', ingredient),
                        'price': data.get('price'),
                        'currency': data.get('currency', 'USD'),
                        'unit': data.get('unit', 'ton'),
                        'date': data.get('price_date'),
                        'source': result.source,
                    })
                else:
                    # Try auto-add if not found (检查中文和英文两种情况)
                    if 'not found' in result.error_message.lower() or '不存在' in result.error_message or '未找到' in result.error_message:
                        return self._try_auto_add(ingredient)
                    else:
                        return self._error(result.error_message)
            else:
                # Return all prices if no specific ingredient
                result = self.price_service.list_public_prices()
                
                if result.success:
                    prices = result.data.get('prices', [])
                    return self._success({
                        'message': 'All ingredient prices',
                        'count': len(prices),
                        'prices': prices[:20],  # Limit to 20
                    })
                else:
                    return self._error(result.error_message)
                
        except Exception as e:
            logger.error(f"PriceLookupSkill error: {e}")
            return self._error(f"Lookup failed: {str(e)}")
    
    def _find_ingredient(self, message: str) -> Optional[str]:
        """Simple ingredient name matching"""
        msg_lower = message.lower()
        
        # Skip if message is asking for "all prices" or list
        if 'all' in msg_lower or 'list' in msg_lower or 'show' in msg_lower:
            return None
        
        # Match known ingredients (使用单词边界匹配，避免 "rice" 匹配到 "price")
        for keyword in self.INGREDIENT_KEYWORDS:
            # 使用正则表达式确保单词边界
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', msg_lower):
                return keyword
        
        # Pattern: xxx price / price of xxx
        match = re.search(r'(?:price\s+(?:of\s+)?|(.+?)\s+price)', message, re.IGNORECASE)
        if match:
            name = match.group(1) if match.group(1) else match.group(0)
            name = name.replace('price', '').replace('of', '').strip()
            if name and len(name) < 30:
                return name
        
        return None
    
    def _try_auto_add(self, ingredient: str) -> Dict:
        """Try to auto-add missing ingredient"""
        try:
            import os
            import sys
            
            # workspace-feedsales 目录 (scripts -> skill -> skills -> workspace-feedsales)
            workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            scripts_path = os.path.join(workspace, 'scripts')
            if scripts_path not in sys.path:
                sys.path.insert(0, scripts_path)
            
            from auto_add_ingredient import auto_add_ingredient
            
            result = auto_add_ingredient(ingredient)
            
            if result.get('success'):
                data = result.get('data', {})
                return self._success({
                    'ingredient': data.get('name', ingredient),
                    'price': data.get('price'),
                    'currency': 'USD',
                    'unit': 'ton',
                    'source': data.get('source', 'auto'),
                    'auto_added': True,
                    'message': result.get('message', 'Ingredient auto-added'),
                })
            else:
                return self._error(result.get('message', f"Could not auto-add '{ingredient}'"))
                
        except ImportError as e:
            logger.warning(f"Auto-add import failed: {e}")
            return self._error(f"Ingredient '{ingredient}' not found. Auto-add not available.")
        except Exception as e:
            logger.error(f"Auto-add failed: {e}")
            return self._error(f"Auto-add failed: {str(e)}")
    
    def _success(self, data: Dict) -> Dict:
        return {'success': True, 'data': data}
    
    def _error(self, msg: str) -> Dict:
        return {'success': False, 'error': msg}


def create_skill(price_service=None):
    """Factory function - auto-initializes if no Service provided"""
    return PriceLookupSkill(price_service)


# Command-line entry point
if __name__ == "__main__":
    import asyncio
    import json
    
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': 'Usage: query_price.py <ingredient_name>'}))
        sys.exit(1)
    
    ingredient_name = sys.argv[1]
    
    skill = create_skill()
    result = asyncio.run(skill.execute('cli_user', f'{ingredient_name} price'))
    
    print(json.dumps(result, indent=2))