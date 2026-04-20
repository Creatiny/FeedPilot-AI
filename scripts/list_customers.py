#!/usr/bin/env python3
"""List customers from database"""
import sqlite3
import sys
import os

# P0 FIX: 添加 owner 过滤，防止跨租户数据泄露
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'feed_sales.db')

def list_customers(owner_id: str):
    """列出客户（按 owner 过滤）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # P0 FIX: 必须按 owner_id 过滤
    cursor.execute('''
        SELECT id, name, phone, animal_type, scale, notes 
        FROM customers 
        WHERE owner_open_id = ? 
        ORDER BY name
    ''', (owner_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 list_customers.py <owner_id>")
        print("Example: python3 list_customers.py 'telegram:123456'")
        sys.exit(1)
    
    owner_id = sys.argv[1]
    customers = list_customers(owner_id)
    
    if customers:
        print(f"Total customers: {len(customers)}")
        print("-" * 60)
        for c in customers:
            print(f"ID: {c['id']} | {c['name']} | {c['phone']} | {c['animal_type']} | {c['scale']} head")
    else:
        print(f"No customers found for owner: {owner_id}")