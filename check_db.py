import sqlite3
import os

db_path = os.path.expanduser("~/.openclaw/workspace/feed-sales-ai-mvp/data/feed_sales.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

# Check for customer-related tables
for table in tables:
    if 'customer' in table[0].lower() or 'client' in table[0].lower():
        print(f"\n{table[0]}:")
        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
        print(cursor.fetchall())

conn.close()