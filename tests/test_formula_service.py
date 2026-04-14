#!/usr/bin/env python3
"""
FeedSales AI - FormulaService 测试

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
from src.database.repository import FormulaRepository
from src.services.formula_service import FormulaService, ServiceResult


def setup_test_db():
    """创建测试数据库"""
    # 重置 DatabasePool 单例
    DatabasePool._instance = None
    DatabasePool._lock = threading.Lock()
    
    # 使用临时文件
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # 初始化 schema（使用 sqlite3 直接连接）
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
    
    # 创建配方表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_open_id TEXT NOT NULL,
            name TEXT NOT NULL,
            animal_type TEXT,
            stage_type TEXT NOT NULL,
            notes TEXT,
            version INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_open_id) REFERENCES users(open_id),
            UNIQUE(owner_open_id, name)
        )
    ''')
    
    # 创建成分表（含 ingredient_code）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formula_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            ingredient_code TEXT NOT NULL,
            ratio_percent REAL NOT NULL,
            FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
        )
    ''')
    
    # 插入测试用户
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('user_a',))
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('user_b',))
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('system_public',))
    
    # 插入公共配方
    cursor.execute('''
        INSERT INTO formulas (owner_open_id, name, animal_type, stage_type)
        VALUES (?, ?, ?, ?)
    ''', ('system_public', 'Nursery Diet 1', 'Swine', 'Nursery'))
    formula_id = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO formula_ingredients (formula_id, ingredient_name, ingredient_code, ratio_percent)
        VALUES (?, ?, ?, ?)
    ''', (formula_id, 'Corn, grain', 'ING_CORN', 60.0))
    cursor.execute('''
        INSERT INTO formula_ingredients (formula_id, ingredient_name, ingredient_code, ratio_percent)
        VALUES (?, ?, ?, ?)
    ''', (formula_id, 'Soybean meal, 48%', 'ING_SBM', 25.0))
    
    conn.commit()
    conn.close()
    
    # 使用 DatabasePool
    pool = DatabasePool(db_path)
    
    return db_path, pool


def test_get_public_formula():
    """测试获取公共配方"""
    print("\n🧪 测试：获取公共配方")
    
    db_path, pool = setup_test_db()
    try:
        service = FormulaService(pool)
        
        # 测试：用户获取公共配方
        result = service.get_formula('user_a', 'Nursery Diet 1')
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert result.data is not None, "应该返回数据"
        assert result.data['name'] == 'Nursery Diet 1', f"名称错误: {result.data['name']}"
        assert result.data['animal_type'] == 'Swine', f"动物类型错误: {result.data['animal_type']}"
        assert result.source == 'public', f"来源应该是 public，实际: {result.source}"
        
        print("  ✅ 公共配方获取成功")
        print(f"  ✅ 来源标记正确: {result.source}")
        
    finally:
        os.unlink(db_path)


def test_get_nonexistent_formula():
    """测试获取不存在的配方"""
    print("\n🧪 测试：获取不存在的配方")
    
    db_path, pool = setup_test_db()
    try:
        service = FormulaService(pool)
        
        result = service.get_formula('user_a', 'Nonexistent Formula')
        
        assert not result.success, "应该失败"
        assert result.error_code == 'E002', f"错误码应该是 E002，实际: {result.error_code}"
        
        print("  ✅ 正确返回 E002 错误")
        
    finally:
        os.unlink(db_path)


def test_create_private_formula():
    """测试创建私有配方"""
    print("\n🧪 测试：创建私有配方")
    
    db_path, pool = setup_test_db()
    try:
        service = FormulaService(pool)
        
        # 创建私有配方
        formula_data = {
            'name': 'My Private Formula',
            'animal_type': 'Swine',
            'stage_type': 'Nursery',
            'ingredients': [
                {'name': 'Corn, grain', 'ratio': 65.0},
                {'name': 'Soybean meal, 48%', 'ratio': 20.0}
            ]
        }
        
        result = service.create_formula('user_a', formula_data)
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert result.data['id'] > 0, "应该返回 ID"
        
        print(f"  ✅ 创建成功，ID: {result.data['id']}")
        
        # 验证可以获取
        result2 = service.get_formula('user_a', 'My Private Formula')
        assert result2.success, "应该能获取刚创建的配方"
        assert result2.source == 'private', f"来源应该是 private，实际: {result2.source}"
        
        print("  ✅ 私有配方获取成功")
        print(f"  ✅ 来源标记正确: {result2.source}")
        
    finally:
        os.unlink(db_path)


def test_multi_tenant_isolation():
    """测试多租户隔离"""
    print("\n🧪 测试：多租户隔离")
    
    db_path, pool = setup_test_db()
    try:
        service = FormulaService(pool)
        
        # 用户 A 创建私有配方
        formula_data = {
            'name': 'User A Formula',
            'animal_type': 'Swine',
            'stage_type': 'Nursery',
            'ingredients': [
                {'name': 'Corn, grain', 'ratio': 60.0}
            ]
        }
        result_a = service.create_formula('user_a', formula_data)
        assert result_a.success, "用户 A 创建应该成功"
        
        # 用户 B 不应该能看到用户 A 的配方
        result_b = service.get_formula('user_b', 'User A Formula')
        assert not result_b.success, "用户 B 不应该能看到用户 A 的配方"
        assert result_b.error_code == 'E002', "应该返回不存在错误"
        
        print("  ✅ 用户隔离正确")
        
        # 用户 B 创建同名配方
        formula_data_b = {
            'name': 'User A Formula',  # 同名
            'animal_type': 'Beef Cattle',
            'stage_type': 'Growing',
            'ingredients': [
                {'name': 'Corn, grain', 'ratio': 70.0}
            ]
        }
        result_b_create = service.create_formula('user_b', formula_data_b)
        assert result_b_create.success, "用户 B 应该能创建同名配方"
        
        print("  ✅ 不同用户可以创建同名配方")
        
    finally:
        os.unlink(db_path)


def test_private_priority_over_public():
    """测试私有配方优先于公共配方"""
    print("\n🧪 测试：私有配方优先")
    
    db_path, pool = setup_test_db()
    try:
        service = FormulaService(pool)
        
        # 公共配方 'Nursery Diet 1' 已存在
        # 用户 A 创建同名私有配方
        formula_data = {
            'name': 'Nursery Diet 1',  # 与公共配方同名
            'animal_type': 'Swine',
            'stage_type': 'Nursery',
            'notes': 'Private version',
            'ingredients': [
                {'name': 'Corn, grain', 'ratio': 55.0}  # 不同比例
            ]
        }
        result = service.create_formula('user_a', formula_data)
        assert result.success, "创建私有配方应该成功"
        
        # 用户 A 获取配方时，应该返回私有版本
        result_get = service.get_formula('user_a', 'Nursery Diet 1')
        assert result_get.success, "获取应该成功"
        assert result_get.source == 'private', f"来源应该是 private，实际: {result_get.source}"
        assert result_get.data['notes'] == 'Private version', "应该是私有版本"
        
        print("  ✅ 私有配方优先于公共配方")
        
        # 用户 B 获取同名配方，应该返回公共版本
        result_b = service.get_formula('user_b', 'Nursery Diet 1')
        assert result_b.success, "用户 B 应该能获取公共配方"
        assert result_b.source == 'public', f"用户 B 来源应该是 public，实际: {result_b.source}"
        
        print("  ✅ 其他用户仍然获取公共配方")
        
    finally:
        os.unlink(db_path)


def test_update_formula_with_version():
    """测试乐观锁更新"""
    print("\n🧪 测试：乐观锁更新")
    
    db_path, pool = setup_test_db()
    try:
        service = FormulaService(pool)
        
        # 创建配方
        formula_data = {
            'name': 'Version Test',
            'animal_type': 'Swine',
            'stage_type': 'Nursery',
            'ingredients': [{'name': 'Corn, grain', 'ratio': 60.0}]
        }
        result = service.create_formula('user_a', formula_data)
        assert result.success
        formula_id = result.data['id']
        version = result.data['version']
        
        print(f"  创建版本: {version}")
        
        # 正确版本更新
        update_data = {
            'animal_type': 'Beef Cattle',
            'stage_type': 'Growing',
            'ingredients': [{'name': 'Corn, grain', 'ratio': 65.0}]
        }
        result_update = service.update_formula('user_a', formula_id, update_data, version)
        assert result_update.success, f"更新应该成功: {result_update.error_message}"
        assert result_update.data['version'] == version + 1, "版本应该增加"
        
        print(f"  ✅ 更新成功，新版本: {result_update.data['version']}")
        
        # 旧版本更新应该失败
        result_old = service.update_formula('user_a', formula_id, update_data, version)
        assert not result_old.success, "旧版本更新应该失败"
        assert result_old.error_code == 'E006', f"错误码应该是 E006，实际: {result_old.error_code}"
        
        print("  ✅ 乐观锁正确拦截旧版本更新")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - FormulaService 测试 (TDD)")
    print("=" * 60)
    
    tests = [
        test_get_public_formula,
        test_get_nonexistent_formula,
        test_create_private_formula,
        test_multi_tenant_isolation,
        test_private_priority_over_public,
        test_update_formula_with_version,
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