"""
FeedSales AI - Auto Add Ingredient

自动检测并添加新原料到数据库
从 Barchart CBOT 和 USDA 数据源获取价格
"""

import sqlite3
import logging
import requests
from datetime import datetime
from typing import Dict, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "data/feed_sales.db"

# 数据源配置
BARCHART_CBOT_URL = "https://www.cmegroup.com/CmeWS/mvc/Quotes/Futures/G/{product}/G"
USDA_API_URL = "https://api.ams.usda.gov/mandated_reports/v1/data"

# 支持的原料映射（英文名 -> 数据源查询代码）
SUPPORTED_INGREDIENTS = {
    # Grains (CBOT/CME)
    "Corn": {"source": "cme", "code": "ZC", "unit": "bushel"},
    "Wheat": {"source": "cme", "code": "ZW", "unit": "bushel"},
    "Soybeans": {"source": "cme", "code": "ZS", "unit": "bushel"},
    "Soybean Meal": {"source": "cme", "code": "ZM", "unit": "ton"},
    "Soybean Oil": {"source": "cme", "code": "ZL", "unit": "lb"},
    "Oats": {"source": "cme", "code": "ZO", "unit": "bushel"},
    "Rough Rice": {"source": "cme", "code": "ZR", "unit": "cwt"},
    
    # USDA 报告原料
    "Alfalfa Hay": {"source": "usda", "code": "HAY_ALFALFA", "unit": "ton"},
    "Barley": {"source": "usda", "code": "BARLEY", "unit": "bushel"},
    "Sorghum": {"source": "usda", "code": "SORGHUM", "unit": "cwt"},
    "Cottonseed Meal": {"source": "usda", "code": "COTTONSEED_MEAL", "unit": "ton"},
    "Canola Meal": {"source": "usda", "code": "CANOLA_MEAL", "unit": "ton"},
    "Fish Meal": {"source": "usda", "code": "FISH_MEAL", "unit": "ton"},
    "Meat Bone Meal": {"source": "usda", "code": "MBM", "unit": "ton"},
    "Blood Meal": {"source": "usda", "code": "BLOOD_MEAL", "unit": "ton"},
    "Feather Meal": {"source": "usda", "code": "FEATHER_MEAL", "unit": "ton"},
    "Poultry Meal": {"source": "usda", "code": "POULTRY_MEAL", "unit": "ton"},
    "DDGS": {"source": "usda", "code": "DDGS", "unit": "ton"},
    "Hominy Feed": {"source": "usda", "code": "HOMINY", "unit": "ton"},
    "Wheat Midds": {"source": "usda", "code": "WHEAT_MIDDS", "unit": "ton"},
    "Corn Gluten Feed": {"source": "usda", "code": "CGF", "unit": "ton"},
    "Corn Gluten Meal": {"source": "usda", "code": "CGM", "unit": "ton"},
    
    # Minerals & Additives (固定价格参考)
    "Limestone": {"source": "fixed", "price": 120, "unit": "ton"},
    "Dicalcium Phosphate": {"source": "fixed", "price": 650, "unit": "ton"},
    "Salt": {"source": "fixed", "price": 150, "unit": "ton"},
    "L-Lysine HCl": {"source": "fixed", "price": 1200, "unit": "ton"},
    "DL-Methionine": {"source": "fixed", "price": 2500, "unit": "ton"},
    "Threonine": {"source": "fixed", "price": 1500, "unit": "ton"},
    "Tryptophan": {"source": "fixed", "price": 5000, "unit": "ton"},
    "Choline Chloride": {"source": "fixed", "price": 800, "unit": "ton"},
    "Vitamin Premix": {"source": "fixed", "price": 3500, "unit": "ton"},
    "Premix Swine": {"source": "fixed", "price": 400, "unit": "ton"},
    "Premix Poultry": {"source": "fixed", "price": 420, "unit": "ton"},
    "Premix Ruminant": {"source": "fixed", "price": 380, "unit": "ton"},
    
    # Forage
    "Corn Silage": {"source": "usda", "code": "CORN_SILAGE", "unit": "ton"},
    "Grass Hay": {"source": "usda", "code": "HAY_GRASS", "unit": "ton"},
    "Straw": {"source": "usda", "code": "STRAW", "unit": "ton"},
    
    # Specialty
    "Molasses": {"source": "usda", "code": "MOLASSES", "unit": "ton"},
    "Fat Animal": {"source": "usda", "code": "ANIMAL_FAT", "unit": "ton"},
    "Vegetable Oil": {"source": "usda", "code": "VEG_OIL", "unit": "ton"},
}


