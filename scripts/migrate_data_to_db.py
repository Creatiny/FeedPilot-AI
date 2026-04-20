"""
FeedSales AI - Migrate JSON data to SQLite database (v1.7)

Migrate NRC formulas, USDA ingredients, and USD prices to SQLite
Schema aligned with src/database/schema.sql
"""

import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables(conn):
    """Create database tables (aligned with schema.sql)"""
    cursor = conn.cursor()
    
    # Enable WAL mode
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            open_id TEXT PRIMARY KEY,
            telegram_user_id TEXT UNIQUE,
            feishu_user_id TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Formulas table (v1.7 schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_open_id TEXT NOT NULL,
            name TEXT NOT NULL,
            animal_type TEXT,
            stage_type TEXT NOT NULL,
            weight_range TEXT,
            notes TEXT,
            version INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_open_id) REFERENCES users(open_id),
            UNIQUE(owner_open_id, name)
        )
    ''')
    
    # Formula ingredients table (v1.7 schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formula_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            ratio_percent REAL NOT NULL CHECK(ratio_percent >= 0 AND ratio_percent <= 100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
        )
    ''')
    
    # Ingredient prices table (v1.7 schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredient_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_open_id TEXT NOT NULL,
            ingredient_code TEXT NOT NULL,
            ingredient_name TEXT NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            unit TEXT DEFAULT 'ton',
            source TEXT DEFAULT 'barchart',
            price_date DATE NOT NULL,
            version INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_open_id) REFERENCES users(open_id),
            UNIQUE(ingredient_code, price_date, owner_open_id)
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prices_owner_date ON ingredient_prices(owner_open_id, price_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_formulas_owner ON formulas(owner_open_id)')
    
    conn.commit()
    logger.info("Tables created successfully (v1.7 schema)")


def migrate_formulas(conn, formulas_file: str):
    """Migrate formulas from JSON to SQLite (v1.7 schema)"""
    logger.info(f"Migrating formulas from {formulas_file}...")
    
    with open(formulas_file, 'r', encoding='utf-8') as f:
        formulas = json.load(f)
    
    cursor = conn.cursor()
    
    # Ensure public user exists
    cursor.execute("INSERT OR IGNORE INTO users (open_id) VALUES ('system_public')")
    
    for formula in formulas:
        # Insert formula (v1.7 schema)
        cursor.execute('''
            INSERT INTO formulas (owner_open_id, name, animal_type, stage_type, weight_range, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'system_public',  # Public data
            formula['name'],
            formula.get('animal_type', formula.get('animal_category', '')),  # Support both field names
            formula.get('stage_type', formula.get('stage', '')),  # Support both field names
            formula.get('weight_range', ''),
            formula.get('source', '')
        ))
        
        formula_id = cursor.lastrowid
        
        # Insert ingredients (v1.7 schema: ratio_percent)
        for ingredient in formula.get('ingredients', []):
            cursor.execute('''
                INSERT INTO formula_ingredients (formula_id, ingredient_name, ratio_percent)
                VALUES (?, ?, ?)
            ''', (formula_id, ingredient['name'], ingredient['ratio']))
    
    conn.commit()
    logger.info(f"Migrated {len(formulas)} formulas")


def migrate_prices(conn, prices_file: str):
    """Migrate prices from JSON to SQLite (v1.7 schema)"""
    logger.info(f"Migrating prices from {prices_file}...")
    
    with open(prices_file, 'r', encoding='utf-8') as f:
        prices = json.load(f)
    
    cursor = conn.cursor()
    
    # Ensure public user exists
    cursor.execute("INSERT OR IGNORE INTO users (open_id) VALUES ('system_public')")
    
    for price in prices:
        # Generate ingredient code if not present
        ingredient_code = price.get('code', f"ING_{price['name'].upper()[:10]}")
        
        # Insert price (v1.7 schema)
        cursor.execute('''
            INSERT OR REPLACE INTO ingredient_prices 
            (owner_open_id, ingredient_code, ingredient_name, price, unit, source, price_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'system_public',  # Public data
            ingredient_code,
            price['name'],
            price['price'],
            price.get('unit', 'ton'),
            price.get('source', 'usda'),
            price.get('date', price.get('price_date', datetime.now().strftime('%Y-%m-%d')))  # Support both field names
        ))
    
    conn.commit()
    logger.info(f"Migrated {len(prices)} prices")


def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("FeedSales AI - Database Migration (v1.7)")
    logger.info("=" * 60)
    
    # Database path
    db_path = Path("data/feed_sales.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Create tables (v1.7 schema)
        create_tables(conn)
        
        # Migrate data
        migrate_formulas(conn, "data/nrc_formulas_full.json")
        migrate_prices(conn, "data/usd_prices.json")
        
        logger.info("\n" + "=" * 60)
        logger.info("Migration completed successfully!")
        logger.info(f"Database: {db_path}")
        logger.info("=" * 60)
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()