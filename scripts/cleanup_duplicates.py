#!/usr/bin/env python3
"""
FeedSales AI - Cleanup Duplicate Price Records

Removes duplicate ingredient_price records, keeping only the latest entry
per ingredient per day.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'feed_sales.db')

def cleanup_duplicates():
    """Remove duplicate price records, keeping the latest by id."""
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Find duplicates: ingredients with multiple records on the same date
    cur.execute("""
        SELECT ingredient_name, price_date, COUNT(*) as cnt, MAX(id) as max_id
        FROM ingredient_prices
        GROUP BY ingredient_name, price_date
        HAVING cnt > 1
    """)
    
    duplicates = cur.fetchall()
    
    if not duplicates:
        print("✅ No duplicates found.")
        return 0
    
    print(f"Found {len(duplicates)} ingredient(s) with duplicates:")
    
    total_removed = 0
    
    for ingredient_name, price_date, count, max_id in duplicates:
        # Delete all except the one with max id (latest)
        cur.execute("""
            DELETE FROM ingredient_prices
            WHERE ingredient_name = ? AND price_date = ? AND id != ?
        """, (ingredient_name, price_date, max_id))
        
        removed = count - 1
        total_removed += removed
        print(f"  - {ingredient_name} ({price_date}): removed {removed} duplicate(s)")
    
    conn.commit()
    
    # Verify results
    cur.execute("""
        SELECT price_date, COUNT(*) FROM ingredient_prices
        GROUP BY price_date ORDER BY price_date DESC LIMIT 5
    """)
    
    print("\n✅ Cleanup complete. Current record counts:")
    for price_date, count in cur.fetchall():
        print(f"  {price_date}: {count} records")
    
    conn.close()
    
    return total_removed

if __name__ == "__main__":
    removed = cleanup_duplicates()
    print(f"\nTotal records removed: {removed}")
