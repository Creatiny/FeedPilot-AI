"""
FeedSales AI - Subscription Service Tests
TDD: RED phase - write failing tests first
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.pool import DatabasePool
from src.services.subscription_service import SubscriptionService


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


class TestSubscriptionPlans:
    """Test subscription plans seeding and retrieval"""
    
    def test_plans_exist_after_init(self, db_pool):
        """Verify default plans are seeded after database initialization"""
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM subscription_plans")
            count = cursor.fetchone()[0]
            assert count == 3, "Should have 3 default plans"
    
    def test_free_plan_properties(self, db_pool):
        """Verify free plan has correct properties"""
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscription_plans WHERE name = 'free'")
            plan = cursor.fetchone()
            assert plan is not None
            assert plan['price_monthly'] == 0.0
            assert plan['queries_per_day'] == 3
            assert plan['max_customers'] == 5
    
    def test_pro_plan_unlimited_queries(self, db_pool):
        """Verify pro plan has unlimited queries (-1)"""
        with db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT queries_per_day FROM subscription_plans WHERE name = 'pro'")
            result = cursor.fetchone()
            assert result['queries_per_day'] == -1


class TestSubscriptionStatus:
    """Test subscription status retrieval"""
    
    def test_new_user_has_free_plan(self, sub_service):
        """New user should automatically get free plan"""
        status = sub_service.get_subscription_status('new_user_123')
        
        assert status['plan_name'] == 'free'
        assert status['queries_per_day'] == 3
        assert status['is_in_trial'] == False
    
    def test_get_existing_user_status(self, sub_service):
        """Get status for user with existing subscription"""
        # Create subscription first
        sub_service.get_subscription_status('user_456')
        
        # Get again
        status = sub_service.get_subscription_status('user_456')
        assert status['user_id'] == 'user_456'
        assert status['plan_name'] == 'free'


class TestTrialPeriod:
    """Test trial period functionality"""
    
    def test_start_trial(self, sub_service):
        """Start 7-day trial for user"""
        result = sub_service.start_trial('trial_user_1', days=7)
        
        assert result['success'] == True
        assert result['trial_days'] == 7
        assert 'trial_ends_at' in result
    
    def test_trial_status_reflected(self, sub_service):
        """Trial status should be reflected in subscription status"""
        sub_service.start_trial('trial_user_2', days=7)
        
        status = sub_service.get_subscription_status('trial_user_2')
        assert status['is_in_trial'] == True
        assert status['trial_days_left'] > 0


class TestQueryLimits:
    """Test query limit checking and recording"""
    
    def test_check_limit_free_user_allowed(self, sub_service):
        """Free user under limit should be allowed"""
        # New user has 3 queries/day
        result = sub_service.check_query_limit('limit_user_1')
        
        assert result['allowed'] == True
        assert result['queries_remaining'] == 3
    
    def test_check_limit_free_user_exceeded(self, sub_service):
        """Free user over limit should be blocked"""
        user_id = 'limit_user_2'
        
        # Use 3 queries
        for i in range(3):
            sub_service.record_usage(user_id)
        
        # 4th query should be blocked
        result = sub_service.check_query_limit(user_id)
        assert result['allowed'] == False
        assert 'limit' in result['message'].lower()
    
    def test_record_usage_increments_count(self, sub_service):
        """Recording usage should increment query count"""
        user_id = 'usage_user_1'
        
        sub_service.record_usage(user_id)
        sub_service.record_usage(user_id)
        
        count = sub_service.get_daily_usage(user_id)
        assert count == 2


class TestReferralSystem:
    """Test referral functionality"""
    
    def test_get_referral_link(self, sub_service):
        """Generate referral link for user"""
        link = sub_service.get_referral_link('referrer_1')
        
        assert link is not None
        assert 'ref_' in link
    
    def test_apply_referral_bonus(self, sub_service):
        """Both referrer and referee get bonus days"""
        referrer = 'referrer_2'
        referee = 'referee_2'
        
        # Ensure both users exist
        sub_service.get_subscription_status(referrer)
        sub_service.get_subscription_status(referee)
        
        result = sub_service.apply_referral_bonus(referrer, referee)
        
        assert result['success'] == True
        assert result['bonus_days'] == 7
        
        # Check both got bonus
        referrer_status = sub_service.get_subscription_status(referrer)
        referee_status = sub_service.get_subscription_status(referee)
        
        assert referrer_status['referral_bonus_days'] >= 7
        assert referee_status['referral_bonus_days'] >= 7
    
    def test_cannot_refer_self(self, sub_service):
        """User cannot refer themselves"""
        user_id = 'self_ref_user'
        sub_service.get_subscription_status(user_id)
        
        result = sub_service.apply_referral_bonus(user_id, user_id)
        
        assert result['success'] == False
        assert 'yourself' in result['message'].lower()
