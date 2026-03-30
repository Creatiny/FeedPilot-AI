"""
FeedSales AI - Pytest Configuration

Shared fixtures and configuration for all tests
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool


@pytest.fixture
def pool():
    """Database pool fixture for tests"""
    db_pool = DatabasePool('data/feed_sales.db')
    yield db_pool
    # Cleanup not needed for SQLite


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
        'notes': 'Test formula for unit tests',
        'ingredients': [
            {'name': 'Corn', 'ratio': 60.0},
            {'name': 'Soybean meal', 'ratio': 25.0},
            {'name': 'Premix', 'ratio': 5.0},
        ]
    }


@pytest.fixture
def sample_customer_data():
    """Sample customer data for tests"""
    return {
        'name': 'Test Customer',
        'phone': '555-1234',
        'address': 'Test Farm',
        'animal_type': 'swine',
        'scale': 100,
        'notes': 'Test customer for unit tests'
    }


# Async test support
@pytest.fixture
def event_loop_policy():
    """Event loop policy for async tests"""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()