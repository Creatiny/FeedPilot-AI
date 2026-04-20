"""
FeedSales AI - Referral Service

Handles referral processing, stats tracking, and permanent free upgrades.
Extends SubscriptionService functionality.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import hashlib


class ReferralService:
    """Service for managing referrals, stats, and permanent free upgrades."""
    
    # Constants
    BONUS_DAYS_PER_REFERRAL = 7
    REFERRALS_FOR_PERMANENT_FREE = 3
    
    def __init__(self, db_pool):
        """Initialize with database pool."""
        self.db_pool = db_pool
        self._referral_code_cache = {}
    
    def get_referral_link(self, user_id: str) -> str:
        self._ensure_user_exists(user_id)
        hash_obj = hashlib.md5(user_id.encode())
        referral_code = hash_obj.hexdigest()[:8]
        full_code = f"ref_{referral_code}"
        self._referral_code_cache[full_code] = user_id
        return full_code
    
    def get_referral_stats(self, user_id: str) -> Dict:
        self._ensure_user_exists(user_id)
        referral_link = self.get_referral_link(user_id)
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ?",
                (user_id,)
            )
            result = cursor.fetchone()
            referral_count = result["count"] if result else 0
            
            cursor.execute(
                "SELECT referral_bonus_days, plan_id FROM subscriptions WHERE user_id = ?",
                (user_id,)
            )
            sub = cursor.fetchone()
            total_bonus_days = sub["referral_bonus_days"] if sub and sub["referral_bonus_days"] else 0
            
            is_permanent_free = False
            plan_name = "free"
            if sub:
                cursor.execute(
                    "SELECT name FROM subscription_plans WHERE id = ?",
                    (sub["plan_id"],)
                )
                plan = cursor.fetchone()
                if plan:
                    plan_name = plan["name"]
                if plan and plan["name"].lower() == "pro" and referral_count >= self.REFERRALS_FOR_PERMANENT_FREE:
                    is_permanent_free = True
        
        return {
            "referral_count": referral_count,
            "total_bonus_days": total_bonus_days,
            "referral_link": referral_link,
            "is_permanent_free": is_permanent_free,
            "plan_name": plan_name
        }
    
    def process_referral(self, referrer_id: str = None, referee_id: str = None, 
                         referral_code: str = None, new_user_id: str = None) -> Dict:
        """
        Process a referral.
        
        Can be called with either:
        - referrer_id + referee_id (direct)
        - referral_code + new_user_id (via code)
        """
        # Handle both calling conventions
        if referrer_id is None and referral_code is not None:
            referrer_id = self._decode_referral_code(referral_code)
            if referrer_id is None:
                return {"success": False, "message": "Invalid referral code"}
        
        if referee_id is None:
            referee_id = new_user_id
        
        if referrer_id == referee_id:
            return {"success": False, "message": "You cannot refer yourself"}
        
        self._ensure_user_exists(referrer_id)
        self._ensure_user_exists(referee_id)
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM referrals WHERE referee_id = ?",
                (referee_id,)
            )
            if cursor.fetchone():
                return {"success": False, "message": "User has already been referred"}
            
            cursor.execute(
                "INSERT INTO referrals (referrer_id, referee_id, bonus_days) VALUES (?, ?, ?)",
                (referrer_id, referee_id, self.BONUS_DAYS_PER_REFERRAL)
            )
            
            cursor.execute(
                "UPDATE subscriptions SET referral_bonus_days = COALESCE(referral_bonus_days, 0) + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (self.BONUS_DAYS_PER_REFERRAL, referrer_id)
            )
            cursor.execute(
                "UPDATE subscriptions SET referral_bonus_days = COALESCE(referral_bonus_days, 0) + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (self.BONUS_DAYS_PER_REFERRAL, referee_id)
            )
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ?",
                (referrer_id,)
            )
            referral_count = cursor.fetchone()["count"]
            
            permanent_free = False
            if referral_count >= self.REFERRALS_FOR_PERMANENT_FREE:
                cursor.execute(
                    "UPDATE subscriptions SET plan_id = 3, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (referrer_id,)
                )
                permanent_free = True
        
        return {
            "success": True,
            "bonus_days": self.BONUS_DAYS_PER_REFERRAL,
            "message": f"Bonus applied! Both users received {self.BONUS_DAYS_PER_REFERRAL} bonus days!",
            "permanent_free": permanent_free
        }
    
    def get_subscription_status(self, user_id: str) -> Dict:
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,))
            subscription = cursor.fetchone()
            
            if subscription is None:
                cursor.execute(
                    "INSERT INTO subscriptions (user_id, plan_id, is_in_trial, referral_bonus_days) VALUES (?, 1, 0, 0)",
                    (user_id,)
                )
                cursor.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,))
                subscription = cursor.fetchone()
            
            cursor.execute("SELECT * FROM subscription_plans WHERE id = ?", (subscription["plan_id"],))
            plan = cursor.fetchone()
            
            trial_days_left = 0
            if subscription["is_in_trial"] and subscription["trial_ends_at"]:
                trial_ends = datetime.fromisoformat(subscription["trial_ends_at"])
                now = datetime.now()
                if trial_ends > now:
                    trial_days_left = (trial_ends - now).days + 1
            
            return {
                "user_id": user_id,
                "plan_name": plan["name"],
                "plan_display_name": plan["display_name"],
                "queries_per_day": plan["queries_per_day"],
                "is_in_trial": bool(subscription["is_in_trial"]),
                "trial_days_left": trial_days_left,
                "referral_bonus_days": subscription["referral_bonus_days"] or 0
            }
    
    def _ensure_user_exists(self, user_id: str) -> None:
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM subscriptions WHERE user_id = ?", (user_id,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO subscriptions (user_id, plan_id, is_in_trial, referral_bonus_days) VALUES (?, 1, 0, 0)",
                    (user_id,)
                )
    
    def _decode_referral_code(self, referral_code: str) -> Optional[str]:
        if not referral_code or not referral_code.startswith("ref_"):
            return None
        
        if referral_code in self._referral_code_cache:
            return self._referral_code_cache[referral_code]
        
        # Try to find by checking all users (inefficient but works for MVP)
        # In production, store referral_code in subscriptions table
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM subscriptions")
            users = cursor.fetchall()
            
            for user in users:
                user_id = user["user_id"]
                hash_obj = hashlib.md5(user_id.encode())
                code = f"ref_{hash_obj.hexdigest()[:8]}"
                if code == referral_code:
                    self._referral_code_cache[referral_code] = user_id
                    return user_id
        
        return None
