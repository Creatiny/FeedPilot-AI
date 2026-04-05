"""
FeedSales AI - SessionStateManager

会话状态管理器，维护当前会话上下文（线程安全）
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class SessionState:
    """会话状态"""
    user_id: Optional[str] = None
    current_customer: Optional[str] = None
    current_formula: Optional[str] = None
    price_mode: str = 'mixed'  # 'private' | 'public' | 'mixed'
    last_quote_result: Optional[Dict] = None
    conversation_turn: int = 0
    last_access: float = field(default_factory=time.time)


class SessionStateManager:
    """
    会话状态管理器（线程安全）
    
    维护当前会话上下文，支持跨对话连续性
    """
    
    def __init__(self, ttl: int = 3600):
        """
        初始化
        
        Args:
            ttl: 会话过期时间（秒），默认 1 小时
        """
        self.sessions: Dict[str, SessionState] = {}
        self.ttl = ttl
        self._lock = threading.RLock()  # 可重入锁
    
    def get_state(self, session_id: str) -> SessionState:
        """
        获取会话状态（线程安全）
        
        Args:
            session_id: 会话 ID
            
        Returns:
            SessionState: 会话状态
        """
        with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = SessionState()
            
            state = self.sessions[session_id]
            state.last_access = time.time()
            
            return state
    
    def update_state(self, session_id: str, **kwargs) -> None:
        """
        更新会话状态（线程安全）
        
        Args:
            session_id: 会话 ID
            **kwargs: 要更新的字段
        """
        with self._lock:
            state = self.get_state(session_id)
            
            for key, value in kwargs.items():
                if hasattr(state, key):
                    setattr(state, key, value)
    
    def increment_turn(self, session_id: str) -> int:
        """
        增加对话轮次（线程安全）
        
        Args:
            session_id: 会话 ID
            
        Returns:
            int: 当前轮次
        """
        with self._lock:
            state = self.get_state(session_id)
            state.conversation_turn += 1
            return state.conversation_turn
    
    def clear_state(self, session_id: str) -> None:
        """
        清除会话状态（线程安全）
        
        Args:
            session_id: 会话 ID
        """
        with self._lock:
            self.sessions[session_id] = SessionState()
    
    def cleanup_expired(self) -> int:
        """
        清理过期会话（线程安全）
        
        Returns:
            int: 清理的会话数
        """
        with self._lock:
            now = time.time()
            expired = [
                sid for sid, state in self.sessions.items()
                if now - state.last_access > self.ttl
            ]
            
            for sid in expired:
                del self.sessions[sid]
            
            return len(expired)
    
    def get_active_sessions(self) -> int:
        """获取活跃会话数（线程安全）"""
        with self._lock:
            return len(self.sessions)