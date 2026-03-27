#!/usr/bin/env python3
"""
FeedSales AI - 数据库初始化脚本

创建数据库目录和初始 Schema
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool


def init_database(db_path: str = "data/feed_sales.db"):
    """初始化数据库"""
    print(f"📦 初始化数据库：{db_path}")
    
    # 创建数据库目录
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 初始化连接池（会自动创建 Schema）
    pool = DatabasePool(str(db_file))
    
    # 测试连接
    if pool.test_connection():
        print("✅ 数据库初始化成功")
        print(f"📁 数据库文件：{db_file}")
        print(f"📁 WAL 文件：{pool.get_wal_path()}")
        print(f"📁 SHM 文件：{pool.get_shm_path()}")
        return True
    else:
        print("❌ 数据库初始化失败")
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
