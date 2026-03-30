#!/usr/bin/env python3
"""List all customers from database"""
import sqlite3

def list_customers():
    conn = sqlite3.connect('data/feed_sales.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, phone, animal_type, scale FROM customers ORDER BY name')
    rows = cursor.fetchall()
    if rows:
        print(f"Total customers: {len(rows)}")
        print("-" * 50)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} head")
    else:
        print("No customers found")
    conn.close()

if __name__ == '__main__':
    list_customers()