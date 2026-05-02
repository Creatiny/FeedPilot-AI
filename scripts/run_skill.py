#!/usr/bin/env python3
"""
FeedSales AI - Unified Skill Runner

A command-line entry point for all skills.
Usage: python3 run_skill.py <skill_name> "<user_message>"
"""

import asyncio
import html
import importlib.util
import json
import logging
import os
import re
import sqlite3
import sys
import unicodedata
from typing import Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, os.path.join(WORKSPACE, "skills"))

DB_PATH = os.path.join(WORKSPACE, "data", "feed_sales.db")

# --- Prompt-injection guard for skill runner ---
# Blocks common LLM prompt-injection patterns that could escape the skill context.
_BLOCKED_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|commands)", re.I | re.DOTALL),
    re.compile(r"forget\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|commands)", re.I | re.DOTALL),
    re.compile(r"you\s+are\s+now\s+(a\s+)?new\s+(assistant|ai|bot)", re.I | re.DOTALL),
    re.compile(r"system\s*prompt\s*:\s*", re.I | re.DOTALL),
    re.compile(r"<\|system\|>", re.I | re.DOTALL),
    re.compile(r"<\|im_start\|>\s*system", re.I | re.DOTALL),
    re.compile(r"\{\{\s*system\s*\}\}", re.I | re.DOTALL),
    re.compile(r"\[\s*system\s*\]", re.I | re.DOTALL),
    re.compile(r"disregard\s+(the\s+)?(above|previous|earlier)", re.I | re.DOTALL),
    re.compile(r"do\s+not\s+follow\s+(the\s+)?(above|previous|earlier)\s+instructions", re.I | re.DOTALL),
]

_MAX_MESSAGE_BYTES = 3800  # Telegram hard limit is 4096 UTF-8 bytes; keep margin

# Map Cyrillic homoglyphs (and other lookalikes) back to ASCII to defeat bypasses.
_HOMOGLYPH_MAP = str.maketrans({
    "і": "i", "І": "I",  # Cyrillic i
    "о": "o", "О": "O",  # Cyrillic o
    "е": "e", "Е": "E",  # Cyrillic e
    "р": "p", "Р": "P",  # Cyrillic p
    "а": "a", "А": "A",  # Cyrillic a
    "с": "c", "С": "C",  # Cyrillic c
    "х": "x", "Х": "X",  # Cyrillic kh
    "у": "y", "У": "Y",  # Cyrillic u
    "ј": "j", "Ј": "J",  # Cyrillic je
    "к": "k", "К": "K",  # Cyrillic k
    "т": "t", "Т": "T",  # Cyrillic t
    "ѕ": "s", "Ѕ": "S",  # Cyrillic dze
    "в": "b", "В": "B",  # Cyrillic v
    "м": "m", "М": "M",  # Cyrillic m
    "н": "n", "Н": "N",  # Cyrillic n
    "г": "r", "Г": "R",  # Cyrillic g (looks like r in some fonts, but map anyway)
    "з": "z", "З": "Z",  # Cyrillic z
})

logger = logging.getLogger(__name__)


def _validate_user_message(user_message: str) -> Optional[str]:
    """Return error string if message looks like a prompt injection, else None."""
    if not isinstance(user_message, str):
        return "Invalid input type."
    byte_len = len(user_message.encode("utf-8"))
    if byte_len > _MAX_MESSAGE_BYTES:
        return f"Message too long ({byte_len} bytes, max {_MAX_MESSAGE_BYTES})."
    # Normalize Unicode to defeat homoglyph bypasses (e.g. Cyrillic іgnоrе)
    normalized = unicodedata.normalize("NFKC", user_message)
    # Fold lookalike characters back to ASCII so regexes match
    folded = normalized.translate(_HOMOGLYPH_MAP)
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(folded):
            logger.warning("Prompt injection blocked: %r", user_message[:200])
            return "Potentially unsafe input detected. Please rephrase your request."
    return None


from src.database.pool import DatabasePool
from src.services.calculation_service import CalculationService
from src.services.customer_service import CustomerService
from src.services.formula_service import FormulaService
from src.services.price_service import PriceService
from src.services.reminder_service import ReminderService


class ServiceResult:
    """Compatibility result object used by local adapters."""

    def __init__(self, success: bool, data=None, source=None, error_code=None, error_message=None):
        self.success = success
        self.data = data if data else {}
        self.source = source
        self.error_code = error_code
        self.error_message = error_message


_DB_POOL = DatabasePool(DB_PATH)


class SkillPriceService:
    def __init__(self):
        self._svc = PriceService(_DB_POOL)

    def get_price(self, user_id: str, ingredient_name: str):
        return self._svc.get_price(user_id, ingredient_name)

    def list_public_prices(self):
        return self._svc.list_public_prices()


class SkillFormulaService:
    def __init__(self):
        self._svc = FormulaService(_DB_POOL)

    def get_formula(self, user_id: str, formula_name: str):
        return self._svc.get_formula(user_id, formula_name)

    def list_formulas(self, user_id: str):
        return self._svc.list_formulas(user_id)


class SkillCalculationService:
    def __init__(self):
        self._svc = CalculationService(_DB_POOL)

    def calculate_cost(self, user_id: str, formula_name: str):
        return self._svc.calculate_cost(user_id, formula_name)