class AutoIngredientManager:
    """自动原料管理器"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def ingredient_exists(self, ingredient_name: str) -> bool:
        """检查原料是否存在于数据库"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM ingredient_prices WHERE ingredient_name LIKE ?",
            (f'%{ingredient_name}%',)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def find_supported_ingredient(self, query: str) -> Optional[Dict]:
        """查找支持的原料"""
        query_lower = query.lower()
        
        for name, config in SUPPORTED_INGREDIENTS.items():
            if name.lower() in query_lower or query_lower in name.lower():
                return {"name": name, **config}
        
        # 模糊匹配
        for name, config in SUPPORTED_INGREDIENTS.items():
            words = name.lower().split()
            if any(w in query_lower for w in words):
                return {"name": name, **config}
        
        return None
    
    def fetch_price_from_cme(self, code: str) -> Optional[float]:
        """从 CME/CBOT 获取价格"""
        try:
            # CME Group Quotes API
            url = f"https://www.cmegroup.com/CmeWS/mvc/Quotes/Futures/G/{code}/G"
            headers = {"User-Agent": "Mozilla/5.0 FeedSales AI"}
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    last_price = data[0].get('last', 0)
                    return float(last_price)
        except Exception as e:
            logger.warning(f"CME fetch failed for {code}: {e}")
        
        return None
    
    def fetch_price_from_usda(self, code: str) -> Optional[float]:
        """从 USDA 获取价格"""
        try:
            # USDA AMS API (模拟)
            url = f"https://www.ams.usda.gov/mnreports/lswgrain.txt"
            headers = {"User-Agent": "FeedSales AI"}
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 200:
                # 简化：返回估算价格
                # 实际应该解析 USDA 报告
                return None
        except Exception as e:
            logger.warning(f"USDA fetch failed for {code}: {e}")
        
        return None
    
    def add_ingredient(self, ingredient_name: str, price: float, source: str = "auto") -> bool:
        """添加新原料到数据库"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            code = ingredient_name.upper().replace(' ', '_')[:20]
            
            cursor.execute('''
                INSERT OR REPLACE INTO ingredient_prices 
                (owner_open_id, ingredient_code, ingredient_name, price, unit, source, price_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('system_public', code, ingredient_name, price, 'ton', source, today))
            
            conn.commit()
            logger.info(f"Added ingredient: {ingredient_name} at ${price}/ton")
            return True
        except Exception as e:
            logger.error(f"Failed to add ingredient {ingredient_name}: {e}")
            return False
        finally:
            conn.close()
    
    def auto_add_ingredient(self, query: str) -> Dict:
        """
        自动检测并添加原料
        
        Args:
            query: 用户查询的原料名称
            
        Returns:
            Dict with success status and message
        """
        # 检查是否已存在
        if self.ingredient_exists(query):
            return {"success": True, "message": f"Ingredient '{query}' already exists"}
        
        # 查找支持的原料
        supported = self.find_supported_ingredient(query)
        if not supported:
            return {
                "success": False,
                "message": f"Ingredient '{query}' not found in supported list. Supported ingredients: {list(SUPPORTED_INGREDIENTS.keys())[:10]}..."
            }
        
        ingredient_name = supported["name"]
        source = supported.get("source", "unknown")
        
        # 获取价格
        price = None
        
        if source == "cme":
            code = supported.get("code")
            price = self.fetch_price_from_cme(code)
            source_name = "CBOT/CME"
        elif source == "usda":
            code = supported.get("code")
            price = self.fetch_price_from_usda(code)
            source_name = "USDA"
        elif source == "fixed":
            price = supported.get("price")
            source_name = "Reference"
        else:
            price = None
        
        if price is None:
            return {
                "success": False,
                "message": f"Could not fetch price for '{ingredient_name}' from {source}"
            }
        
        # 添加到数据库
        if self.add_ingredient(ingredient_name, price, source_name):
            return {
                "success": True,
                "message": f"Added '{ingredient_name}' at ${price}/ton from {source_name}",
                "data": {
                    "name": ingredient_name,
                    "price": price,
                    "source": source_name
                }
            }
        else:
            return {"success": False, "message": f"Failed to add '{ingredient_name}' to database"}


def auto_add_ingredient(query: str) -> Dict:
    """便捷函数"""
    manager = AutoIngredientManager()
    return manager.auto_add_ingredient(query)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        result = auto_add_ingredient(query)
        print(json.dumps(result, indent=2))
    else:
        # 交互模式
        print("=== Auto Ingredient Manager ===")
        print("Enter ingredient name (or 'quit' to exit):")
        
        manager = AutoIngredientManager()
        
        while True:
            try:
                query = input("> ").strip()
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                result = manager.auto_add_ingredient(query)
                if result['success']:
                    print(f"✅ {result['message']}")
                else:
                    print(f"❌ {result['message']}")
            except EOFError:
                break