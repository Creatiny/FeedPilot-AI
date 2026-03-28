"""
FeedSales AI - Migrate JSON data to SQLite database

Migrate NRC formulas, USDA ingredients, and USD prices to SQLite
"""

import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables(conn):
    """Create database tables"""
    cursor = conn.cursor()
    
    # Formulas table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            animal_category TEXT NOT NULL,
            stage TEXT NOT NULL,
            weight_range TEXT,
            source TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Formula ingredients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formula_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            ratio REAL NOT NULL,
            FOREIGN KEY (formula_id) REFERENCES formulas(id)
        )
    ''')
    
    # Ingredients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT,
            usda_id TEXT,
            nutrition TEXT,
            unit TEXT,
            source TEXT
        )
    ''')
    
    # Prices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredient_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_name TEXT NOT NULL,
            price REAL NOT NULL,
            unit TEXT NOT NULL,
            date TEXT NOT NULL,
            market TEXT,
            trend TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    logger.info("Tables created successfully")


def migrate_formulas(conn, formulas_file: str):
    """Migrate formulas from JSON to SQLite"""
    logger.info(f"Migrating formulas from {formulas_file}...")
    
    with open(formulas_file, 'r', encoding='utf-8') as f:
        formulas = json.load(f)
    
    cursor = conn.cursor()
    
    for formula in formulas:
        # Insert formula
        cursor.execute('''
            INSERT INTO formulas (name, animal_category, stage, weight_range, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            formula['name'],
            formula['animal_type'],
            formula['stage'],
            formula.get('weight_range', ''),
            formula.get('source', '')
        ))
        
        formula_id = cursor.lastrowid
        
        # Insert ingredients
        for ingredient in formula.get('ingredients', []):
            cursor.execute('''
                INSERT INTO formula_ingredients (formula_id, ingredient_name, ratio)
                VALUES (?, ?, ?)
            ''', (formula_id, ingredient['name'], ingredient['ratio']))
    
    conn.commit()
    logger.info(f"Migrated {len(formulas)} formulas")


def migrate_ingredients(conn, ingredients_file: str):
    """Migrate ingredients from JSON to SQLite"""
    logger.info(f"Migrating ingredients from {ingredients_file}...")
    
    with open(ingredients_file, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)
    
    cursor = conn.cursor()
    
    for ingredient in ingredients:
        cursor.execute('''
            INSERT OR REPLACE INTO ingredients 
            (name, category, usda_id, nutrition, unit, source)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            ingredient['name'],
            ingredient.get('category', ''),
            ingredient.get('usda_id', ''),
            json.dumps(ingredient.get('nutrition', {})),
            ingredient.get('unit', ''),
            ingredient.get('source', '')
        ))
    
    conn.commit()
    logger.info(f"Migrated {len(ingredients)} ingredients")


def migrate_prices(conn, prices_file: str):
    """Migrate prices from JSON to SQLite"""
    logger.info(f"Migrating prices from {prices_file}...")
    
    with open(prices_file, 'r', encoding='utf-8') as f:
        prices = json.load(f)
    
    cursor = conn.cursor()
    
    for price in prices:
        cursor.execute('''
            INSERT INTO ingredient_prices 
            (ingredient_name, price, unit, date, market, trend)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            price['name'],
            price['price'],
            price['unit'],
            price['date'],
            price.get('market', ''),
            price.get('trend', '')
        ))
    
    conn.commit()
    logger.info(f"Migrated {len(prices)} prices")


def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("FeedSales AI - Database Migration")
    logger.info("=" * 60)
    
    # Database path
    db_path = Path("data/feed_sales.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Create tables
        create_tables(conn)
        
        # Migrate data
        migrate_formulas(conn, "data/nrc_formulas_full.json")
        migrate_ingredients(conn, "data/usda_ingredients.json")
        migrate_prices(conn, "data/usd_prices.json")
        
        logger.info("\n" + "=" * 60)
        logger.info("Migration completed successfully!")
        logger.info(f"Database: {db_path}")
        logger.info("=" * 60)
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
