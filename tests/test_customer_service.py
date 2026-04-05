#!/usr/bin/env python3
"""
FeedSales AI - CustomerService 测试

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
from src.services.customer_service import CustomerService, ServiceResult


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
    
    # 创建客户表（与 schema.sql 一致）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_open_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            animal_type TEXT,
            scale INTEGER,
            notes TEXT,
            version INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_open_id) REFERENCES users(open_id)
        )
    ''')
    
    # 插入测试用户
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('user_a',))
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('user_b',))
    
    conn.commit()
    conn.close()
    
    pool = DatabasePool(db_path)
    return db_path, pool


def test_create_customer():
    """测试创建客户"""
    print("\n🧪 测试：创建客户")
    
    db_path, pool = setup_test_db()
    try:
        service = CustomerService(pool)
        
        customer_data = {
            'name': 'John Smith',
            'phone': '555-1234',
            'address': '123 Farm Road, Iowa',
            'animal_type': 'swine',
            'scale': 5000,
            'notes': 'Swine farmer'
        }
        
        result = service.create_customer('user_a', customer_data)
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert result.data['id'] > 0, "应该返回 ID"
        assert result.data['name'] == 'John Smith', f"名称错误: {result.data['name']}"
        
        print(f"  ✅ 创建成功，ID: {result.data['id']}")
        
    finally:
        os.unlink(db_path)


def test_create_customer_missing_name():
    """测试创建客户缺少名称"""
    print("\n🧪 测试：创建客户缺少名称")
    
    db_path, pool = setup_test_db()
    try:
        service = CustomerService(pool)
        
        customer_data = {
            'animal_type': 'Test Farm',
            'phone': '555-9999'
        }
        
        result = service.create_customer('user_a', customer_data)
        
        assert not result.success, "应该失败"
        assert result.error_code == 'E001', f"错误码应该是 E001，实际: {result.error_code}"
        
        print("  ✅ 正确返回 E001 错误")
        
    finally:
        os.unlink(db_path)


def test_get_customer():
    """测试获取客户"""
    print("\n🧪 测试：获取客户")
    
    db_path, pool = setup_test_db()
    try:
        service = CustomerService(pool)
        
        # 先创建
        customer_data = {'name': 'Jane Doe', 'address': 'Doe Ranch'}
        create_result = service.create_customer('user_a', customer_data)
        assert create_result.success
        
        # 再获取
        result = service.get_customer('user_a', 'Jane Doe')
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert result.data['name'] == 'Jane Doe', f"名称错误: {result.data['name']}"
        assert result.data['address'] == 'Doe Ranch', f"地址错误: {result.data['address']}"
        
        print("  ✅ 获取成功")
        
    finally:
        os.unlink(db_path)


def test_list_customers():
    """测试列出客户"""
    print("\n🧪 测试：列出客户")
    
    db_path, pool = setup_test_db()
    try:
        service = CustomerService(pool)
        
        # 创建多个客户
        service.create_customer('user_a', {'name': 'Customer 1'})
        service.create_customer('user_a', {'name': 'Customer 2'})
        service.create_customer('user_a', {'name': 'Customer 3'})
        
        result = service.list_customers('user_a')
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert result.data['total'] == 3, f"应该有 3 个客户，实际: {result.data['total']}"
        
        print(f"  ✅ 列出 {result.data['total']} 个客户")
        
    finally:
        os.unlink(db_path)


def test_multi_tenant_isolation():
    """测试多租户隔离"""
    print("\n🧪 测试：多租户隔离")
    
    db_path, pool = setup_test_db()
    try:
        service = CustomerService(pool)
        
        # 用户 A 创建客户
        service.create_customer('user_a', {'name': 'User A Customer'})
        
        # 用户 B 不应该能看到用户 A 的客户
        result_b = service.get_customer('user_b', 'User A Customer')
        assert not result_b.success, "用户 B 不应该能看到用户 A 的客户"
        assert result_b.error_code == 'E002', "应该返回不存在错误"
        
        print("  ✅ 用户隔离正确")
        
        # 用户 B 创建同名客户
        result_b_create = service.create_customer('user_b', {'name': 'User A Customer'})
        assert result_b_create.success, "用户 B 应该能创建同名客户"
        
        print("  ✅ 不同用户可以创建同名客户")
        
    finally:
        os.unlink(db_path)


def test_update_customer():
    """测试更新客户"""
    print("\n🧪 测试：更新客户")
    
    db_path, pool = setup_test_db()
    try:
        service = CustomerService(pool)
        
        # 创建客户
        create_result = service.create_customer('user_a', {
            'name': 'Update Test',
            'address': 'Original Address'
        })
        customer_id = create_result.data['id']
        
        # 更新客户
        update_data = {
            'address': 'Updated Address',
            'notes': 'Updated notes'
        }
        result = service.update_customer('user_a', customer_id, update_data)
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert result.data['address'] == 'Updated Address', f"地址应该更新，实际: {result.data['address']}"
        
        print("  ✅ 更新成功")
        
    finally:
        os.unlink(db_path)


def test_delete_customer():
    """测试删除客户"""
    print("\n🧪 测试：删除客户")
    
    db_path, pool = setup_test_db()
    try:
        service = CustomerService(pool)
        
        # 创建客户
        create_result = service.create_customer('user_a', {'name': 'Delete Test'})
        customer_id = create_result.data['id']
        
        # 删除客户
        result = service.delete_customer('user_a', customer_id)
        assert result.success, f"删除应该成功，但返回: {result.error_message}"
        
        # 验证已删除
        get_result = service.get_customer('user_a', 'Delete Test')
        assert not get_result.success, "删除后应该获取不到"
        
        print("  ✅ 删除成功")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - CustomerService 测试 (TDD)")
    print("=" * 60)
    
    tests = [
        test_create_customer,
        test_create_customer_missing_name,
        test_get_customer,
        test_list_customers,
        test_multi_tenant_isolation,
        test_update_customer,
        test_delete_customer,
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