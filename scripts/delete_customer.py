#!/usr/bin/env python3
"""Delete customer from database"""
import sqlite3
import sys

def delete_customer(name):
    conn = sqlite3.connect('data/feed_sales.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM customers WHERE name = ?', (name,))
    deleted = cursor.rowcount
    conn.commit()
    print(f"Deleted {deleted} customer(s) named '{name}'")
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 delete_customer.py <name>")
        sys.exit(1)
    delete_customer(sys.argv[1])