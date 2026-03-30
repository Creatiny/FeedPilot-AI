#!/usr/bin/env python3
"""Add customer to database"""
import sqlite3
import sys
import os

# P0 FIX: 移除硬编码 owner ID，改为必填参数
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'feed_sales.db')

def add_customer(owner_id: str, name: str, phone: str, animal_type: str, scale: int):
    """添加客户（owner_id 必填）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customers (owner_open_id, name, phone, animal_type, scale)
        VALUES (?, ?, ?, ?, ?)
    ''', (owner_id, name, phone, animal_type, scale))
    customer_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return customer_id

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print("Usage: python3 add_customer.py <owner_id> <name> <phone> <animal_type> <scale>")
        print("Example: python3 add_customer.py 'telegram:123456' 'John Doe' '555-1234' 'Swine' 500")
        sys.exit(1)
    
    owner_id = sys.argv[1]
    name = sys.argv[2]
    phone = sys.argv[3]
    animal_type = sys.argv[4]
    try:
        scale = int(sys.argv[5])
    except ValueError:
        print("Error: scale must be an integer")
        sys.exit(1)
    
    customer_id = add_customer(owner_id, name, phone, animal_type, scale)
    print(f"✓ Customer added: ID={customer_id} | {name} | {phone} | {animal_type} | {scale} head")