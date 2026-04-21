"""
FeedSales AI - Subscription Service

Handles subscription management, trials, query limits, and referrals.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import hashlib


class SubscriptionService:
    """Service for managing user subscriptions, trials, and usage limits."""
    
    def __init__(self, db_pool):
        """Initialize with database pool."""
        self.db_pool = db_pool
    
    def get_subscription_status(self, user_id: str) -> Dict:
        """
        Get subscription status for a user.
        
        Creates a new subscription with free plan if user doesn't exist.
        
        Returns:
            dict with plan_name, queries_per_day, is_in_trial, trial_days_left,
            user_id, referral_bonus_days
        """
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get or create subscription
            cursor.execute(
                "SELECT * FROM subscriptions WHERE user_id = ?",
                (user_id,)
            )
            subscription = cursor.fetchone()
            
            if subscription is None:
                # Create new subscription with free plan
                cursor.execute(
                    """INSERT INTO subscriptions (user_id, plan_id, is_in_trial, referral_bonus_days)
                       VALUES (?, 1, 0, 0)""",
                    (user_id,)
                )
                cursor.execute(
                    "SELECT * FROM subscriptions WHERE user_id = ?",
                    (user_id,)
                )
                subscription = cursor.fetchone()
            
            # Get plan details
            cursor.execute(
                "SELECT * FROM subscription_plans WHERE id = ?",
                (subscription['plan_id'],)
            )
            plan = cursor.fetchone()
            
            # Calculate trial days left
            trial_days_left = 0
            if subscription['is_in_trial'] and subscription['trial_ends_at']:
                trial_ends = datetime.fromisoformat(subscription['trial_ends_at'])
                now = datetime.now()
                if trial_ends > now:
                    trial_days_left = (trial_ends - now).days + 1
            
            return {
                'user_id': user_id,
                'plan_name': plan['name'],
                'plan_display_name': plan['display_name'],
                'queries_per_day': plan['queries_per_day'],
                'is_in_trial': bool(subscription['is_in_trial']),
                'trial_days_left': trial_days_left,
                'referral_bonus_days': subscription['referral_bonus_days'] or 0
            }
    
    def start_trial(self, user_id: str, days: int = 7) -> Dict:
        """
        Start a trial period for a user.
        
        Args:
            user_id: User identifier
            days: Trial duration in days (default 7)
            
        Returns:
            dict with success, trial_days, trial_ends_at
        """
        # Ensure user exists
        self.get_subscription_status(user_id)
        
        now = datetime.now()
        trial_ends = now + timedelta(days=days)
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE subscriptions 
                   SET is_in_trial = 1, 
                       trial_started_at = ?,
                       trial_ends_at = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?""",
                (now.isoformat(), trial_ends.isoformat(), user_id)
            )
        
        return {
            'success': True,
            'trial_days': days,
            'trial_ends_at': trial_ends.isoformat()
        }
    
    def check_query_limit(self, user_id: str) -> Dict:
        """
        Check if user can make a query.
        
        Args:
            user_id: User identifier
            
        Returns:
            dict with allowed, queries_remaining, message
        """
        status = self.get_subscription_status(user_id)
        queries_per_day = status['queries_per_day']
        
        # Unlimited queries (-1)
        if queries_per_day == -1:
            return {
                'allowed': True,
                'queries_remaining': -1,
                'message': 'Unlimited queries'
            }
        
        # Get today's usage
        today = datetime.now().date().isoformat()
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT query_count FROM daily_usage 
                   WHERE user_id = ? AND usage_date = ?""",
                (user_id, today)
            )
            result = cursor.fetchone()
            used = result['query_count'] if result else 0
        
        remaining = queries_per_day - used
        
        if remaining > 0:
            return {
                'allowed': True,
                'queries_remaining': remaining,
                'message': f'{remaining} queries remaining today'
            }
        else:
            return {
                'allowed': False,
                'queries_remaining': 0,
                'message': f'Daily limit reached ({queries_per_day} queries/day). Upgrade for more.'
            }
    
    def record_usage(self, user_id: str) -> None:
        """
        Record a query usage for a user.
        
        Args:
            user_id: User identifier
        """
        # Ensure user exists
        self.get_subscription_status(user_id)
        
        today = datetime.now().date().isoformat()
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            # Try to insert or update
            cursor.execute(
                """INSERT INTO daily_usage (user_id, usage_date, query_count)
                   VALUES (?, ?, 1)
                   ON CONFLICT(user_id, usage_date) 
                   DO UPDATE SET query_count = query_count + 1, updated_at = CURRENT_TIMESTAMP""",
                (user_id, today)
            )
    
    def get_daily_usage(self, user_id: str) -> int:
        """
        Get today's query count for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of queries used today
        """
        today = datetime.now().date().isoformat()
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT query_count FROM daily_usage 
                   WHERE user_id = ? AND usage_date = ?""",
                (user_id, today)
            )
            result = cursor.fetchone()
            return result['query_count'] if result else 0
    
    def get_referral_link(self, user_id: str) -> str:
        """
        Generate a referral link for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Referral link string
        """
        # Ensure user exists
        self.get_subscription_status(user_id)
        
        # Create unique referral code from user_id
        hash_obj = hashlib.md5(user_id.encode())
        referral_code = hash_obj.hexdigest()[:8]
        
        return f"ref_{referral_code}"
    
    def apply_referral_bonus(self, referrer_id: str, referee_id: str, bonus_days: int = 7) -> Dict:
        """
        Apply referral bonus to both referrer and referee.
        
        Args:
            referrer_id: User who made the referral
            referee_id: User who was referred
            bonus_days: Bonus days to add (default 7)
            
        Returns:
            dict with success, bonus_days, message (if failed)
        """
        # Check for self-referral
        if referrer_id == referee_id:
            return {
                'success': False,
                'message': 'You cannot refer yourself'
            }
        
        # Ensure both users exist
        self.get_subscription_status(referrer_id)
        self.get_subscription_status(referee_id)
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if referee was already referred
            cursor.execute(
                "SELECT id FROM referrals WHERE referee_id = ?",
                (referee_id,)
            )
            if cursor.fetchone():
                return {
                    'success': False,
                    'message': 'User has already been referred'
                }
            
            # Create referral record
            cursor.execute(
                """INSERT INTO referrals (referrer_id, referee_id, bonus_days)
                   VALUES (?, ?, ?)""",
                (referrer_id, referee_id, bonus_days)
            )
            
            # Add bonus days to both users
            cursor.execute(
                """UPDATE subscriptions 
                   SET referral_bonus_days = COALESCE(referral_bonus_days, 0) + ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?""",
                (bonus_days, referrer_id)
            )
            cursor.execute(
                """UPDATE subscriptions 
                   SET referral_bonus_days = COALESCE(referral_bonus_days, 0) + ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?""",
                (bonus_days, referee_id)
            )
        
        return {
            'success': True,
            'bonus_days': bonus_days
        }
