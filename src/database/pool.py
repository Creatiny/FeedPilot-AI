"""
FeedSales AI - Database Pool

SQLite connection pool utilities (WAL mode)
Provides thread-safe database connection management.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


class DatabasePool:
    """SQLite connection pool (WAL mode)."""

    _instances = {}
    _lock = threading.Lock()

    def __new__(cls, db_path: str):
        """One shared DatabasePool instance per database path."""
        resolved_path = str(Path(db_path).resolve())
        with cls._lock:
            if resolved_path not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[resolved_path] = instance
            return cls._instances[resolved_path]

    def __init__(self, db_path: str):
        """Initialize database pool."""
        resolved_path = Path(db_path).resolve()
        if self._initialized:
            if str(self.db_path) != str(resolved_path):
                raise RuntimeError(
                    f"DatabasePool instance already initialized with {self.db_path}, "
                    f"cannot switch to {resolved_path}"
                )
            return

        self.db_path = resolved_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()
        self._initialized = True

    def _init_db(self):
        """Initialize database and enable WAL mode."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA foreign_keys=ON")

        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                cursor.executescript(f.read())

        conn.commit()
        conn.close()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection (thread-safe, auto-commit)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def test_connection(self) -> bool:
        """Test database connectivity."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()[0]
            return result == 1

    def get_wal_path(self) -> Path:
        """Get WAL file path."""
        return self.db_path.with_suffix(self.db_path.suffix + "-wal")

    def get_shm_path(self) -> Path:
        """Get SHM file path."""
        return self.db_path.with_suffix(self.db_path.suffix + "-shm")
