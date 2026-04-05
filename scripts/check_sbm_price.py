#!/usr/bin/env python3
"""
Soybean Meal Price Alert Script
Notifies when SBM price exceeds $400/ton
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "feed_sales.db"
THRESHOLD = 400

def check_sbm_price():
    """Check current SBM price and alert if above threshold"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get latest SBM price
    cursor.execute("""
        SELECT ingredient_name, price, price_date 
        FROM ingredient_prices 
        WHERE ingredient_name LIKE '%Soybean meal, 48%'
        ORDER BY price_date DESC 
        LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print("No SBM price data found")
        return
    
    name, price, date = result
    
    if price > THRESHOLD:
        print(f"⚠️ PRICE ALERT: Soybean meal is ${price}/ton - ABOVE ${THRESHOLD} threshold!")
        print(f"Date: {date}")
        return True
    else:
        print(f"Soybean meal: ${price}/ton (below ${THRESHOLD} threshold)")
        return False

if __name__ == "__main__":
    exceeded = check_sbm_price()
    sys.exit(0 if not exceeded else 1)