"""
Onboarding Skill - Guide new users through first valuable action

Integrates:
- Referral link display
- Subscription status information
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "feed_sales.db"


def get_subscription_info(user_id: str) -> dict:
    """Get user's subscription and trial info"""
    try:
        from src.database.pool import DatabasePool
        from src.services.subscription_service import SubscriptionService
        
        db_path = PROJECT_ROOT / "data" / "feed_sales.db"
        pool = DatabasePool(str(db_path))
        service = SubscriptionService(pool)
        return service.get_subscription_status(user_id)
    except Exception as e:
        return {"plan_name": "free", "is_in_trial": False, "trial_days_left": 0}


def get_referral_link(user_id: str) -> str:
    """Get user's referral link"""
    try:
        from src.database.pool import DatabasePool
        from src.services.referral_service import ReferralService
        
        db_path = PROJECT_ROOT / "data" / "feed_sales.db"
        pool = DatabasePool(str(db_path))
        service = ReferralService(pool)
        return service.get_referral_link(user_id)
    except Exception as e:
        return ""


def get_user_state(user_id: str) -> dict:
    """Get user's onboarding state"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_onboarding (
                user_id TEXT PRIMARY KEY,
                onboarding_step INTEGER DEFAULT 0,
                first_action_type TEXT,
                onboarding_started_at TEXT,
                onboarding_completed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('SELECT * FROM user_onboarding WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "user_id": row[0],
                "step": row[1],
                "first_action_type": row[2],
                "started_at": row[3],
                "completed_at": row[4]
            }
        return {"step": 0}
    except Exception as e:
        return {"step": 0, "error": str(e)}


def update_user_state(user_id: str, step: int, action_type: str = None):
    """Update user's onboarding state"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO user_onboarding (user_id, onboarding_step, first_action_type, onboarding_started_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                onboarding_step = ?,
                first_action_type = COALESCE(?, first_action_type),
                onboarding_completed_at = CASE WHEN ? = 3 THEN ? ELSE onboarding_completed_at END
        ''', (user_id, step, action_type, now, step, action_type, step, now))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating state: {e}")
        return False


def handle_onboarding(user_id: str, message: str) -> dict:
    """
    Handle onboarding flow
    
    Returns structured response for OpenClaw Agent
    """
    message_lower = message.lower().strip()
    state = get_user_state(user_id)
    
    # Step 0: New user - show welcome
    if state["step"] == 0 or message_lower in ["/start", "start", "hi", "hello"]:
        update_user_state(user_id, 1)
        
        return {
            "success": True,
            "data": {
                "step": 1,
                "message": f"""👋 Welcome to FeedPilot AI!

I'm your pocket feed assistant. What do you want to do first?

1️⃣ Check ingredient prices
2️⃣ Calculate feed formula cost
3️⃣ Set a customer reminder

Just type 1, 2, or 3 to start!""",
                "options": ["1", "2", "3"]
            }
        }
    
    # Step 1: User chose an option
    if state["step"] == 1:
        if message_lower in ["1", "price", "prices"]:
            update_user_state(user_id, 2, "price")
            return {
                "success": True,
                "data": {
                    "step": 2,
                    "action": "price",
                    "message": """📊 Great choice! Let's check some prices.

Which ingredient? Type the name or choose:
• corn
• soybean meal
• fish meal
• wheat
• all (see all prices)""",
                    "options": ["corn", "soybean meal", "fish meal", "wheat", "all"]
                }
            }
        
        elif message_lower in ["2", "formula", "cost", "calculate"]:
            update_user_state(user_id, 2, "formula")
            return {
                "success": True,
                "data": {
                    "step": 2,
                    "action": "formula",
                    "message": """🧮 Let's calculate a formula cost!

Tell me your formula ingredients, like:
"corn 60%, soybean meal 25%, premix 5%..."

Or type 'example' to see a sample calculation.""",
                    "options": ["example"]
                }
            }
        
        elif message_lower in ["3", "remind", "reminder"]:
            update_user_state(user_id, 2, "reminder")
            return {
                "success": True,
                "data": {
                    "step": 2,
                    "action": "reminder",
                    "message": """⏰ Never miss a follow-up!

What should I remind you about?
Example: "Follow up with John next Monday"

Or type 'help' for more options.""",
                    "options": ["help"]
                }
            }
        
        else:
            return {
                "success": True,
                "data": {
                    "step": 1,
                    "message": "Please choose 1, 2, or 3 to continue.",
                    "options": ["1", "2", "3"]
                }
            }
    
    # Step 2: User completed first action - show success with referral info
    if state["step"] == 2:
        update_user_state(user_id, 3)
        
        # Get subscription info
        sub_info = get_subscription_info(user_id)
        referral_link = get_referral_link(user_id)
        
        referral_msg = ""
        if referral_link:
            referral_msg = f"""

🎁 **Referral Program**
Share your link: {referral_link}
When friends join, you both get 7 extra days free!
Invite 3 friends = permanent free Pro!"""
        
        return {
            "success": True,
            "data": {
                "step": 3,
                "completed": True,
                "message": f"""✅ Nice! You've completed your first action!

Here's what else you can do:
• /formula - Calculate feed cost
• /remind - Set customer reminders
• /customer - Manage your customers
• /help - See all features
• /subscription - Check your plan{referral_msg}

💡 Tip: Try asking "What's the corn price trend?" for insights!"""
            }
        }
    
    # Already completed onboarding
    return {
        "success": True,
        "data": {
            "step": 3,
            "completed": True,
            "message": "You've already completed onboarding. Type /help to see all features!"
        }
    }


if __name__ == "__main__":
    # Test
    user_id = sys.argv[1] if len(sys.argv) > 1 else "test_user"
    message = sys.argv[2] if len(sys.argv) > 2 else "/start"
    
    result = handle_onboarding(user_id, message)
    print(json.dumps(result, indent=2))
