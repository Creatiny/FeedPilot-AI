#!/usr/bin/env python3
"""Quick price check script for cron jobs"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "feed_sales.db"

def check_price(ingredient_pattern, code_pattern=None):
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    if code_pattern:
        row = conn.execute(
            "SELECT ingredient_name, price, price_date, source FROM ingredient_prices WHERE ingredient_code LIKE ? OR ingredient_name LIKE ? ORDER BY price_date DESC LIMIT 1",
            (code_pattern, f'%{ingredient_pattern}%')
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT ingredient_name, price, price_date, source FROM ingredient_prices WHERE ingredient_name LIKE ? ORDER BY price_date DESC LIMIT 1",
            (f'%{ingredient_pattern}%',)
        ).fetchone()
    
    conn.close()
    return dict(row) if row else None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: quick_price_check.py <ingredient_name> <code_pattern>")
        sys.exit(1)
    
    ingredient = sys.argv[1]
    code = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = check_price(ingredient, code)
    if result:
        print(f"{result['ingredient_name']}|{result['price']}|{result['price_date']}|{result['source']}")
    else:
        print("NOT_FOUND")
