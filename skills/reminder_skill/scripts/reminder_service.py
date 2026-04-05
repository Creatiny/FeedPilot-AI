#!/usr/bin/env python3
"""
Reminder Service - 提醒服务

提供价格提醒和配方成本提醒功能。
"""
import json
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any


# 原料名称映射
_INGREDIENT_MAPPING: Dict[str, Dict[str, str]] = {}

def _load_ingredient_mapping():
    """加载原料名称映射"""
    global _INGREDIENT_MAPPING
    if _INGREDIENT_MAPPING:
        return _INGREDIENT_MAPPING
    
    # 修复路径：从 scripts/ 目录向上一级找到 reference/
    mapping_path = Path(__file__).parent.parent / "reference" / "ingredient_codes.json"
    if mapping_path.exists():
        with open(mapping_path, "r", encoding="utf-8") as f:
            _INGREDIENT_MAPPING = json.load(f)
    return _INGREDIENT_MAPPING


def normalize_ingredient(user_input: str) -> Optional[Dict[str, str]]:
    """
    标准化原料名称
    
    Args:
        user_input: 用户输入的原料名称
        
    Returns:
        标准化后的原料信息，包含 name 和 code
        如果找不到匹配，返回 None
    """
    mapping = _load_ingredient_mapping()
    
    # 1. 精确匹配
    if user_input in mapping:
        return mapping[user_input]
    
    # 2. 小写匹配
    lower_input = user_input.lower()
    if lower_input in mapping:
        return mapping[lower_input]
    
    # 3. 去空格匹配
    no_space = user_input.replace(" ", "")
    if no_space in mapping:
        return mapping[no_space]
    
    # 4. 模糊匹配（包含关系）
    for key, value in mapping.items():
        if key.lower() in lower_input or lower_input in key.lower():
            return value
    
    return None


class ReminderService:
    """提醒服务"""
    
    def __init__(self, db_path: str):
        """
        初始化提醒服务
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        
        # 创建 reminders 表
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
        conn.close()
    
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
    ) -> Dict[str, Any]:
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
            创建的提醒信息
        """
        reminder_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO reminders 
            (id, user_id, type, ingredient, ingredient_code, formula, formula_id, threshold, condition, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (reminder_id, user_id, reminder_type, ingredient, ingredient_code, formula, formula_id, threshold, condition, now, now)
        )
        conn.commit()
        conn.close()
        
        return {
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
    
    def list_reminders(self, user_id: str, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        查询用户的提醒列表
        
        Args:
            user_id: 用户 ID
            enabled_only: 是否只返回启用的提醒
            
        Returns:
            提醒列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
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
        conn.close()
        
        return reminders
    
    def delete_reminder(self, reminder_id: str, user_id: str) -> bool:
        """
        删除提醒（带用户验证）
        
        Args:
            reminder_id: 提醒 ID
            user_id: 用户 ID
            
        Returns:
            是否删除成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "DELETE FROM reminders WHERE id = ? AND user_id = ?",
            (reminder_id, user_id)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        
        return deleted
    
    def get_reminder(self, reminder_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个提醒（带用户验证）
        
        Args:
            reminder_id: 提醒 ID
            user_id: 用户 ID
            
        Returns:
            提醒信息，如果不存在或无权限则返回 None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(
            "SELECT * FROM reminders WHERE id = ? AND user_id = ?",
            (reminder_id, user_id)
        )
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_enabled_reminders(self) -> List[Dict[str, Any]]:
        """
        获取所有启用的提醒（用于 cron 任务）
        
        Returns:
            所有启用的提醒列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(
            "SELECT * FROM reminders WHERE enabled = 1"
        )
        reminders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return reminders
    
    def update_trigger(self, reminder_id: str) -> None:
        """
        更新提醒触发记录
        
        Args:
            reminder_id: 提醒 ID
        """
        conn = sqlite3.connect(self.db_path)
        now = datetime.now().isoformat()
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
        conn.close()
    
    def disable_reminder(self, reminder_id: str, user_id: str) -> bool:
        """
        禁用提醒
        
        Args:
            reminder_id: 提醒 ID
            user_id: 用户 ID
            
        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        now = datetime.now().isoformat()
        cursor = conn.execute(
            "UPDATE reminders SET enabled = 0, updated_at = ? WHERE id = ? AND user_id = ?",
            (now, reminder_id, user_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        return success


# 配方名称映射
FORMULA_MAPPING = {
    "保育料": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
    "保育料1": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
    "保育期": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
    "nursery": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
    
    "育肥料": {"name": "Finishing Diet", "id": "FORMULA_FINISHING"},
    "育肥期": {"name": "Finishing Diet", "id": "FORMULA_FINISHING"},
    "finishing": {"name": "Finishing Diet", "id": "FORMULA_FINISHING"},
    
    "生长料": {"name": "Grower Diet 1", "id": "FORMULA_GROWER_1"},
    "生长期": {"name": "Grower Diet 1", "id": "FORMULA_GROWER_1"},
    "grower": {"name": "Grower Diet 1", "id": "FORMULA_GROWER_1"},
    
    "肉鸡料": {"name": "Broiler Starter", "id": "FORMULA_BROILER_STARTER"},
    "肉鸡开食料": {"name": "Broiler Starter", "id": "FORMULA_BROILER_STARTER"},
    "broiler": {"name": "Broiler Starter", "id": "FORMULA_BROILER_STARTER"},
    
    "蛋鸡料": {"name": "Layer Diet", "id": "FORMULA_LAYER"},
    "layer": {"name": "Layer Diet", "id": "FORMULA_LAYER"},
    
    "肉牛育肥料": {"name": "Beef Cattle Finisher", "id": "FORMULA_BEEF_FINISHING"},
    "beef finisher": {"name": "Beef Cattle Finisher", "id": "FORMULA_BEEF_FINISHING"},
}


def normalize_formula(user_input: str) -> Optional[Dict[str, str]]:
    """
    标准化配方名称
    
    Args:
        user_input: 用户输入的配方名称
        
    Returns:
        标准化后的配方信息，包含 name 和 id
    """
    # 1. 精确匹配
    if user_input in FORMULA_MAPPING:
        return FORMULA_MAPPING[user_input]
    
    # 2. 小写匹配
    lower_input = user_input.lower()
    if lower_input in FORMULA_MAPPING:
        return FORMULA_MAPPING[lower_input]
    
    # 3. 模糊匹配
    for key, value in FORMULA_MAPPING.items():
        if key.lower() in lower_input or lower_input in key.lower():
            return value
    
    return None
