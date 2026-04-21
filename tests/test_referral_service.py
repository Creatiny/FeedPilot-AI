"""
FeedSales AI - Referral Service Tests

Tests for the referral system: referral links, stats, and permanent free upgrade.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

# Will import after implementation
# from src.services.referral_service import ReferralService


class MockConnection:
    """Mock database connection with dict-like rows."""
    
    def __init__(self, db_path):
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def cursor(self):
        return self.conn.cursor()
    
    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.commit()
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.close()
        return False


class MockDBPool:
    """Mock database pool."""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_connection(self):
        return MockConnection(self.db_path)


@pytest.fixture
def temp_db():
    """Create a temporary database with schema."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Create schema
    schema_path = '/tmp/feed-sales-ai-mvp/src/database/schema.sql'
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    conn.close()
    
    yield db_path
    
    os.unlink(db_path)


@pytest.fixture
def referral_service(temp_db):
    """Create ReferralService instance."""
    from src.services.referral_service import ReferralService
    pool = MockDBPool(temp_db)
    return ReferralService(pool)


class TestReferralService:
    """Tests for ReferralService."""
    
    def test_get_referral_link(self, referral_service):
        """Test generating referral link for user."""
        link = referral_service.get_referral_link('user_123')
        
        assert link is not None
        assert link.startswith('ref_')
        assert len(link) == 12  # 'ref_' + 8 chars
    
    def test_get_referral_stats_new_user(self, referral_service):
        """Test getting referral stats for new user."""
        stats = referral_service.get_referral_stats('user_123')
        
        assert stats['referral_count'] == 0
        assert stats['total_bonus_days'] == 0
        assert stats['referral_link'] is not None
        assert stats['referral_link'].startswith('ref_')
    
    def test_process_referral_success(self, referral_service):
        """Test processing a valid referral."""
        # Referrer invites referee
        result = referral_service.process_referral(
            referrer_id='user_123',
            referee_id='user_456'
        )
        
        assert result['success'] is True
        assert result['bonus_days'] == 7
        assert 'bonus applied' in result['message'].lower()
    
    def test_process_referral_updates_stats(self, referral_service):
        """Test that referral updates stats for referrer."""
        # Process referral
        referral_service.process_referral(
            referrer_id='user_123',
            referee_id='user_456'
        )
        
        # Check referrer stats
        stats = referral_service.get_referral_stats('user_123')
        assert stats['referral_count'] == 1
        assert stats['total_bonus_days'] == 7
    
    def test_self_referral_blocked(self, referral_service):
        """Test that self-referral is blocked."""
        result = referral_service.process_referral(
            referrer_id='user_123',
            referee_id='user_123'
        )
        
        assert result['success'] is False
        assert 'cannot refer yourself' in result['message'].lower()
    
    def test_duplicate_referral_blocked(self, referral_service):
        """Test that duplicate referral is blocked."""
        # First referral succeeds
        result1 = referral_service.process_referral(
            referrer_id='user_123',
            referee_id='user_456'
        )
        assert result1['success'] is True
        
        # Second referral with same referee fails
        result2 = referral_service.process_referral(
            referrer_id='user_789',
            referee_id='user_456'
        )
        assert result2['success'] is False
        assert 'already been referred' in result2['message'].lower()
    
    def test_three_referrals_pro_bonus(self, referral_service):
        """Test that 3+ referrals grant 1 month Pro each (starting from 3rd)."""
        # User makes 3 referrals
        for i in range(3):
            result = referral_service.process_referral(
                referrer_id='user_123',
                referee_id=f'user_{i+1}'
            )
            assert result['success'] is True
        
        # Check referrer got Pro bonus months
        # 3 referrals = 1 month Pro (only the 3rd referral grants Pro)
        stats = referral_service.get_referral_stats('user_123')
        assert stats['referral_count'] == 3
        assert stats['pro_bonus_months'] == 1  # 1 month Pro (from 3rd referral)
        assert stats['is_permanent_free'] is True
        assert stats['plan_name'].lower() == 'pro'
    
    def test_fourth_referral_adds_more_pro(self, referral_service):
        """Test that 4th referral adds another month Pro."""
        # User makes 4 referrals
        for i in range(4):
            result = referral_service.process_referral(
                referrer_id='user_123',
                referee_id=f'user_{i+1}'
            )
            assert result['success'] is True
        
        # Check referrer got 2 months Pro (3rd and 4th referrals)
        stats = referral_service.get_referral_stats('user_123')
        assert stats['referral_count'] == 4
        assert stats['pro_bonus_months'] == 2  # 2 months Pro (from 3rd and 4th referrals)
    
    def test_referee_gets_bonus(self, referral_service):
        """Test that referee also gets bonus days."""
        result = referral_service.process_referral(
            referrer_id='user_123',
            referee_id='user_456'
        )
        
        # Check referee subscription
        from src.services.subscription_service import SubscriptionService
        pool = referral_service.db_pool
        sub_service = SubscriptionService(pool)
        status = sub_service.get_subscription_status('user_456')
        
        assert status['referral_bonus_days'] >= 7
