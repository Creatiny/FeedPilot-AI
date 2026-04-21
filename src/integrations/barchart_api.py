"""
FeedSales AI - Barchart API 客户端

获取大宗农产品实时价格数据
API 文档：https://www.barchart.com/ondemand/api
"""

import os
import logging
import requests
from typing import Optional, Dict, List
from datetime import datetime, date


logger = logging.getLogger(__name__)


class BarchartAPIClient:
    """Barchart API 客户端"""
    
    BASE_URL = "https://www.barchart.com/ondemand/api/v1"
    
    # 原料代码映射（英文）
    SYMBOL_MAP = {
        "Corn": "ZC",
        "Soybean meal": "ZM",
        "Soybean oil": "ZL",
        "Wheat": "ZW",
        "Rice": "RR",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: Barchart API Key，如果为 None 则从环境变量读取
        """
        self.api_key = api_key or os.getenv("BARCHART_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json"
        })
    
    def get_commodity_price(self, symbol: str) -> Optional[Dict]:
        """
        获取商品价格
        
        Args:
            symbol: 商品代码（如 "ZC" 玉米）
            
        Returns:
            价格数据字典，失败返回 None
        """
        if not self.api_key:
            logger.warning("BARCHART_API_KEY 未配置")
            return None
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/market/v2/futures/prices",
                params={
                    "symbols": symbol,
                    "fields": "last,change,changePercent,high,low,volume,tradeTime"
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("status", {}).get("code") == 200:
                result = data["result"][0]
                return {
                    "symbol": result["symbol"],
                    "name": result["description"],
                    "price": float(result["last"]),
                    "change": float(result["change"]),
                    "change_percent": float(result["changePercent"]),
                    "high": float(result["high"]),
                    "low": float(result["low"]),
                    "volume": int(result["volume"]),
                    "trade_time": result["tradeTime"],
                    "currency": "USD",
                    "unit": "bushel"
                }
            else:
                logger.error(f"API 错误：{data.get('status', {}).get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败：{e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"数据解析失败：{e}")
            return None
    
    def get_grain_prices(self) -> List[Dict]:
        """
        获取谷物价格列表
        
        Returns:
            价格数据列表
        """
        symbols = ["ZC", "ZM", "ZW"]  # 玉米、豆粕、小麦
        prices = []
        
        for symbol in symbols:
            price_data = self.get_commodity_price(symbol)
            if price_data:
                prices.append(price_data)
        
        return prices
    
    def convert_to_usd_ton(self, price_usd_bushel: float, commodity: str) -> float:
        """
        将 USD/蒲式耳 转换为 USD/吨
        
        Args:
            price_usd_bushel: 美元/蒲式耳价格
            commodity: 商品名称
            
        Returns:
            USD/吨价格
        """
        # kg per bushel (不同商品不同)
        kg_per_bushel = {
            "Corn": 25.4,  # 1 蒲式耳 = 25.4 kg
            "Soybean meal": 27.2,
            "Wheat": 27.2,
        }

        factor = kg_per_bushel.get(commodity, 25.4)
        # USD/bushel -> USD/kg -> USD/ton
        price_usd_ton = price_usd_bushel / factor * 1000
        
        return round(price_usd_ton, 2)
    
    def test_connection(self) -> bool:
        """测试 API 连接"""
        price_data = self.get_commodity_price("ZC")
        return price_data is not None


# 使用示例
if __name__ == "__main__":
    client = BarchartAPIClient()
    
    # 测试连接
    if client.test_connection():
        logger.info(" Barchart API 连接成功")
    else:
        logger.error(" Barchart API 连接失败")
    
    # 获取玉米价格
    corn_price = client.get_commodity_price("ZC")
    if corn_price:
        print(f"\n📊 Corn price")
        print(f"  Price: ${corn_price['price']} / bushel")
        print(f"  Change: {corn_price['change_percent']}%")
        print(f"  Volume: {corn_price['volume']}")
        
        # 转换为 USD/ton
        price_usd = client.convert_to_usd_ton(corn_price['price'], "Corn")
        print(f"  Converted: ${price_usd} / ton")
