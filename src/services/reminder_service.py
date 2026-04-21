"""
FeedSales AI - ReminderService

Reminder service supporting price and formula-cost reminders.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from ..database.pool import DatabasePool
from ..result_types import ServiceResult

logger = logging.getLogger(__name__)


class ReminderService:
    """Reminder service."""

    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self._init_table()

    def _get_table_columns(self, conn, table_name: str):
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return [row[1] for row in rows]

    def _migrate_legacy_reminders_if_needed(self, conn) -> None:
        """
        Migrate legacy schema:
        reminders(id INTEGER, owner_open_id, reminder_type, reminder_date, message, status, created_at)
        to the current reminder schema used by this service.
        """
        table_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='reminders'"
        ).fetchone()
        if not table_exists:
            return

        columns = self._get_table_columns(conn, "reminders")
        if "user_id" in columns and "type" in columns:
            return

        conn.execute("ALTER TABLE reminders RENAME TO reminders_legacy")

        conn.execute(
            """
            CREATE TABLE reminders (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('price', 'formula_cost')),
                ingredient TEXT,
                ingredient_code TEXT,
                formula TEXT,
                formula_id TEXT,
                threshold REAL NOT NULL,
                condition TEXT NOT NULL CHECK(condition IN ('above', 'below')),
                enabled BOOLEAN DEFAULT 1,
                last_triggered_at TEXT,
                trigger_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        legacy_columns = self._get_table_columns(conn, "reminders_legacy")
        if "owner_open_id" in legacy_columns:
            conn.execute(
                """
                INSERT INTO reminders (
                    id, user_id, type, ingredient, ingredient_code, formula, formula_id,
                    threshold, condition, enabled, last_triggered_at, trigger_count, created_at, updated_at
                )
                SELECT
                    CAST(id AS TEXT),
                    owner_open_id,
                    CASE WHEN reminder_type = 'price' THEN 'price' ELSE 'formula_cost' END,
                    NULL,
                    NULL,
                    NULL,
                    NULL,
                    0.0,
                    'above',
                    CASE WHEN status = 'disabled' THEN 0 ELSE 1 END,
                    NULL,
                    0,
                    created_at,
                    created_at
                FROM reminders_legacy
                """
            )

    def _init_table(self):
        """Initialize reminders table and indexes."""
        with self.db_pool.get_connection() as conn:
            self._migrate_legacy_reminders_if_needed(conn)

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('price', 'formula_cost')),
                    ingredient TEXT,
                    ingredient_code TEXT,
                    formula TEXT,
                    formula_id TEXT,
                    threshold REAL NOT NULL,
                    condition TEXT NOT NULL CHECK(condition IN ('above', 'below')),
                    enabled BOOLEAN DEFAULT 1,
                    last_triggered_at TEXT,
                    trigger_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_enabled ON reminders(enabled)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_type_ingredient ON reminders(type, ingredient_code)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_type_formula ON reminders(type, formula_id)")

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
    ) -> ServiceResult:
        try:
            reminder_id = str(uuid.uuid4())
            now = datetime.now().isoformat()

            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO reminders
                    (id, user_id, type, ingredient, ingredient_code, formula, formula_id, threshold, condition, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        reminder_id,
                        user_id,
                        reminder_type,
                        ingredient,
                        ingredient_code,
                        formula,
                        formula_id,
                        threshold,
                        condition,
                        now,
                        now,
                    ),
                )

            return ServiceResult(
                success=True,
                data={
                    "id": reminder_id,
                    "user_id": user_id,
                    "type": reminder_type,
                    "ingredient": ingredient,
                    "ingredient_code": ingredient_code,
                    "formula": formula,
                    "formula_id": formula_id,
                    "threshold": threshold,
                    "condition": condition,
                    "enabled": True,
                    "created_at": now,
                },
            )
        except Exception as e:
            logger.error(f"Failed to create reminder: {e}")
            return ServiceResult(success=False, error_code="CREATE_FAILED", error_message=str(e))

    def list_reminders(self, user_id: str, enabled_only: bool = True) -> ServiceResult:
        try:
            with self.db_pool.get_connection() as conn:
                if enabled_only:
                    cursor = conn.execute(
                        "SELECT * FROM reminders WHERE user_id = ? AND enabled = 1 ORDER BY created_at DESC",
                        (user_id,),
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM reminders WHERE user_id = ? ORDER BY created_at DESC",
                        (user_id,),
                    )
                reminders = [dict(row) for row in cursor.fetchall()]

            return ServiceResult(success=True, data={"reminders": reminders, "count": len(reminders)})
        except Exception as e:
            logger.error(f"Failed to list reminders: {e}")
            return ServiceResult(success=False, error_code="LIST_FAILED", error_message=str(e))

    def get_reminder(self, reminder_id: str, user_id: str) -> ServiceResult:
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM reminders WHERE id = ? AND user_id = ?",
                    (reminder_id, user_id),
                )
                row = cursor.fetchone()

            if row:
                return ServiceResult(success=True, data=dict(row))
            return ServiceResult(success=False, error_code="NOT_FOUND", error_message="Reminder not found or access denied")
        except Exception as e:
            logger.error(f"Failed to get reminder: {e}")
            return ServiceResult(success=False, error_code="GET_FAILED", error_message=str(e))

    def delete_reminder(self, reminder_id: str, user_id: str) -> ServiceResult:
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM reminders WHERE id = ? AND user_id = ?",
                    (reminder_id, user_id),
                )
                deleted = cursor.rowcount > 0

            if deleted:
                return ServiceResult(success=True, data={"deleted": True, "reminder_id": reminder_id})
            return ServiceResult(success=False, error_code="NOT_FOUND", error_message="Reminder not found or access denied")
        except Exception as e:
            logger.error(f"Failed to delete reminder: {e}")
            return ServiceResult(success=False, error_code="DELETE_FAILED", error_message=str(e))

    def get_all_enabled_reminders(self) -> ServiceResult:
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM reminders WHERE enabled = 1")
                reminders = [dict(row) for row in cursor.fetchall()]

            return ServiceResult(success=True, data={"reminders": reminders, "count": len(reminders)})
        except Exception as e:
            logger.error(f"Failed to get all enabled reminders: {e}")
            return ServiceResult(success=False, error_code="QUERY_FAILED", error_message=str(e))

    def update_trigger(self, reminder_id: str) -> ServiceResult:
        try:
            now = datetime.now().isoformat()
            with self.db_pool.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE reminders
                    SET last_triggered_at = ?,
                        trigger_count = trigger_count + 1,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (now, now, reminder_id),
                )

            return ServiceResult(
                success=True,
                data={"triggered": True, "reminder_id": reminder_id, "triggered_at": now},
            )
        except Exception as e:
            logger.error(f"Failed to update trigger: {e}")
            return ServiceResult(success=False, error_code="UPDATE_FAILED", error_message=str(e))

    def disable_reminder(self, reminder_id: str, user_id: str) -> ServiceResult:
        try:
            now = datetime.now().isoformat()
            with self.db_pool.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE reminders SET enabled = 0, updated_at = ? WHERE id = ? AND user_id = ?",
                    (now, reminder_id, user_id),
                )
                success = cursor.rowcount > 0

            if success:
                return ServiceResult(success=True, data={"disabled": True, "reminder_id": reminder_id})
            return ServiceResult(success=False, error_code="NOT_FOUND", error_message="Reminder not found or access denied")
        except Exception as e:
            logger.error(f"Failed to disable reminder: {e}")
            return ServiceResult(success=False, error_code="UPDATE_FAILED", error_message=str(e))
