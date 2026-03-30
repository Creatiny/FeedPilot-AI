#!/usr/bin/env python3
"""Delete customer from database"""
import sqlite3
import sys
import os

# P0 FIX: 添加 owner 验证，防止跨租户删除
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'feed_sales.db')

def delete_customer(owner_id: str, customer_id: int):
    """删除客户（带 owner 验证）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # P0 FIX: 必须验证 owner_id
    cursor.execute('DELETE FROM customers WHERE id = ? AND owner_open_id = ?', (customer_id, owner_id))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 delete_customer.py <owner_id> <customer_id>")
        print("Example: python3 delete_customer.py 'telegram:123456' 1")
        sys.exit(1)
    
    owner_id = sys.argv[1]
    try:
        customer_id = int(sys.argv[2])
    except ValueError:
        print("Error: customer_id must be an integer")
        sys.exit(1)
    
    deleted = delete_customer(owner_id, customer_id)
    if deleted > 0:
        print(f"✓ Deleted customer {customer_id}")
    else:
        print(f"✗ Customer not found or not authorized")