"""
FeedSales AI - Query Limit Middleware Tests
TDD: RED phase - write failing tests first
"""

import pytest
import tempfile
import os
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.services.subscription_service import SubscriptionService
from src.middleware.query_limit_middleware import QueryLimitMiddleware


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    os.unlink(db_path)


@pytest.fixture
def db_pool(temp_db):
    """Create database pool with schema"""
    pool = DatabasePool(temp_db)
    yield pool


@pytest.fixture
def sub_service(db_pool):
    """Create subscription service"""
    return SubscriptionService(db_pool)


@pytest.fixture
def middleware(sub_service):
    """Create query limit middleware"""
    return QueryLimitMiddleware(sub_service)


class TestQueryLimitMiddleware:
    """Test query limit middleware functionality"""
    
    def test_free_user_with_queries_remaining_allowed(self, middleware, sub_service):
        """Free user with queries remaining should be allowed"""
        user_id = 'free_user_1'
        
        # New free user has 3 queries/day
        result = middleware.check_and_record(user_id, 'price-lookup')
        
        assert result['allowed'] == True
        assert 'remaining' in result
        assert result['remaining'] == 2  # 3 - 1 after recording
    
    def test_free_user_exceeded_limit_blocked(self, middleware, sub_service):
        """Free user exceeded limit should be blocked with upgrade message"""
        user_id = 'free_user_2'
        
        # Use all 3 queries
        for i in range(3):
            middleware.check_and_record(user_id, f'skill_{i}')
        
        # 4th query should be blocked
        result = middleware.check_and_record(user_id, 'price-lookup')
        
        assert result['allowed'] == False
        assert 'upgrade' in result['message'].lower() or 'pro' in result['message'].lower()
    
    def test_pro_user_unlimited_always_allowed(self, middleware, sub_service, db_pool):
        """Pro user with unlimited queries should always be allowed"""
        user_id = 'pro_user_1'
        
        # Ensure user exists first (creates free subscription)
        sub_service.get_subscription_status(user_id)
        
        # Upgrade user to Pro plan
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE subscriptions SET plan_id = 3 WHERE user_id = ?",
                (user_id,)
            )
        
        # Make many queries
        for i in range(10):
            result = middleware.check_and_record(user_id, f'skill_{i}')
            assert result['allowed'] == True
        
        # Should still be allowed
        result = middleware.check_and_record(user_id, 'price-lookup')
        assert result['allowed'] == True
    
    def test_onboarding_skill_exempt_from_limits(self, middleware, sub_service):
        """Onboarding skill should not count against query limits"""
        user_id = 'onboarding_user_1'
        
        # Use all 3 queries
        for i in range(3):
            middleware.check_and_record(user_id, f'skill_{i}')
        
        # Regular query should be blocked
        result = middleware.check_and_record(user_id, 'price-lookup')
        assert result['allowed'] == False
        
        # But onboarding should still be allowed
        result = middleware.check_and_record(user_id, 'onboarding')
        assert result['allowed'] == True
        assert 'exempt' in result.get('message', '').lower() or result.get('exempt') == True
    
    def test_usage_recording_increments_correctly(self, middleware, sub_service):
        """Usage recording should increment query count correctly"""
        user_id = 'usage_user_1'
        
        # Check and record first query
        result1 = middleware.check_and_record(user_id, 'price-lookup')
        assert result1['allowed'] == True
        assert result1['remaining'] == 2
        
        # Check and record second query
        result2 = middleware.check_and_record(user_id, 'formula-cost')
        assert result2['allowed'] == True
        assert result2['remaining'] == 1
        
        # Check and record third query
        result3 = middleware.check_and_record(user_id, 'nutrition-analysis')
        assert result3['allowed'] == True
        assert result3['remaining'] == 0
        
        # Fourth query should be blocked
        result4 = middleware.check_and_record(user_id, 'customer-record')
        assert result4['allowed'] == False
