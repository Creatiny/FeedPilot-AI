"""
FeedSales AI - Price Scraper

Scrape feed ingredient prices from USDA/CBOT sources
Auto-update prices in database
"""

import requests
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceScraper:
    """Price scraper for US feed ingredients"""
    
    def __init__(self, db_path: str = "data/feed_sales.db"):
        """
        Initialize scraper
        
        Args:
            db_path: SQLite database path
        """
        self.db_path = Path(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def scrape_cbot_prices(self) -> List[Dict]:
        """
        Scrape CBOT futures prices
        
        Note: This is a demo implementation.
        For production, use official CBOT API or web scraping with proper authorization.
        """
        logger.info("Scraping CBOT futures prices...")
        
        # Demo prices (in real implementation, scrape from CBOT website)
        # CBOT quotes: https://www.cmegroup.com/markets/agriculture.html
        prices = [
            {
                'name': 'Corn, No.2 Yellow',
                'price': 450.00,  # cents/bushel
                'unit': 'cents/bu',
                'market': 'CBOT',
                'change': '+2.5',
                'trend': 'up'
            },
            {
                'name': 'Soybean meal, 48%',
                'price': 350.00,  # $/short ton
                'unit': 'USD/ton',
                'market': 'CBOT',
                'change': '-1.2',
                'trend': 'down'
            },
            {
                'name': 'Soybeans, No.1 Yellow',
                'price': 1200.00,  # cents/bushel
                'unit': 'cents/bu',
                'market': 'CBOT',
                'change': '+5.0',
                'trend': 'up'
            },
            {
                'name': 'Wheat, No.2 Soft Red',
                'price': 550.00,  # cents/bushel
                'unit': 'cents/bu',
                'market': 'CBOT',
                'change': '-3.5',
                'trend': 'down'
            },
        ]
        
        logger.info(f"Scraped {len(prices)} CBOT prices")
        return prices
    
    def scrape_usda_prices(self) -> List[Dict]:
        """
        Scrape USDA national average prices
        
        Note: This is a demo implementation.
        For production, use USDA AMS API: https://www.ams.usda.gov/mnreports
        """
        logger.info("Scraping USDA national prices...")
        
        # Demo prices from USDA reports
        prices = [
            {
                'name': 'Fish meal, 65%',
                'price': 1800.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '0.0',
                'trend': 'stable'
            },
            {
                'name': 'Premix, swine',
                'price': 450.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.5',
                'trend': 'up'
            },
            {
                'name': 'Dicalcium phosphate',
                'price': 650.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '-0.3',
                'trend': 'down'
            },
            {
                'name': 'Limestone, ag',
                'price': 120.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '0.0',
                'trend': 'stable'
            },
            {
                'name': 'Salt, white',
                'price': 150.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '0.0',
                'trend': 'stable'
            },
            {
                'name': 'L-Lysine HCl',
                'price': 1200.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+1.0',
                'trend': 'up'
            },
            {
                'name': 'DL-Methionine',
                'price': 2500.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.5',
                'trend': 'up'
            },
            {
                'name': 'Alfalfa hay, early bloom',
                'price': 220.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '-0.2',
                'trend': 'down'
            },
            {
                'name': 'Corn silage',
                'price': 80.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '0.0',
                'trend': 'stable'
            },
            {
                'name': 'Wheat middlings',
                'price': 190.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.3',
                'trend': 'up'
            },
            {
                'name': 'Milk replacer, calf',
                'price': 2800.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.8',
                'trend': 'up'
            },
            {
                'name': 'Premix, beef',
                'price': 400.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '0.0',
                'trend': 'stable'
            },
            {
                'name': 'Premix, dairy',
                'price': 480.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.2',
                'trend': 'up'
            },
            {
                'name': 'Premix, broiler',
                'price': 520.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.3',
                'trend': 'up'
            },
            {
                'name': 'Premix, layer',
                'price': 550.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.4',
                'trend': 'up'
            },
            {
                'name': 'Premix, sow',
                'price': 460.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.2',
                'trend': 'up'
            },
            {
                'name': 'Premix, calf',
                'price': 500.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.3',
                'trend': 'up'
            },
            {
                'name': 'Premix, heifer',
                'price': 420.00,
                'unit': 'USD/ton',
                'market': 'US',
                'change': '+0.1',
                'trend': 'up'
            },
        ]
        
        logger.info(f"Scraped {len(prices)} USDA prices")
        return prices
    
    def convert_cbot_units(self, price: float, ingredient: str) -> float:
        """
        Convert CBOT units to USD/ton
        
        Args:
            price: Price in CBOT units (cents/bu)
            ingredient: Ingredient name
            
        Returns:
            Price in USD/ton
        """
        # Conversion factors (approximate)
        conversion_factors = {
            'Corn': 39.37,  # bushels per metric ton
            'Soybeans': 36.74,
            'Wheat': 37.04,
        }
        
        for ingredient_key, factor in conversion_factors.items():
            if ingredient_key in ingredient:
                # Convert cents/bu to USD/ton
                return (price / 100.0) * factor
        
        return price
    
    def _get_ingredient_code(self, ingredient_name: str) -> str:
        """
        Generate ingredient code from name
        
        Args:
            ingredient_name: Ingredient name
            
        Returns:
            Ingredient code (e.g., 'ING_CORN')
        """
        # Map common names to codes
        code_map = {
            'Corn': 'ING_CORN',
            'Soybean meal': 'ING_SBM',
            'Soybeans': 'ING_SBEAN',
            'Wheat': 'ING_WHEAT',
            'Fish meal': 'ING_FISHM',
            'Premix': 'ING_PREMIX',
            'Dicalcium phosphate': 'ING_DCP',
            'Limestone': 'ING_LIME',
            'Salt': 'ING_SALT',
            'L-Lysine': 'ING_LYS',
            'DL-Methionine': 'ING_MET',
            'Alfalfa': 'ING_ALFALFA',
            'Corn silage': 'ING_CSILAGE',
            'Wheat middlings': 'ING_WHEATMID',
            'Milk replacer': 'ING_MILKREP',
        }
        
        for key, code in code_map.items():
            if key in ingredient_name:
                return code
        
        # Default: generate from first word
        return 'ING_' + ingredient_name.split(',')[0].upper().replace(' ', '_')[:15]
    
    def update_database(self, prices: List[Dict]) -> int:
        """
        Update prices in database (UPSERT - updates existing, inserts new)
        
        Args:
            prices: List of price data
            
        Returns:
            Number of records updated
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        updated = 0
        
        for price_data in prices:
            # Convert CBOT units if needed
            if price_data.get('unit') == 'cents/bu':
                price_usd_ton = self.convert_cbot_units(
                    price_data['price'],
                    price_data['name']
                )
            else:
                price_usd_ton = price_data['price']
            
            # UPSERT: Update if exists, insert if new
            cursor.execute('''
                INSERT INTO ingredient_prices 
                (owner_open_id, ingredient_name, ingredient_code, price, currency, unit, price_date, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ingredient_code, price_date, owner_open_id) DO UPDATE SET
                    price = excluded.price,
                    source = excluded.source
            ''', (
                'system_public',
                price_data['name'],
                self._get_ingredient_code(price_data['name']),
                round(price_usd_ton, 2),
                'USD',
                'ton',
                today,
                price_data.get('market', 'US')
            ))
            
            updated += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated {updated} price records")
        return updated
    
    def run_full_update(self):
        """Run full price update"""
        logger.info("=" * 60)
        logger.info("FeedSales AI - Price Update")
        logger.info("=" * 60)
        
        # Scrape CBOT prices
        cbot_prices = self.scrape_cbot_prices()
        
        # Scrape USDA prices
        usda_prices = self.scrape_usda_prices()
        
        # Combine prices
        all_prices = cbot_prices + usda_prices
        
        # Update database
        updated = self.update_database(all_prices)
        
        logger.info("=" * 60)
        logger.info(f"Price update completed: {updated} records")
        logger.info("=" * 60)
        
        return updated


def main():
    """Main function"""
    scraper = PriceScraper()
    scraper.run_full_update()


if __name__ == "__main__":
    main()
