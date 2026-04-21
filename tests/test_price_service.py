#!/usr/bin/env python3
"""
FeedSales AI - PriceService 测试

TDD: 先写测试，再写实现
"""

import sys
import tempfile
import os
import threading
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.services.price_service import PriceService, ServiceResult


def setup_test_db():
    """创建测试数据库"""
    # 重置 DatabasePool 单例
    DatabasePool._instance = None
    DatabasePool._lock = threading.Lock()
    
    # 使用临时文件
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # 初始化 schema
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            open_id TEXT PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建价格表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingredient_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_open_id TEXT NOT NULL,
            ingredient_code TEXT NOT NULL,
            ingredient_name TEXT NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            unit TEXT DEFAULT 'ton',
            source TEXT DEFAULT 'manual',
            price_date DATE NOT NULL,
            version INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_open_id) REFERENCES users(open_id),
            UNIQUE(owner_open_id, ingredient_code, price_date)
        )
    ''')
    
    # 插入测试用户
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('user_a',))
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('user_b',))
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('system_public',))
    
    # 插入公共价格
    cursor.execute('''
        INSERT INTO ingredient_prices (owner_open_id, ingredient_code, ingredient_name, price, price_date)
        VALUES (?, ?, ?, ?, ?)
    ''', ('system_public', 'ING_CORN', 'Corn, grain', 180.00, '2026-03-29'))
    
    cursor.execute('''
        INSERT INTO ingredient_prices (owner_open_id, ingredient_code, ingredient_name, price, price_date)
        VALUES (?, ?, ?, ?, ?)
    ''', ('system_public', 'ING_SBM', 'Soybean meal, 48%', 350.00, '2026-03-29'))
    
    conn.commit()
    conn.close()
    
    pool = DatabasePool(db_path)
    return db_path, pool


def test_get_public_price():
    """测试获取公共价格"""
    print("\n🧪 测试：获取公共价格")
    
    db_path, pool = setup_test_db()
    try:
        service = PriceService(pool)
        
        result = service.get_price('user_a', 'ING_CORN')
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert result.data['price'] == 180.00, f"价格错误: {result.data['price']}"
        assert result.source == 'public', f"来源应该是 public，实际: {result.source}"
        
        print("  ✅ 公共价格获取成功")
        print(f"  ✅ 来源标记正确: {result.source}")
        
    finally:
        os.unlink(db_path)


def test_get_nonexistent_price():
    """测试获取不存在的价格"""
    print("\n🧪 测试：获取不存在的价格")
    
    db_path, pool = setup_test_db()
    try:
        service = PriceService(pool)
        
        result = service.get_price('user_a', 'ING_NONEXISTENT')
        
        assert not result.success, "应该失败"
        assert result.error_code == 'E002', f"错误码应该是 E002，实际: {result.error_code}"
        assert result.error_code == 'E002', f"错误码应该是 E002，实际: {result.error_code}"
        
        print("  ✅ 正确返回 E002 错误")
        
    finally:
        os.unlink(db_path)


def test_set_private_price():
    """测试设置私有价格"""
    print("\n🧪 测试：设置私有价格")
    
    db_path, pool = setup_test_db()
    try:
        service = PriceService(pool)
        
        # 设置私有价格
        result = service.set_private_price('user_a', 'Corn, grain', 175.00)
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        
        print("  ✅ 私有价格设置成功")
        
        # 验证获取时优先返回私有价格
        result2 = service.get_price('user_a', 'ING_CORN')
        assert result2.success, "获取应该成功"
        assert result2.data['price'] == 175.00, f"价格应该是 175.00，实际: {result2.data['price']}"
        assert result2.source == 'private', f"来源应该是 private，实际: {result2.source}"
        
        print("  ✅ 私有价格优先返回")
        
    finally:
        os.unlink(db_path)


def test_multi_tenant_price_isolation():
    """测试多租户价格隔离"""
    print("\n🧪 测试：多租户价格隔离")
    
    db_path, pool = setup_test_db()
    try:
        service = PriceService(pool)
        
        # 用户 A 设置私有价格
        result_a = service.set_private_price('user_a', 'Corn, grain', 170.00)
        assert result_a.success, "用户 A 设置应该成功"
        
        # 用户 B 获取价格时应该返回公共价格，不是用户 A 的私有价格
        result_b = service.get_price('user_b', 'ING_CORN')
        assert result_b.success, "用户 B 获取应该成功"
        assert result_b.data['price'] == 180.00, f"用户 B 应该获取公共价格，实际: {result_b.data['price']}"
        assert result_b.source == 'public', f"用户 B 来源应该是 public，实际: {result_b.source}"
        
        print("  ✅ 用户隔离正确")
        
    finally:
        os.unlink(db_path)


def test_list_private_prices():
    """测试列出私有价格"""
    print("\n🧪 测试：列出私有价格")
    
    db_path, pool = setup_test_db()
    try:
        service = PriceService(pool)
        
        # 设置多个私有价格
        service.set_private_price('user_a', 'Corn, grain', 170.00)
        service.set_private_price('user_a', 'Soybean meal, 48%', 340.00)
        
        result = service.list_private_prices('user_a')
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert result.data['total'] == 2, f"应该有 2 个私有价格，实际: {result.data['total']}"
        
        print(f"  ✅ 列出 {result.data['total']} 个私有价格")
        
    finally:
        os.unlink(db_path)


def test_list_public_prices():
    """测试列出公共价格"""
    print("\n🧪 测试：列出公共价格")
    
    db_path, pool = setup_test_db()
    try:
        service = PriceService(pool)
        
        result = service.list_public_prices()
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert result.data['total'] == 2, f"应该有 2 个公共价格，实际: {result.data['total']}"
        
        print(f"  ✅ 列出 {result.data['total']} 个公共价格")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - PriceService 测试 (TDD)")
    print("=" * 60)
    
    tests = [
        test_get_public_price,
        test_get_nonexistent_price,
        test_set_private_price,
        test_multi_tenant_price_isolation,
        test_list_private_prices,
        test_list_public_prices,
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