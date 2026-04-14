"""
FeedSales AI - Price Lookup Skill

Query ingredient prices. Supports auto-adding missing ingredients.
Uses PriceService (v1.7 architecture).

Requires PriceService to be injected at initialization.
"""

import logging
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


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
            price_service: PriceService instance (required)
        """
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
                # 将原料名称转换为 ingredient_code（按设计文档：价格查询使用精确的 ingredient_code）
                ingredient_code = self._generate_ingredient_code(ingredient)
                result = self.price_service.get_price(user_id, ingredient_code)
                
                if result.success:
                    data = result.data
                    return self._success({
                        'ingredient': data.get('ingredient_name', ingredient),
                        'ingredient_code': ingredient_code,
                        'price': data.get('price'),
                        'currency': data.get('currency', 'USD'),
                        'unit': data.get('unit', 'ton'),
                        'date': data.get('price_date'),
                        'source': result.source,
                    })
                else:
                    # Try auto-add if not found
                    if 'not found' in result.error_message.lower():
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
        
        # Match known ingredients
        for keyword in self.INGREDIENT_KEYWORDS:
            if keyword.lower() in msg_lower:
                return keyword
        
        # Pattern: xxx price / price of xxx
        match = re.search(r'(?:price\s+(?:of\s+)?|(.+?)\s+price)', message, re.IGNORECASE)
        if match:
            name = match.group(1) if match.group(1) else match.group(0)
            name = name.replace('price', '').replace('of', '').strip()
            if name and len(name) < 30:
                return name
        
        return None
    
    def _generate_ingredient_code(self, ingredient_name: str) -> str:
        """将原料名称转换为 ingredient_code"""
        code_map = {
            'Corn': 'ING_CORN',
            'Soybean meal': 'ING_SBM',
            'Soybean': 'ING_SBM',
            'Fish meal': 'ING_FISHM',
            'Wheat': 'ING_WHEAT',
            'Barley': 'ING_BARLEY',
            'Rice': 'ING_RICE',
            'DDGS': 'ING_DDGS',
            'Canola meal': 'ING_CANOLA',
            'Cottonseed meal': 'ING_COTTON',
            'Dicalcium phosphate': 'ING_DCP',
            'Limestone': 'ING_LIME',
            'Salt': 'ING_SALT',
            'L-Lysine': 'ING_LYS',
            'Lysine': 'ING_LYS',
            'DL-Methionine': 'ING_MET',
            'Methionine': 'ING_MET',
            'Premix': 'ING_PREMIX',
            'Alfalfa': 'ING_ALFALFA',
            'Corn silage': 'ING_SILAGE',
            'Grass hay': 'ING_HAY',
            'Molasses': 'ING_MOLASSES',
        }
        for key, code in code_map.items():
            if key.lower() in ingredient_name.lower():
                return code
        return 'ING_' + ingredient_name.split(',')[0].upper().replace(' ', '_')[:15]
    
    def _try_auto_add(self, ingredient: str) -> Dict:
        """Try to auto-add missing ingredient"""
        try:
            from scripts.auto_add_ingredient import auto_add_ingredient
            
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
                
        except ImportError:
            return self._error(f"Ingredient '{ingredient}' not found. Auto-add not available.")
        except Exception as e:
            return self._error(f"Auto-add failed: {str(e)}")
    
    def _success(self, data: Dict) -> Dict:
        return {'success': True, 'data': data}
    
    def _error(self, msg: str) -> Dict:
        return {'success': False, 'error': msg}


def create_skill(price_service):
    """Factory function - requires PriceService"""
    return PriceLookupSkill(price_service)
