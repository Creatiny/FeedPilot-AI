"""
FeedSales AI - Database Pool

SQLite 连接池（WAL 模式）
提供线程安全的数据库连接管理
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


class DatabasePool:
    """SQLite 连接池（WAL 模式）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str):
        """初始化数据库连接池"""
        if self._initialized:
            return
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
        self._initialized = True
    
    def _init_db(self):
        """初始化数据库（启用 WAL 模式）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 启用 WAL 模式
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA foreign_keys=ON")
        
        # 执行 Schema
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                cursor.executescript(f.read())
        
        conn.commit()
        conn.close()
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接（线程安全）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def test_connection(self) -> bool:
        """测试连接"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]
            return result == 1
    
    def get_wal_path(self) -> Path:
        """获取 WAL 文件路径"""
        return self.db_path.with_suffix(self.db_path.suffix + '-wal')
    
    def get_shm_path(self) -> Path:
        """获取 SHM 文件路径"""
        return self.db_path.with_suffix(self.db_path.suffix + '-shm')
