"""
FeedSales AI - FeedSalesHarness

OpenClaw Agent 集成层
- 移除 TaskRouter，让 LLM 原生处理 NLU
- Agent 直接调用 skills，传递结构化参数
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..database.pool import DatabasePool
from ..services.formula_service import FormulaService
from ..services.price_service import PriceService
from ..services.customer_service import CustomerService
from ..services.calculation_service import CalculationService
from .session_state import SessionStateManager
from .result_validator import ResultValidator

logger = logging.getLogger(__name__)


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, db_pool: DatabasePool = None):
        self.db_pool = db_pool

    def log(self, user_id: str, action: str, details: Dict, result: str):
        """记录审计日志"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "details": details,
            "result": result
        }

        # 输出到日志
        logger.info(f"AUDIT: {log_entry}")

        # 可选：写入数据库
        if self.db_pool:
            self._write_to_db(log_entry)

    def _write_to_db(self, entry: Dict):
        """写入数据库（可选）"""
        try:
            with self.db_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audit_log
                    (timestamp, user_id, action, details, result)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    entry['timestamp'],
                    entry['user_id'],
                    entry['action'],
                    entry['details'],
                    entry['result']
                ))
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to write audit log to DB: {e}")


class FeedSalesHarness:
    """
    FeedSales 业务最小 Harness

    整合所有服务和 Harness 组件，提供统一的业务处理入口

    架构变更（2026-04-15）：
    - 移除 TaskRouter（regex NLU）
    - 让 OpenClaw Agent 原生处理自然语言理解
    - Agent 调用 skills 时传递结构化参数
    """

    def __init__(self, db_pool: DatabasePool):
        """
        初始化 Harness

        Args:
            db_pool: 数据库连接池
        """
        self.db_pool = db_pool

        # 初始化服务层
        self.formula_service = FormulaService(db_pool)
        self.price_service = PriceService(db_pool)
        self.customer_service = CustomerService(db_pool)
        self.calculation_service = CalculationService(db_pool)

        # 初始化 Harness 组件（移除 TaskRouter）
        self.session_manager = SessionStateManager()
        self.result_validator = ResultValidator()
        self.audit_logger = AuditLogger(db_pool)

        logger.info("FeedSalesHarness initialized (Agent-based NLU)")

    def process(self, session_id: str, user_id: str, message: str) -> Dict[str, Any]:
        """
        处理用户消息

        注意：此方法现在仅用于会话管理和审计日志
        实际业务逻辑由 OpenClaw Agent 处理

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            message: 用户消息

        Returns:
            Dict: 处理结果
        """
        try:
            # 1. 更新会话状态
            self.session_manager.update_state(session_id, user_id=user_id)
            self.session_manager.increment_turn(session_id)

            # 2. 审计日志（Agent 会记录更详细的日志）
            self.audit_logger.log(
                user_id,
                'user_message',
                {'message': message},
                'received'
            )

            # 3. 返回成功，让 Agent 处理
            return {
                'success': True,
                'message': 'Agent processing started',
                'session_id': session_id,
                'user_id': user_id
            }

        except Exception as e:
            logger.error(f"Harness process failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'task_type': 'unknown'
            }

    def get_session_state(self, session_id: str):
        """获取会话状态"""
        return self.session_manager.get_state(session_id)

    def clear_session(self, session_id: str):
        """清除会话"""
        self.session_manager.clear_state(session_id)
