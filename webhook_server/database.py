"""Database operations for webhook server."""
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

from .config import DB_PATH, PLAN_IDS, SUBSCRIPTION_DAYS

logger = logging.getLogger("webhook.db")


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def migrate():
    """Add new columns and tables for payment webhook support."""
    with get_db() as conn:
        # Check if columns already exist
        cursor = conn.execute("PRAGMA table_info(subscriptions)")
        existing_cols = {row["name"] for row in cursor.fetchall()}

        new_columns = {
            "payment_method": "TEXT DEFAULT 'free'",
            "payment_id": "TEXT",
            "subscription_expires_at": "TEXT",
            "gumroad_email": "TEXT",
        }

        for col, definition in new_columns.items():
            if col not in existing_cols:
                conn.execute(f"ALTER TABLE subscriptions ADD COLUMN {col} {definition}")
                logger.info(f"Added column: subscriptions.{col}")

        # Create payment_logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payment_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                payment_id TEXT NOT NULL UNIQUE,
                plan_id INTEGER NOT NULL,
                amount REAL,
                currency TEXT DEFAULT 'USD',
                status TEXT DEFAULT 'pending',
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
            )
        """)
        logger.info("payment_logs table ready")


def log_payment(user_id: str, payment_method: str, payment_id: str,
                plan_id: int, amount: float, currency: str,
                status: str, raw_data: dict):
    """Record a payment transaction."""
    with get_db() as conn:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO payment_logs
                (user_id, payment_method, payment_id, plan_id, amount, currency, status, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, payment_method, payment_id, plan_id, amount, currency,
                  status, json.dumps(raw_data)))
        except sqlite3.IntegrityError:
            logger.warning(f"Duplicate payment_id ignored: {payment_id}")


def activate_subscription(user_id: str, plan_key: str, payment_id: str,
                          payment_method: str, amount: float, currency: str,
                          raw_data: dict):
    """Activate or renew a user's subscription."""
    plan_id = PLAN_IDS.get(plan_key, 1)
    now = datetime.utcnow()

    # Determine duration
    if plan_key == "starter":
        days = SUBSCRIPTION_DAYS["starter_monthly"]
    elif plan_key == "pro":
        days = SUBSCRIPTION_DAYS["pro_monthly"]
    else:
        days = 30  # fallback

    expires_at = (now + timedelta(days=days)).isoformat()

    with get_db() as conn:
        # Upsert subscription
        existing = conn.execute(
            "SELECT id, subscription_expires_at FROM subscriptions WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        if existing:
            # Extend from current expiry if still active
            if existing["subscription_expires_at"]:
                try:
                    current_expiry = datetime.fromisoformat(existing["subscription_expires_at"])
                    if current_expiry > now:
                        expires_at = (current_expiry + timedelta(days=days)).isoformat()
                except ValueError:
                    pass

            conn.execute("""
                UPDATE subscriptions
                SET plan_id = ?,
                    payment_method = ?,
                    payment_id = ?,
                    subscription_expires_at = ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (plan_id, payment_method, payment_id, expires_at,
                  now.isoformat(), user_id))
        else:
            conn.execute("""
                INSERT INTO subscriptions
                (user_id, plan_id, payment_method, payment_id, subscription_expires_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, plan_id, payment_method, payment_id, expires_at,
                  now.isoformat(), now.isoformat()))

    # Log the payment
    log_payment(user_id, payment_method, payment_id, plan_id, amount, currency, "completed", raw_data)
    logger.info(f"Activated {plan_key} for {user_id}, expires {expires_at}")
    return expires_at


def refund_subscription(user_id: str, payment_id: str, raw_data: dict):
    """Handle a refund — downgrade to free."""
    with get_db() as conn:
        conn.execute("""
            UPDATE subscriptions
            SET plan_id = 1,
                payment_method = 'free',
                payment_id = NULL,
                subscription_expires_at = NULL,
                updated_at = ?
            WHERE user_id = ?
        """, (datetime.utcnow().isoformat(), user_id))

        # Update payment log status
        conn.execute("""
            UPDATE payment_logs SET status = 'refunded'
            WHERE payment_id = ?
        """, (payment_id,))

    logger.info(f"Refunded {user_id}, payment {payment_id}")


def find_user_by_gumroad_email(email: str):
    """Find user_id by Gumroad email."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT user_id FROM subscriptions WHERE gumroad_email = ?",
            (email,)
        ).fetchone()
        return row["user_id"] if row else None


def set_gumroad_email(user_id: str, email: str):
    """Link Gumroad email to user."""
    with get_db() as conn:
        conn.execute(
            "UPDATE subscriptions SET gumroad_email = ? WHERE user_id = ?",
            (email, user_id)
        )
