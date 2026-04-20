"""
FeedSales AI - Price Lookup Skill

Query ingredient prices. Supports auto-adding missing ingredients.
Uses PriceService (v1.7 architecture).

Requires PriceService to be injected at initialization.
"""

import logging
import re
import sys
from pathlib import Path as _Path
from typing import Dict, Any, Optional, List

# 添加项目根目录到路径
if str(_Path(__file__).parent.parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(_Path(__file__).parent.parent.parent.parent))

from src.utils.ingredient_codes import generate_ingredient_code

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
        Execute skill - lookup or set ingredient prices

        Args:
            user_id: User ID
            message: Message with ingredient name or price setting command

        Returns:
            Dict with price data or operation result
        """
        try:
            logger.info(f"PriceLookupSkill.execute: {message[:50]}...")

            if not self.price_service:
                return self._error("PriceService not initialized")

            # Check for private price setting commands
            set_match = re.search(
                r'(?:set|update|change)\s+(?:my\s+)?(.+?)\s+(?:price\s+)?(?:to|=|at|:)\s*(\d+(?:\.\d+)?)',
                message, re.IGNORECASE
            )
            if set_match:
                ingredient_name = set_match.group(1).strip()
                price = float(set_match.group(2))
                return self._set_private_price(user_id, ingredient_name, price)

            # Check for list private prices command
            if re.search(r'(?:my\s+)?private\s+price', message, re.IGNORECASE):
                return self._list_private_prices(user_id)

            # Find ingredient name
            ingredient = self._find_ingredient(message)

            if ingredient:
                # 将原料名称转换为 ingredient_code（按设计文档：价格查询使用精确的 ingredient_code）
                ingredient_code = generate_ingredient_code(ingredient)
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
        """Ingredient name matching with word boundary awareness.
        
        Uses word-boundary matching to avoid false positives like
        'rice' matching inside 'price'.
        """
        msg_lower = message.lower()
        
        # Skip if message is asking for "all prices" or list
        if 'all' in msg_lower or 'list' in msg_lower or 'show' in msg_lower:
            return None
        
        # Match known ingredients using word-boundary regex
        # Sort by length descending so longer names match first
        # (e.g. "Soybean meal" before "Soybean", "Fish meal" before "Fish")
        sorted_keywords = sorted(self.INGREDIENT_KEYWORDS, key=len, reverse=True)
        for keyword in sorted_keywords:
            # Use word boundary: the keyword must appear as a whole word/phrase
            # \b doesn't work well for multi-word, so check with boundaries manually
            pattern = r'(?<![a-z])' + re.escape(keyword.lower()) + r'(?![a-z])'
            if re.search(pattern, msg_lower):
                return keyword
        
        # Pattern: xxx price / price of xxx
        match = re.search(r'price\s+of\s+(.+?)(?:\s*$|\s*\?)', message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if name and len(name) < 30:
                return name
        
        match = re.search(r'(.+?)\s+price', message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Filter out common non-ingredient words
            for skip in ['what', 'the', 'current', 'today', 'latest', 'show', 'all']:
                name = re.sub(r'\b' + skip + r'\b', '', name, flags=re.IGNORECASE).strip()
            if name and len(name) < 30:
                return name
        
        return None
    
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

    def _set_private_price(self, user_id: str, ingredient_name: str, price: float) -> Dict:
        """Set a private price for an ingredient"""
        if price <= 0:
            return self._error("Price must be greater than 0")

        result = self.price_service.set_private_price(user_id, ingredient_name, price)

        if result.success:
            return self._success({
                'message': f"Private price for '{ingredient_name}' set to ${price:.2f}/ton",
                'ingredient': ingredient_name,
                'price': price,
                'currency': 'USD',
                'unit': 'ton',
                'source': 'private',
            })
        else:
            return self._error(result.error_message)

    def _list_private_prices(self, user_id: str) -> Dict:
        """List all private prices for a user"""
        result = self.price_service.list_private_prices(user_id)

        if result.success:
            prices = result.data.get('prices', [])
            if not prices:
                return self._success({
                    'message': 'No private prices set. Use "set my [ingredient] price to [price]" to add one.',
                    'count': 0,
                    'prices': [],
                })
            return self._success({
                'message': f'Found {len(prices)} private price(s)',
                'count': len(prices),
                'prices': prices,
            })
        else:
            return self._error(result.error_message)


def create_skill(price_service):
    """Factory function - requires PriceService"""
    return PriceLookupSkill(price_service)
