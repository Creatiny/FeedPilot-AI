#!/usr/bin/env python3
"""Add customer to database"""
import sqlite3
import sys

def add_customer(name, phone, animal_type, scale):
    conn = sqlite3.connect('data/feed_sales.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customers (owner_open_id, name, phone, animal_type, scale)
        VALUES (?, ?, ?, ?, ?)
    ''', ('telegram:7972653610', name, phone, animal_type, scale))
    conn.commit()
    print(f"Customer added: {name} | {phone} | {animal_type} | {scale} head")
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python3 add_customer.py <name> <phone> <animal_type> <scale>")
        sys.exit(1)
    add_customer(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]))