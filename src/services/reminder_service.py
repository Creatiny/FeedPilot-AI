"""
FeedSales AI - ReminderService

提醒服务，支持价格提醒和配方成本提醒
"""

import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from ..database.pool import DatabasePool
from ..types import ServiceResult

logger = logging.getLogger(__name__)


class ReminderService:
    """提醒服务"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
        self._init_table()
    
    def _init_table(self):
        """初始化 reminders 表"""
        with self.db_pool.get_connection() as conn:
            conn.execute("""
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
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_enabled ON reminders(enabled)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_type_ingredient ON reminders(type, ingredient_code)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_type_formula ON reminders(type, formula_id)")
            
            conn.commit()
    
    def create_reminder(
        self,
        user_id: str,
        reminder_type: str,
        threshold: float,
        condition: str,
        ingredient: Optional[str] = None,
        ingredient_code: Optional[str] = None,
        formula: Optional[str] = None,
        formula_id: Optional[str] = None
    ) -> ServiceResult:
        """
        创建提醒
        
        Args:
            user_id: 用户 ID
            reminder_type: 提醒类型 ('price' | 'formula_cost')
            threshold: 阈值
            condition: 条件 ('above' | 'below')
            ingredient: 原料名称
            ingredient_code: 原料代码
            formula: 配方名称
            formula_id: 配方 ID
            
        Returns:
            ServiceResult: 包含创建的提醒信息
        """
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
                    (reminder_id, user_id, reminder_type, ingredient, ingredient_code, formula, formula_id, threshold, condition, now, now)
                )
                conn.commit()
            
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
                    "created_at": now
                }
            )
        except Exception as e:
            logger.error(f"Failed to create reminder: {e}")
            return ServiceResult(
                success=False,
                error_code="CREATE_FAILED",
                error_message=str(e)
            )
    
    def list_reminders(self, user_id: str, enabled_only: bool = True) -> ServiceResult:
        """
        查询用户的提醒列表
        
        Args:
            user_id: 用户 ID
            enabled_only: 是否只返回启用的提醒
            
        Returns:
            ServiceResult: 包含提醒列表
        """
        try:
            with self.db_pool.get_connection() as conn:
                if enabled_only:
                    cursor = conn.execute(
                        "SELECT * FROM reminders WHERE user_id = ? AND enabled = 1 ORDER BY created_at DESC",
                        (user_id,)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT * FROM reminders WHERE user_id = ? ORDER BY created_at DESC",
                        (user_id,)
                    )
                
                reminders = [dict(row) for row in cursor.fetchall()]
            
            return ServiceResult(
                success=True,
                data={"reminders": reminders, "count": len(reminders)}
            )
        except Exception as e:
            logger.error(f"Failed to list reminders: {e}")
            return ServiceResult(
                success=False,
                error_code="LIST_FAILED",
                error_message=str(e)
            )
    
    def get_reminder(self, reminder_id: str, user_id: str) -> ServiceResult:
        """
        获取单个提醒（带用户验证）
        
        Args:
            reminder_id: 提醒 ID
            user_id: 用户 ID
            
        Returns:
            ServiceResult: 包含提醒信息
        """
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM reminders WHERE id = ? AND user_id = ?",
                    (reminder_id, user_id)
                )
                row = cursor.fetchone()
            
            if row:
                return ServiceResult(
                    success=True,
                    data=dict(row)
                )
            else:
                return ServiceResult(
                    success=False,
                    error_code="NOT_FOUND",
                    error_message="Reminder not found or access denied"
                )
        except Exception as e:
            logger.error(f"Failed to get reminder: {e}")
            return ServiceResult(
                success=False,
                error_code="GET_FAILED",
                error_message=str(e)
            )
    
    def delete_reminder(self, reminder_id: str, user_id: str) -> ServiceResult:
        """
        删除提醒（带用户验证）
        
        Args:
            reminder_id: 提醒 ID
            user_id: 用户 ID
            
        Returns:
            ServiceResult: 是否删除成功
        """
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM reminders WHERE id = ? AND user_id = ?",
                    (reminder_id, user_id)
                )
                conn.commit()
                deleted = cursor.rowcount > 0
            
            if deleted:
                return ServiceResult(
                    success=True,
                    data={"deleted": True, "reminder_id": reminder_id}
                )
            else:
                return ServiceResult(
                    success=False,
                    error_code="NOT_FOUND",
                    error_message="Reminder not found or access denied"
                )
        except Exception as e:
            logger.error(f"Failed to delete reminder: {e}")
            return ServiceResult(
                success=False,
                error_code="DELETE_FAILED",
                error_message=str(e)
            )
    
    def get_all_enabled_reminders(self) -> ServiceResult:
        """
        获取所有启用的提醒（用于 cron 任务）
        
        Returns:
            ServiceResult: 包含所有启用的提醒列表
        """
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM reminders WHERE enabled = 1"
                )
                reminders = [dict(row) for row in cursor.fetchall()]
            
            return ServiceResult(
                success=True,
                data={"reminders": reminders, "count": len(reminders)}
            )
        except Exception as e:
            logger.error(f"Failed to get all enabled reminders: {e}")
            return ServiceResult(
                success=False,
                error_code="QUERY_FAILED",
                error_message=str(e)
            )
    
    def update_trigger(self, reminder_id: str) -> ServiceResult:
        """
        更新提醒触发记录
        
        Args:
            reminder_id: 提醒 ID
            
        Returns:
            ServiceResult: 是否更新成功
        """
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
                    (now, now, reminder_id)
                )
                conn.commit()
            
            return ServiceResult(
                success=True,
                data={"triggered": True, "reminder_id": reminder_id, "triggered_at": now}
            )
        except Exception as e:
            logger.error(f"Failed to update trigger: {e}")
            return ServiceResult(
                success=False,
                error_code="UPDATE_FAILED",
                error_message=str(e)
            )
    
    def disable_reminder(self, reminder_id: str, user_id: str) -> ServiceResult:
        """
        禁用提醒
        
        Args:
            reminder_id: 提醒 ID
            user_id: 用户 ID
            
        Returns:
            ServiceResult: 是否成功
        """
        try:
            now = datetime.now().isoformat()
            with self.db_pool.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE reminders SET enabled = 0, updated_at = ? WHERE id = ? AND user_id = ?",
                    (now, reminder_id, user_id)
                )
                conn.commit()
                success = cursor.rowcount > 0
            
            if success:
                return ServiceResult(
                    success=True,
                    data={"disabled": True, "reminder_id": reminder_id}
                )
            else:
                return ServiceResult(
                    success=False,
                    error_code="NOT_FOUND",
                    error_message="Reminder not found or access denied"
                )
        except Exception as e:
            logger.error(f"Failed to disable reminder: {e}")
            return ServiceResult(
                success=False,
                error_code="UPDATE_FAILED",
                error_message=str(e)
            )
