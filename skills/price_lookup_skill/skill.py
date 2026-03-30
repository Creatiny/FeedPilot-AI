"""
FeedSales AI - Price Lookup Skill

Query ingredient prices. Uses PriceService (v1.7 architecture).
"""

import logging
import re
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get('FEEDSALES_DB_PATH', 'data/feed_sales.db')


class PriceLookupSkill:
    """Ingredient price lookup skill"""
    
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
            price_service: PriceService instance (injected or auto-created)
        """
        self.price_service = price_service
        
        # Auto-initialize if not injected
        if self.price_service is None:
            try:
                from src.database.pool import DatabasePool
                from src.services.price_service import PriceService
                db_pool = DatabasePool(DB_PATH)
                self.price_service = PriceService(db_pool)
            except ImportError as e:
                logger.warning(f"PriceLookupSkill: Could not import Service layer: {e}")
    
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
                        'ingredient': data['ingredient_name'],
                        'price': data['price'],
                        'currency': data.get('currency', 'USD'),
                        'unit': data.get('unit', 'ton'),
                        'date': data.get('price_date'),
                        'source': result.source,
                    })
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
    
    def _success(self, data: Dict) -> Dict:
        return {'success': True, 'data': data}
    
    def _error(self, msg: str) -> Dict:
        return {'success': False, 'error': msg}


def create_skill(price_service):
    """Factory function - requires PriceService"""
    return PriceLookupSkill(price_service)