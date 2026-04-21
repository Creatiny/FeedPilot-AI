"""
FeedSales AI - Pytest Configuration

Shared fixtures and configuration for all tests (v1.7)
"""

import pytest
import sys
import tempfile
import os
import threading
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool


@pytest.fixture(autouse=True)
def reset_database_pool():
    """每个测试前重置 DatabasePool 单例"""
    DatabasePool._instance = None
    DatabasePool._lock = threading.Lock()
    yield
    DatabasePool._instance = None


@pytest.fixture
def pool():
    """Database pool fixture using actual database"""
    db_pool = DatabasePool('data/feed_sales.db')
    yield db_pool


@pytest.fixture
def test_db():
    """Create temporary test database with full schema (v1.7)"""
    # Reset DatabasePool singleton
    DatabasePool._instance = None
    DatabasePool._lock = threading.Lock()
    
    # Create temp file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Initialize full schema (matching schema.sql)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Enable WAL mode
    cursor.execute("PRAGMA journal_mode = WAL")
    
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
    
    # Ingredient prices table
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
            UNIQUE(ingredient_code, price_date, owner_open_id)
        )
    ''')
    
    # Formulas table
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
            UNIQUE(owner_open_id, name)
        )
    ''')
    
    # Formula ingredients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formula_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            ingredient_code TEXT NOT NULL,
            ratio_percent REAL NOT NULL CHECK(ratio_percent >= 0 AND ratio_percent <= 100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
        )
    ''')
    
    # Customers table (v1.7 schema)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_open_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            animal_type TEXT,
            scale INTEGER,
            notes TEXT,
            version INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_open_id) REFERENCES users(open_id)
        )
    ''')
    
    # Calculation history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calculation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_open_id TEXT NOT NULL,
            formula_name TEXT NOT NULL,
            total_cost REAL NOT NULL,
            cost_per_ton REAL NOT NULL,
            ingredients_json TEXT NOT NULL,
            data_source TEXT DEFAULT 'barchart',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert test users
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('user_a',))
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('user_b',))
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('test_user_pytest',))
    
    # Insert public formulas (matching actual data)
    cursor.execute('''
        INSERT INTO formulas (owner_open_id, name, animal_type, stage_type)
        VALUES ('system_public', 'Nursery Diet 1', 'Swine', 'Nursery')
    ''')
    formula_id = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO formula_ingredients (formula_id, ingredient_name, ingredient_code, ratio_percent)
        VALUES (?, 'Corn', 'ING_CORN', 60.0)
    ''', (formula_id,))
    cursor.execute('''
        INSERT INTO formula_ingredients (formula_id, ingredient_name, ingredient_code, ratio_percent)
        VALUES (?, 'Soybean meal', 'ING_SBM', 25.0)
    ''', (formula_id,))
    
    # Insert public prices
    cursor.execute('''
        INSERT INTO ingredient_prices (owner_open_id, ingredient_code, ingredient_name, price, price_date, source)
        VALUES ('system_public', 'ING_CORN', 'Corn', 180.0, '2026-03-30', 'test')
    ''')
    cursor.execute('''
        INSERT INTO ingredient_prices (owner_open_id, ingredient_code, ingredient_name, price, price_date, source)
        VALUES ('system_public', 'ING_SBM', 'Soybean meal', 350.0, '2026-03-30', 'test')
    ''')
    
    conn.commit()
    conn.close()
    
    pool = DatabasePool(db_path)
    yield pool
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def test_user_id():
    """Test user ID fixture"""
    return "test_user_pytest"


@pytest.fixture
def sample_formula_data():
    """Sample formula data for tests"""
    return {
        'name': 'Test Formula',
        'stage_type': 'Nursery',
        'animal_type': 'Swine',
        'notes': 'Test formula for unit tests',
        'ingredients': [
            {'name': 'Corn', 'ratio': 60.0},
            {'name': 'Soybean meal', 'ratio': 25.0},
            {'name': 'Premix', 'ratio': 5.0},
        ]
    }


@pytest.fixture
def sample_customer_data():
    """Sample customer data for tests (v1.7 schema)"""
    return {
        'name': 'Test Customer',
        'phone': '555-1234',
        'address': 'Test Farm Road',
        'animal_type': 'swine',
        'scale': 100,
        'notes': 'Test customer for unit tests'
    }