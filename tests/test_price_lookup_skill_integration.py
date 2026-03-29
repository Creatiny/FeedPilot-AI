#!/usr/bin/env python3
"""
FeedSales AI - PriceLookupSkill 集成测试

测试技能走 PriceService 统一接口
"""

import sys
import tempfile
import os
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.services.price_service import PriceService
from skills.price_lookup_skill.skill import PriceLookupSkill


def setup_test_db():
    """创建测试数据库"""
    DatabasePool._instance = None
    DatabasePool._lock = threading.Lock()
    
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('CREATE TABLE users (open_id TEXT PRIMARY KEY)')
    cursor.execute('''
        CREATE TABLE ingredient_prices (
            id INTEGER PRIMARY KEY,
            owner_open_id TEXT NOT NULL,
            ingredient_code TEXT NOT NULL,
            ingredient_name TEXT NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            unit TEXT DEFAULT 'ton',
            source TEXT DEFAULT 'manual',
            price_date DATE NOT NULL,
            UNIQUE(owner_open_id, ingredient_code, price_date)
        )
    ''')
    
    cursor.execute("INSERT INTO users VALUES ('user_a')")
    cursor.execute("INSERT INTO users VALUES ('system_public')")
    
    # 公共价格
    cursor.execute('''
        INSERT INTO ingredient_prices 
        (owner_open_id, ingredient_code, ingredient_name, price, price_date)
        VALUES (?, ?, ?, ?, ?)
    ''', ('system_public', 'ING_CORN', 'Corn, grain', 180.00, '2026-03-29'))
    
    cursor.execute('''
        INSERT INTO ingredient_prices 
        (owner_open_id, ingredient_code, ingredient_name, price, price_date)
        VALUES (?, ?, ?, ?, ?)
    ''', ('system_public', 'ING_SBM', 'Soybean meal, 48%', 350.00, '2026-03-29'))
    
    conn.commit()
    conn.close()
    
    return db_path, DatabasePool(db_path)


def test_query_public_price():
    """测试查询公共价格"""
    print("\n🧪 测试：查询公共价格")
    
    db_path, pool = setup_test_db()
    try:
        service = PriceService(pool)
        skill = PriceLookupSkill(price_service=service)
        
        import asyncio
        result = asyncio.run(skill.execute('user_a', '玉米价格'))
        
        assert result['success'], f"应该成功: {result.get('error')}"
        assert result['data']['price'] == 180.00
        assert result['data']['source'] == 'public'
        
        print(f"  ✅ 查询成功: ${result['data']['price']}/ton")
        
    finally:
        os.unlink(db_path)


def test_set_private_price():
    """测试设置私有价格"""
    print("\n🧪 测试：设置私有价格")
    
    db_path, pool = setup_test_db()
    try:
        service = PriceService(pool)
        skill = PriceLookupSkill(price_service=service)
        
        import asyncio
        result = asyncio.run(skill.execute('user_a', '设置玉米价格 175'))
        
        assert result['success'], f"应该成功: {result.get('error')}"
        
        # 验证私有价格生效
        result2 = asyncio.run(skill.execute('user_a', '玉米价格'))
        assert result2['data']['price'] == 175.00
        assert result2['data']['source'] == 'private'
        
        print("  ✅ 私有价格设置成功")
        
    finally:
        os.unlink(db_path)


def test_list_prices():
    """测试列出价格"""
    print("\n🧪 测试：列出价格")
    
    db_path, pool = setup_test_db()
    try:
        service = PriceService(pool)
        skill = PriceLookupSkill(price_service=service)
        
        import asyncio
        result = asyncio.run(skill.execute('user_a', '列出所有价格'))
        
        assert result['success']
        assert result['data']['total'] >= 2
        
        print(f"  ✅ 列出 {result['data']['total']} 个价格")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - PriceLookupSkill 集成测试")
    print("=" * 60)
    
    tests = [
        test_query_public_price,
        test_set_private_price,
        test_list_prices,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)