class SkillCustomerService:
    def __init__(self):
        self._svc = CustomerService(_DB_POOL)

    def create_customer(self, user_id: str, data: dict):
        return self._svc.create_customer(user_id, data)

    def list_customers(self, user_id: str):
        return self._svc.list_customers(user_id)

    def get_customer(self, user_id: str, name: str):
        return self._svc.get_customer(user_id, name)

    def update_customer(self, user_id: str, customer_id: int, data: dict):
        return self._svc.update_customer(user_id, customer_id, data)

    def delete_customer(self, user_id: str, customer_id: int):
        return self._svc.delete_customer(user_id, customer_id)


class SkillReminderService:
    def __init__(self):
        self._svc = ReminderService(_DB_POOL)

    def create_reminder(
        self,
        user_id: str,
        reminder_type: str,
        threshold: float,
        condition: str,
        ingredient: Optional[str] = None,
        ingredient_code: Optional[str] = None,
        formula: Optional[str] = None,
        formula_id: Optional[str] = None,
    ):
        return self._svc.create_reminder(
            user_id=user_id,
            reminder_type=reminder_type,
            threshold=threshold,
            condition=condition,
            ingredient=ingredient,
            ingredient_code=ingredient_code,
            formula=formula,
            formula_id=formula_id,
        )

    def list_reminders(self, user_id: str):
        return self._svc.list_reminders(user_id, enabled_only=False)

    def delete_reminder(self, user_id: str, reminder_id: str):
        list_result = self._svc.list_reminders(user_id, enabled_only=False)
        if not list_result.success:
            return list_result

        for reminder in list_result.data.get("reminders", []):
            full_id = str(reminder.get("id", ""))
            if full_id.startswith(reminder_id):
                return self._svc.delete_reminder(full_id, user_id)

        return ServiceResult(success=False, error_message=f"Reminder '{reminder_id}' not found")


_INGREDIENT_MAP = {
    "corn": {"name": "Corn, No.2 Yellow", "code": "ING_CORN"},
    "soybean": {"name": "Soybean meal, 48%", "code": "ING_SBM"},
    "soybean meal": {"name": "Soybean meal, 48%", "code": "ING_SBM"},
    "sbm": {"name": "Soybean meal, 48%", "code": "ING_SBM"},
    "wheat": {"name": "Wheat, grain", "code": "ING_WHEAT"},
    "barley": {"name": "Barley", "code": "ING_BARLEY"},
    "fish meal": {"name": "Fish meal, 65%", "code": "ING_FISHM"},
    "ddgs": {"name": "DDGS, 28%", "code": "ING_DDGS"},
    "limestone": {"name": "Limestone", "code": "ING_LIME"},
    "lysine": {"name": "L-Lysine HCl", "code": "ING_LYS"},
    "methionine": {"name": "DL-Methionine", "code": "ING_MET"},
}

_FORMULA_MAP = {
    "nursery": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
    "nursery diet": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
    "grower": {"name": "Grower Diet 1", "id": "FORMULA_GROWER_1"},
    "finishing": {"name": "Finishing Diet", "id": "FORMULA_FINISHING"},
    "broiler": {"name": "Broiler Starter", "id": "FORMULA_BROILER_STARTER"},
    "layer": {"name": "Layer Diet", "id": "FORMULA_LAYER"},
}


