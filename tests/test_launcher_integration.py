"""
FeedSales AI - Launcher Integration Tests

Tests the complete integration of subscription, query limits, and referral services
through the launcher interface.

Run from project root: python -m pytest tests/test_launcher_integration.py -v
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        
        # Import and create DatabasePool
        from src.database.pool import DatabasePool
        
        # Reset singleton for test isolation
        DatabasePool._instance = None
        
        pool = DatabasePool(db_path)
        yield db_path
        
        # Cleanup
        DatabasePool._instance = None


class TestFullIntegration:
    """Test complete integration scenarios."""
    
    def test_new_user_journey(self, temp_db):
        """Test complete new user journey."""
        from src.database.pool import DatabasePool
        from src.services.subscription_service import SubscriptionService
        from src.services.referral_service import ReferralService
        from src.middleware.query_limit_middleware import QueryLimitMiddleware
        
        pool = DatabasePool(temp_db)
        sub_service = SubscriptionService(pool)
        referral_service = ReferralService(pool)
        middleware = QueryLimitMiddleware(sub_service)
        
        user_id = "journey_user"
        
        # 1. Check initial status (should be free)
        status = sub_service.get_subscription_status(user_id)
        assert status['plan_name'] == 'free'
        
        # 2. Start trial
        trial = sub_service.start_trial(user_id, days=7)
        assert trial['success'] is True
        
        # 3. Get referral link
        link = referral_service.get_referral_link(user_id)
        assert link.startswith("ref_")
        
        # 4. Use queries (should work during trial)
        for i in range(3):
            result = middleware.check_and_record(user_id, "price-lookup")
            assert result['allowed'] is True
    
    def test_referral_bonus_flow(self, temp_db):
        """Test referral bonus flow."""
        from src.database.pool import DatabasePool
        from src.services.referral_service import ReferralService
        
        pool = DatabasePool(temp_db)
        referral_service = ReferralService(pool)
        
        referrer = "bonus_referrer"
        referee = "bonus_referee"
        
        # Get referrer's link
        link = referral_service.get_referral_link(referrer)
        assert link.startswith("ref_")
        
        # Process referral
        result = referral_service.process_referral(
            referral_code=link,
            new_user_id=referee
        )
        
        assert result['success'] is True
        assert result['bonus_days'] == 7
        
        # Check both users got bonus
        referrer_stats = referral_service.get_referral_stats(referrer)
        referee_stats = referral_service.get_referral_stats(referee)
        
        assert referrer_stats['total_bonus_days'] == 7
        assert referee_stats['total_bonus_days'] == 7
    
    def test_three_referrals_permanent_free(self, temp_db):
        """Test that 3 referrals grant permanent free Pro."""
        from src.database.pool import DatabasePool
        from src.services.referral_service import ReferralService
        
        pool = DatabasePool(temp_db)
        referral_service = ReferralService(pool)
        
        referrer = "permanent_referrer"
        
        # Make 3 referrals
        for i in range(3):
            referee = f"permanent_referee_{i}"
            result = referral_service.process_referral(
                referrer_id=referrer,
                referee_id=referee
            )
            assert result['success'] is True
        
        # Check if permanent free
        stats = referral_service.get_referral_stats(referrer)
        assert stats['referral_count'] == 3
        assert stats['is_permanent_free'] is True
        assert stats['plan_name'] == 'pro'