class ReminderSkill:
    def __init__(self, service: SkillReminderService):
        self.service = service

    async def execute(self, user_id: str, message: str) -> dict:
        msg_lower = message.lower()

        if "list" in msg_lower or "show" in msg_lower or "my reminder" in msg_lower or "reminders" in msg_lower:
            result = self.service.list_reminders(user_id)
            if result.success:
                reminders = result.data["reminders"]
                if not reminders:
                    return {
                        "success": True,
                        "message": "You have no reminders set. Create one:\n- Alert when corn > $90/ton\n- Remind me when soybean meal < $350/ton",
                    }
                lines = ["| ID | Type | Target | Condition |", "|----|------|--------|-----------|"]
                for r in reminders:
                    target = r.get("ingredient") or r.get("formula", "Unknown")
                    cond = "above" if r.get("condition") == "above" else "below"
                    lines.append(f"| {str(r.get('id', ''))[:8]} | {r.get('type')} | {target} | {cond} ${r.get('threshold')} |")
                return {"success": True, "message": "\n".join(lines)}
            return {"success": False, "error": result.error_message}

        if "delete" in msg_lower or "remove" in msg_lower or "cancel" in msg_lower:
            id_match = re.search(r"[a-f0-9]{8}", msg_lower)
            if id_match:
                reminder_id = id_match.group()
                result = self.service.delete_reminder(user_id, reminder_id)
                if result.success:
                    return {"success": True, "message": f"Reminder {reminder_id} deleted."}
                return {"success": False, "error": result.error_message}
            return {
                "success": False,
                "error": 'Please provide a reminder ID to delete. Example: "delete reminder 245f1bd9"',
            }

        price_pattern = r"(?:alert|remind|notify).*?(?:when|if)\s+(\w+(?:\s+\w+)?)\s+(?:exceeds?|goes?|falls?|drops?|above|below|>|<)\s*\$?(\d+(?:\.\d+)?)"
        match = re.search(price_pattern, msg_lower)

        if match:
            ingredient_name = match.group(1).strip()
            threshold = float(match.group(2))

            condition = "above"
            if any(w in msg_lower for w in ["below", "under", "<", "falls", "drops", "less"]):
                condition = "below"

            ingredient_info = _INGREDIENT_MAP.get(ingredient_name.lower())
            if ingredient_info:
                result = self.service.create_reminder(
                    user_id=user_id,
                    reminder_type="price",
                    threshold=threshold,
                    condition=condition,
                    ingredient=ingredient_info["name"],
                    ingredient_code=ingredient_info["code"],
                )
                if result.success:
                    cond_text = "exceeds" if condition == "above" else "falls below"
                    return {
                        "success": True,
                        "message": f"Price alert created!\n\n| Ingredient | Condition | Alert ID |\n|------------|-----------|----------|\n| {ingredient_info['name']} | {cond_text} ${threshold}/ton | {result.data['id']} |",
                    }
                return {"success": False, "error": result.error_message}

            formula_info = _FORMULA_MAP.get(ingredient_name.lower())
            if formula_info:
                result = self.service.create_reminder(
                    user_id=user_id,
                    reminder_type="formula_cost",
                    threshold=threshold,
                    condition=condition,
                    formula=formula_info["name"],
                    formula_id=formula_info["id"],
                )
                if result.success:
                    cond_text = "exceeds" if condition == "above" else "falls below"
                    return {
                        "success": True,
                        "message": f"Formula cost alert created!\n\n| Formula | Condition | Alert ID |\n|---------|-----------|----------|\n| {formula_info['name']} | {cond_text} ${threshold}/ton | {result.data['id']} |",
                    }
                return {"success": False, "error": result.error_message}

            return {
                "success": False,
                "error": f"Unknown ingredient or formula: '{ingredient_name}'. Supported: corn, soybean meal, wheat, barley, fish meal, DDGS, nursery diet, grower diet, finishing diet.",
            }

        return {
            "success": False,
            "error": 'Could not parse reminder request. Try: "Alert when corn > $100/ton" or "show my reminders"',
        }


def get_reminder_skill():
    return ReminderSkill(SkillReminderService())


def _load_module(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module '{module_name}' from '{file_path}'")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ============== Subscription & Referral Services ==============
# (Migrated from src/services/subscription_service.py and src/services/referral_service.py)

import hashlib
from datetime import datetime, timedelta


class SimpleSubscriptionService:
    """Simplified subscription service for Hermes skill execution."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_subscription_status(self, user_id: str) -> dict:
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
        )
        subscription = cursor.fetchone()

        if subscription is None:
            cursor.execute(
                "INSERT INTO subscriptions (user_id, plan_id, is_in_trial, referral_bonus_days) VALUES (?, 1, 0, 0)",
                (user_id,)
            )
            conn.commit()
            cursor.execute(
                "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
            )
            subscription = cursor.fetchone()

        cursor.execute(
            "SELECT * FROM subscription_plans WHERE id = ?",
            (subscription['plan_id'],)
        )
        plan = cursor.fetchone()

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
            'referral_bonus_days': subscription['referral_bonus_days'] or 0,
            'pro_bonus_months': subscription['pro_bonus_months'] or 0,
        }

    def check_query_limit(self, user_id: str) -> dict:
        status = self.get_subscription_status(user_id)
        queries_per_day = status['queries_per_day']

        if queries_per_day == -1:
            return {'allowed': True, 'queries_remaining': -1}

        today = datetime.now().date().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT query_count FROM daily_usage WHERE user_id = ? AND usage_date = ?",
            (user_id, today)
        )
        result = cursor.fetchone()
        used = result['query_count'] if result else 0
        conn.close()

        remaining = queries_per_day - used

        if remaining > 0:
            return {'allowed': True, 'queries_remaining': remaining}
        else:
            return {
                'allowed': False,
                'queries_remaining': 0,
                'message': f"Daily limit reached ({queries_per_day} queries/day). Upgrade for more."
            }

    def record_usage(self, user_id: str) -> None:
        self.get_subscription_status(user_id)

        today = datetime.now().date().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO daily_usage (user_id, usage_date, query_count) VALUES (?, ?, 1) ON CONFLICT(user_id, usage_date) DO UPDATE SET query_count = query_count + 1, updated_at = CURRENT_TIMESTAMP",
            (user_id, today)
        )
        conn.commit()
        conn.close()

    def get_daily_usage(self, user_id: str) -> int:
        today = datetime.now().date().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT query_count FROM daily_usage WHERE user_id = ? AND usage_date = ?",
            (user_id, today)
        )
        result = cursor.fetchone()
        conn.close()
        return result['query_count'] if result else 0


class SimpleReferralService:
    """Simplified referral service for Hermes skill execution."""

    BONUS_DAYS_PER_REFERRAL = 7
    REFERRALS_FOR_PRO_BONUS = 3

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._sub_service = SimpleSubscriptionService(db_path)
        self._referral_code_cache = {}

    def _get_conn(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # Telegram bot username for deep-link referrals
    BOT_USERNAME = os.getenv("FEEDPILOT_BOT_USERNAME", "feedpilot_bot")

    def get_referral_link(self, user_id: str) -> str:
        self._sub_service.get_subscription_status(user_id)
        hash_obj = hashlib.md5(user_id.encode())
        referral_code = hash_obj.hexdigest()[:8]
        full_code = f"ref_{referral_code}"
        self._referral_code_cache[full_code] = user_id
        return f"https://t.me/{self.BOT_USERNAME}?start={full_code}"

    def get_referral_stats(self, user_id: str) -> dict:
        self._sub_service.get_subscription_status(user_id)
        referral_link = self.get_referral_link(user_id)

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        referral_count = result["count"] if result else 0

        cursor.execute(
            "SELECT referral_bonus_days, pro_bonus_months, plan_id FROM subscriptions WHERE user_id = ?",
            (user_id,)
        )
        sub = cursor.fetchone()
        total_bonus_days = sub["referral_bonus_days"] if sub and sub["referral_bonus_days"] else 0
        pro_bonus_months = sub["pro_bonus_months"] if sub and sub["pro_bonus_months"] else 0

        is_permanent_pro = bool(pro_bonus_months > 0)
        plan_name = "free"
        if sub:
            cursor.execute(
                "SELECT name FROM subscription_plans WHERE id = ?",
                (sub["plan_id"],)
            )
            plan = cursor.fetchone()
            if plan:
                plan_name = plan["name"]

        conn.close()

        return {
            "referral_count": referral_count,
            "total_bonus_days": total_bonus_days,
            "pro_bonus_months": pro_bonus_months,
            "referral_link": referral_link,
            "is_permanent_pro": is_permanent_pro,
            "plan_name": plan_name,
        }

    def process_referral(self, referrer_id: str, referee_id: str, bonus_days: int = 7) -> dict:
        if referrer_id == referee_id:
            return {"success": False, "message": "You cannot refer yourself."}

        self._sub_service.get_subscription_status(referrer_id)
        self._sub_service.get_subscription_status(referee_id)

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM referrals WHERE referee_id = ?",
            (referee_id,)
        )
        if cursor.fetchone():
            conn.close()
            return {"success": False, "message": "User has already been referred."}

        cursor.execute(
            "SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ?",
            (referrer_id,)
        )
        current_count = cursor.fetchone()["count"]

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

        new_count = current_count + 1
        pro_bonus_awarded = False

        if new_count >= self.REFERRALS_FOR_PRO_BONUS:
            cursor.execute(
                "UPDATE subscriptions SET pro_bonus_months = COALESCE(pro_bonus_months, 0) + 1, plan_id = 3, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (referrer_id,)
            )
            pro_bonus_awarded = True

        conn.commit()
        conn.close()

        message = f"Bonus applied! Both users received {self.BONUS_DAYS_PER_REFERRAL} bonus days!"
        if pro_bonus_awarded:
            message += f" Plus 1 month Pro for the referrer (now at {new_count} referrals)!"

        return {
            "success": True,
            "bonus_days": self.BONUS_DAYS_PER_REFERRAL,
            "pro_bonus_awarded": pro_bonus_awarded,
            "message": message,
            "referral_count": new_count
        }

    def _decode_referral_code(self, referral_code: str) -> str:
        if not referral_code or not referral_code.startswith("ref_"):
            return None

        if referral_code in self._referral_code_cache:
            return self._referral_code_cache[referral_code]

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM subscriptions")
        users = cursor.fetchall()
        conn.close()

        for user in users:
            user_id = user["user_id"]
            hash_obj = hashlib.md5(user_id.encode())
            code = f"ref_{hash_obj.hexdigest()[:8]}"
            if code == referral_code:
                self._referral_code_cache[referral_code] = user_id
                return user_id

        return None


# ============== Subscription Skill ==============
class SubscriptionSkill:
    """Check subscription status."""

    def __init__(self):
        self._sub_service = SimpleSubscriptionService(DB_PATH)

    async def execute(self, user_id: str, message: str) -> dict:
        # Show subscription status
        status = self._sub_service.get_subscription_status(user_id)
        lines = [
            f"<b>Plan:</b> {html.escape(str(status['plan_display_name']))}",
            f"<b>Queries per day:</b> {'Unlimited' if status['queries_per_day'] == -1 else status['queries_per_day']}",
        ]

        if status['referral_bonus_days'] > 0:
            lines.append(f"<b>Referral bonus:</b> {status['referral_bonus_days']} days")

        if status['pro_bonus_months'] > 0:
            lines.append(f"<b>Pro bonus:</b> {status['pro_bonus_months']} months")

        remaining = self._sub_service.check_query_limit(user_id)
        if remaining['allowed']:
            if remaining['queries_remaining'] > 0:
                lines.append(f"<b>Queries remaining today:</b> {remaining['queries_remaining']}")
        else:
            lines.append("<b>Daily limit reached.</b> Upgrade to Pro for unlimited.")

        return {
            'success': True,
            'data': {'_html': '\n'.join(lines)}
        }


# ============== Referral Skill ==============
class ReferralSkill:
    """Handle referral: show link, stats, process codes."""

    def __init__(self):
        self._referral_service = SimpleReferralService(DB_PATH)
        self._sub_service = SimpleSubscriptionService(DB_PATH)

    async def execute(self, user_id: str, message: str) -> dict:
        msg_lower = message.lower().strip()

        if msg_lower in ['link', '/referral', 'my link', 'stats', 'my stats', 'referral stats']:
            stats = self._referral_service.get_referral_stats(user_id)
            referral_link = html.escape(self._referral_service.get_referral_link(user_id))
            lines = [
                f"<b>Your referral link:</b> {referral_link}",
                f"<b>Referrals:</b> {stats['referral_count']}",
                f"<b>Bonus days earned:</b> {stats['total_bonus_days']}",
            ]
            if stats['pro_bonus_months'] > 0:
                lines.append(f"<b>Pro bonus:</b> {stats['pro_bonus_months']} months")
                lines.append("You have permanent Pro access!")
            elif stats['referral_count'] >= 3:
                lines.append("Each new referral = 1 month Pro for you!")
            else:
                needed = max(0, 3 - stats['referral_count'])
                lines.append(f"{needed} more referral(s) for 1 month Pro!")

            return {
                'success': True,
                'data': {'_html': '\n'.join(lines)}
            }

        # Process a referral code (e.g., "ref_abc12345")
        if msg_lower.startswith('ref_'):
            referrer_id = self._referral_service._decode_referral_code(msg_lower)
            if referrer_id is None:
                return {'success': False, 'error': 'Invalid referral code.'}
            if referrer_id == user_id:
                return {'success': False, 'error': 'You cannot use your own referral code.'}

            result = self._referral_service.process_referral(referrer_id, user_id)
            if result['success']:
                return {
                    'success': True,
                    'data': {
                        '_html': f"<b>Referral bonus applied!</b>\n\n{html.escape(result['message'])}"
                    }
                }
            return {'success': False, 'error': result.get('message', 'Failed to process referral')}

        # Default: show referral info
        referral_link = html.escape(self._referral_service.get_referral_link(user_id))
        return {
            'success': True,
            'data': {
                '_html': f"<b>Your referral link:</b>\n{referral_link}\n\nShare it with friends \u2014 both of you get 7 bonus days!\n3+ referrals = 1 month Pro per referral!"
            }
        }


# ============== Onboarding Skill ==============
class OnboardingSkill:
    """
    Two-track onboarding funnel:
      - Step 0: Plan selection (Basic vs Pro trial)
      - Step 1: Guided first action (track-specific)
      - Step 2: Feature demo completion + referral
      - Upsell triggers: limit hit, basic-user accessing Pro features
    """

    BASIC_PLAN_ID = 1
    PRO_PLAN_ID = 2
    UPSELL_THRESHOLD = 3  # queries before prompting Pro upgrade

    # Step constants
    STEP_WELCOME = 0      # Show welcome + plan selection
    STEP_PLAN_SELECT = 1  # Await A or P choice
    STEP_GUIDED_ACTION = 2 # User is trying features
    STEP_DEMO_COMPLETE = 3

    def __init__(self):
        self._sub_service = SimpleSubscriptionService(DB_PATH)
        self._referral_service = SimpleReferralService(DB_PATH)

    def _get_conn(self):
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_onboarding_state(self, user_id: str) -> dict:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Migration: add new columns if schema is from old version
        cursor.execute("PRAGMA table_info(user_onboarding)")
        columns = {row[1] for row in cursor.fetchall()}
        if "chosen_track" not in columns:
            cursor.execute("ALTER TABLE user_onboarding ADD COLUMN chosen_track TEXT DEFAULT NULL")
        if "queries_in_session" not in columns:
            cursor.execute("ALTER TABLE user_onboarding ADD COLUMN queries_in_session INTEGER DEFAULT 0")
        if "completed_at" not in columns:
            cursor.execute("ALTER TABLE user_onboarding ADD COLUMN completed_at TEXT DEFAULT NULL")
        conn.commit()

        cursor.execute(
            "SELECT user_id, onboarding_step, chosen_track, queries_in_session, "
            "onboarding_started_at, completed_at FROM user_onboarding WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "user_id": row[0],
                "step": row[1],
                "track": row[2],
                "queries_in_session": row[3] or 0,
                "started_at": row[4],
                "completed_at": row[5]
            }
        return {"step": self.STEP_WELCOME, "track": None, "queries_in_session": 0}

    def _update_onboarding_state(self, user_id: str, step: int, track: str = None, queries: int = None):
        from datetime import datetime
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        if step == self.STEP_WELCOME:
            # Just set step=1 to advance from welcome to plan select
            cursor.execute('''
                INSERT INTO user_onboarding (user_id, onboarding_step, onboarding_started_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    onboarding_step = excluded.onboarding_step,
                    onboarding_started_at = COALESCE(user_onboarding.onboarding_started_at, excluded.onboarding_started_at)
            ''', (user_id, step, now))
        elif track is not None:
            cursor.execute('''
                INSERT INTO user_onboarding (user_id, onboarding_step, chosen_track, queries_in_session, onboarding_started_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    onboarding_step = excluded.onboarding_step,
                    chosen_track = excluded.chosen_track,
                    queries_in_session = COALESCE(excluded.queries_in_session, queries_in_session),
                    onboarding_started_at = COALESCE(user_onboarding.onboarding_started_at, excluded.onboarding_started_at)
            ''', (user_id, step, track, queries or 0, now))
        else:
            cursor.execute('''
                INSERT INTO user_onboarding (user_id, onboarding_step, completed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    onboarding_step = excluded.onboarding_step,
                    completed_at = CASE WHEN excluded.onboarding_step = 3 THEN ? ELSE user_onboarding.completed_at END
            ''', (user_id, step, now if step == self.STEP_DEMO_COMPLETE else now, now if step == self.STEP_DEMO_COMPLETE else now))

        conn.commit()
        conn.close()

    def _increment_queries(self, user_id: str) -> int:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_onboarding (user_id, queries_in_session)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                queries_in_session = (user_onboarding.queries_in_session + 1)
        ''', (user_id,))
        conn.commit()
        cursor.execute('SELECT queries_in_session FROM user_onboarding WHERE user_id = ?', (user_id,))
        q = cursor.fetchone()
        conn.close()
        return q[0] if q else 0

    def _get_referral_link(self, user_id: str) -> str:
        return self._referral_service.get_referral_link(user_id)

    def _build_upgrade_cta(self, user_id: str) -> str:
        """Build upgrade CTA with user's referral link."""
        referral_link = html.escape(self._get_referral_link(user_id))
        return f"""
━━━━━━━━━━━━━━━━━━━━━━━
🚀 <b>Upgrade Your Plan</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>Starter — $9.99/month (700 ⭐)</b>
• 100 queries/day
• All Basic features
• More formulas access

👉 <a href="https://t.me/feedpilot_payment_bot?start=starter_monthly">Pay with Stars (700 ⭐)</a>
👉 <a href="https://feedpilot.gumroad.com/l/ktkuo">Pay with Gumroad</a>

━━━━━━━━━━━━━━━━━━━━━━━

<b>Pro — $29.99/month (2,100 ⭐)</b>
• Unlimited queries
• All feed formulas (Nursery, Breeder, Broiler, Layer...)
• Customer CRM
• AI nutrition analysis
• Priority support

👉 <a href="https://t.me/feedpilot_payment_bot?start=pro_monthly">Pay with Stars (2,100 ⭐)</a>
👉 <a href="https://feedpilot.gumroad.com/l/ktkuo">Pay with Gumroad</a>

━━━━━━━━━━━━━━━━━━━━━━━
Share to extend your access:
🔗 {referral_link}

Each friend who joins = +7 days Pro!
3+ referrals = each gets 1 month Pro."""

    async def execute(self, user_id: str, message: str) -> dict:
        message_lower = message.lower().strip()
        state = self._get_onboarding_state(user_id)
        sub = self._sub_service.get_subscription_status(user_id)

        # === STEP 0: Welcome — show plan selection to new/free users ===
        if state["step"] == self.STEP_WELCOME:
            plan_name = sub.get("plan_name", "free")

            if plan_name == "pro":
                return {
                    "success": True,
                    "data": {
                        "_html": """🦅 <b>You're a Pro user!</b>

Welcome back. Here's your quick-start menu:

1️⃣ <b>Price Check</b> — corn, soybean meal, wheat...
2️⃣ <b>Formula Cost</b> — nursery, grower, finisher, broiler, layer...
3️⃣ <b>Customer CRM</b> — add, search, manage customers
4️⃣ <b>Nutrition Analysis</b> — compare vs NRC standards
5️⃣ <b>Referral Stats</b> — see your referral count & bonus days

What would you like to try?"""
                    }
                }

            # New user or free user — show plan selection, advance to STEP_PLAN_SELECT
            self._update_onboarding_state(user_id, self.STEP_PLAN_SELECT)
            return {
                "success": True,
                "data": {
                    "_html": """🐔 <b>Welcome to FeedPilot AI!</b>
Your pocket feed formulation assistant.

━━━━━━━━━━━━━━━━━━━━━━━
<b>Choose your plan:</b>
━━━━━━━━━━━━━━━━━━━━━━━

<b>Type A</b> — Basic (FREE)
• 10 price queries/day
• Price lookup (corn, soybean meal, wheat...)
• Basic formula cost calculation
• Good for trying things out

<b>Type S</b> — Starter ($9.99/month)
• 100 queries/day
• All Basic features
• More formulas access
• 💳 Pay with Telegram Stars or Gumroad

<b>Type P</b> — Pro ($29.99/month)
• Everything in Basic, PLUS:
• ✦ Unlimited queries
• ✦ All feed formulas (Nursery, Breeder, Broiler, Layer, Finisher...)
• ✦ Customer CRM management
• ✦ AI nutrition analysis vs NRC standards
• ✦ Price trend alerts
• 💳 Pay with Telegram Stars or Gumroad (credit card/PayPal)

━━━━━━━━━━━━━━━━━━━━━━━
<b>Type A, S, or P to get started →</b>
━━━━━━━━━━━━━━━━━━━━━━━
"""
                }
            }

        # === STEP 1: User chose a track ===
        elif state["step"] == self.STEP_PLAN_SELECT:
            chosen = None
            if message_lower in ["a", "basic", "free", "1"]:
                chosen = "basic"
                self._update_onboarding_state(user_id, self.STEP_GUIDED_ACTION, track="basic")
                return {
                    "success": True,
                    "data": {
                        "_html": """✅ <b>Basic plan activated</b> (10 queries/day)

Let's start with a quick demo — try checking an ingredient price:

<b>Type an ingredient name</b> (e.g. corn, soybean meal, wheat, fish meal)
or type <b>'all'</b> to see all prices."""
                    }
                }

            elif message_lower in ["s", "starter", "3"]:
                chosen = "starter"
                self._update_onboarding_state(user_id, self.STEP_GUIDED_ACTION, track="starter")
                return {
                    "success": True,
                    "data": {
                        "_html": """✅ <b>Starter plan selected!</b>

<b>💳 Choose your payment method:</b>

1️⃣ <b>Telegram Stars</b> — pay inside Telegram
👉 <a href="https://t.me/feedpilot_payment_bot?start=starter_monthly">Pay with Stars (700 ⭐)</a>

2️⃣ <b>Gumroad</b> — credit card / PayPal
👉 <a href="https://feedpilot.gumroad.com/l/ktkuo">Pay with Gumroad</a>

You now have:
✓ 100 queries/day
✓ Basic formulas + price lookup
✓ More access than Basic

<b>Let's start with your first feature — try checking an ingredient price:</b>

<b>Type an ingredient name</b> (e.g. corn, soybean meal, wheat, fish meal)
or type <b>'all'</b> to see all prices."""
                    }
                }

            elif message_lower in ["p", "pro", "2"]:
                chosen = "pro"
                self._update_onboarding_state(user_id, self.STEP_GUIDED_ACTION, track="pro")
                return {
                    "success": True,
                    "data": {
                        "_html": """✅ <b>Pro plan selected!</b>

<b>💳 Choose your payment method:</b>

1️⃣ <b>Telegram Stars</b> — pay inside Telegram
👉 <a href="https://t.me/feedpilot_payment_bot?start=pro_monthly">Pay with Stars (2,100 ⭐)</a>

2️⃣ <b>Gumroad</b> — credit card / PayPal
👉 <a href="https://feedpilot.gumroad.com/l/ktkuo">Pay with Gumroad</a>

You now have full access to:
✓ Unlimited queries
✓ All feed formulas
✓ Customer CRM
✓ AI nutrition analysis

<b>Let's start with your first feature — try calculating a formula cost:</b>

Type your formula, for example:
`corn 60%, soybean meal 25%, premix 5%, limestone 10%`

Or type <b>'example'</b> to see a sample nursery diet calculation with full cost breakdown."""
                    }
                }

            elif message_lower in ["upgrade", "up", "subscribe", "buy"]:
                # Free user requesting upgrade — show both plans
                self._update_onboarding_state(user_id, self.STEP_GUIDED_ACTION, track="pro")
                return {
                    "success": True,
                    "data": {
                        "_html": """✅ <b>Upgrade your plan!</b>

<b>Starter — $9.99/month (700 ⭐)</b>
• 100 queries/day
• All Basic features

👉 <a href="https://t.me/feedpilot_payment_bot?start=starter_monthly">Pay with Stars (700 ⭐)</a>
👉 <a href="https://feedpilot.gumroad.com/l/ktkuo">Pay with Gumroad</a>

━━━━━━━━━━━━━━━━━━━━━━━

<b>Pro — $29.99/month (2,100 ⭐)</b>
• Unlimited queries
• All feed formulas
• Customer CRM
• AI nutrition analysis

👉 <a href="https://t.me/feedpilot_payment_bot?start=pro_monthly">Pay with Stars (2,100 ⭐)</a>
👉 <a href="https://feedpilot.gumroad.com/l/ktkuo">Pay with Gumroad</a>

━━━━━━━━━━━━━━━━━━━━━━━
Let's calculate your first formula. Type your ingredients:
`corn 60%, soybean meal 25%, premix 5%`

Or type <b>'example'</b> for a full nursery diet cost breakdown."""
                    }
                }

            else:
                return {
                    "success": True,
                    "data": {
                        "_html": "Please type <b>A</b> for Basic (free), <b>S</b> for Starter, or <b>P</b> for Pro to continue."
                    }
                }

        # === STEP 2: Guided first action ===
        if state["step"] == self.STEP_GUIDED_ACTION:
            track = state.get("track", "basic")

            # Increment query count
            q_count = self._increment_queries(user_id)

            # Basic user hitting upsell threshold → trigger upgrade CTA
            if track == "basic" and q_count >= self.UPSELL_THRESHOLD:
                return {
                    "success": True,
                    "data": {
                        "_html": f"""🔔 <b>You've used {html.escape(str(q_count))} queries on Basic</b>

You've seen the basics — ready to unlock full access?

{self._build_upgrade_cta(user_id)}

<b>Just type P or 'upgrade' to unlock Pro features →</b>"""
                    }
                }

            # Continue guided action based on track
            if track == "basic":
                return {
                    "success": True,
                    "data": {
                        "_html": f"""📊 <b>Basic plan: {html.escape(str(10 - q_count))} queries left today</b>

Try checking prices or calculating a simple formula cost.

<b>Quick examples:</b>
• "corn price" — check corn
• "soybean meal price" — check SBM
• "example formula" — see a sample calculation

<b>Type 'upgrade'</b> anytime to unlock Pro features!"""
                    }
                }
            else:  # pro track
                return {
                    "success": True,
                    "data": {
                        "_html": """🧮 <b>Pro features — unlimited queries!</b>

Try one of these Pro features:

<b>Formula Cost</b> — type your formula:
`corn 60%, soybean meal 25%, premix 5%, limestone 10%`

<b>Customer CRM</b> — type:
`add customer John Farm, phone 555-1234`

<b>Nutrition Analysis</b> — type:
`analyze Nursery Diet 1 vs NRC standards`

Or type <b>'example'</b> for a full nursery diet breakdown with cost + nutrition data."""
                    }
                }

        # === STEP 3: Demo complete — show referral + Pro upsell ===
        if state["step"] == self.STEP_DEMO_COMPLETE:
            referral_link = html.escape(self._get_referral_link(user_id))
            return {
                "success": True,
                "data": {
                    "_html": f"""🎉 <b>You've completed the demo!</b>

Your quick-start menu:
• <b>corn price</b> — check any ingredient
• <b>formula cost</b> — calculate feed cost
• <b>add customer</b> — CRM management
• <b>subscription</b> — check your plan & usage
• <b>referral</b> — share for bonus days

{self._build_upgrade_cta(user_id)}

Keep going with any command, or type <b>'upgrade'</b> to start your Pro trial!"""
                }
            }

        # Fallback
        return {
            "success": True,
            "data": {
                "_html": """Type <b>'onboard'</b> to restart the guided tour, or type any command to continue."""
            }
        }


# ============== Skill Factories ==============
def get_price_lookup_skill():
    """初始化 PriceLookupSkill"""
    # 直接导入脚本文件
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "query_price", 
        os.path.join(WORKSPACE, 'skills/price_lookup_skill/scripts/query_price.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_price_lookup_skill():
    module = _load_module(
        "query_price",
        os.path.join(WORKSPACE, "skills/price_lookup_skill/scripts/query_price.py"),
    )
    return module.create_skill(SkillPriceService())


def get_formula_cost_skill():
    module = _load_module(
        "formula_cost",
        os.path.join(WORKSPACE, "skills/formula_cost_skill/skill.py"),
    )
    return module.FormulaCostSkill(SkillCalculationService())


def get_nutrition_skill():
    module = _load_module(
        "nutrition",
        os.path.join(WORKSPACE, "skills/nutrition_analysis_skill/skill.py"),
    )
    return module.NutritionAnalysisSkill(SkillFormulaService())


def get_customer_skill():
    module = _load_module(
        "customer",
        os.path.join(WORKSPACE, "skills/customer_record_skill/skill.py"),
    )
    return module.CustomerRecordSkill(SkillCustomerService())


def get_subscription_skill():
    module = _load_module(
        "subscription",
        os.path.join(WORKSPACE, "skills/subscription_skill/skill.py"),
    )
    sub_service = SimpleSubscriptionService(DB_PATH)
    referral_service = SimpleReferralService(DB_PATH)
    return module.SubscriptionSkill(sub_service, referral_service)


SKILL_MAP = {
    'price_lookup': get_price_lookup_skill,
    'price': get_price_lookup_skill,
    'formula_cost': get_formula_cost_skill,
    'cost': get_formula_cost_skill,
    'nutrition': get_nutrition_skill,
    'analyze': get_nutrition_skill,
    'customer': get_customer_skill,
    'customers': get_customer_skill,
    'reminder': get_reminder_skill,
    'reminders': get_reminder_skill,
    'alert': get_reminder_skill,
    'subscription': get_subscription_skill,
    'onboarding': OnboardingSkill,
    '/onboard': OnboardingSkill,
    'onboard': OnboardingSkill,
    'getstarted': OnboardingSkill,
    'start': OnboardingSkill,
    'upgrade': OnboardingSkill,
    'referral': ReferralSkill,
    '/referral': ReferralSkill,
    'my referral': ReferralSkill,
    'referral link': ReferralSkill,
    'my link': ReferralSkill,
}


async def run_skill(skill_name: str, user_message: str, user_id: str = "cli_user"):
    # LLM trust-boundary guard: validate input before any skill execution
    validation_error = _validate_user_message(user_message)
    if validation_error:
        return {"success": False, "error": validation_error}

    skill_factory = SKILL_MAP.get(skill_name)
    if not skill_factory:
        return {"success": False, "error": f"Unknown skill: {skill_name}. Available: {list(SKILL_MAP.keys())}"}

    skill = skill_factory()
    result = await skill.execute(user_id, user_message)
    return result


def main():
    if len(sys.argv) < 3:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": 'Usage: run_skill.py <skill_name> "<user_message>"',
                    "available_skills": list(SKILL_MAP.keys()),
                },
                indent=2,
            )
        )
        sys.exit(1)

    skill_name = sys.argv[1]
    user_message = sys.argv[2]

    result = asyncio.run(run_skill(skill_name, user_message))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
