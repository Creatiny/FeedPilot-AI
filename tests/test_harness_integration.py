#!/usr/bin/env python3
"""
FeedSales AI - Harness 入口集成测试

测试完整的 Harness 工作流
"""

import sys
import tempfile
import os
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.services.formula_service import FormulaService
from src.services.price_service import PriceService
from src.services.customer_service import CustomerService
from src.services.calculation_service import CalculationService
from src.harness.task_router import TaskRouter
from src.harness.session_state import SessionStateManager
from src.harness.result_validator import ResultValidator
from src.harness.harness import FeedSalesHarness


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
    
    # 创建所有表
    cursor.execute('CREATE TABLE users (open_id TEXT PRIMARY KEY)')
    cursor.execute('''
        CREATE TABLE formulas (
            id INTEGER PRIMARY KEY, owner_open_id TEXT, name TEXT,
            animal_type TEXT, stage_type TEXT, notes TEXT,
            UNIQUE(owner_open_id, name)
        )
    ''')
    cursor.execute('''
        CREATE TABLE formula_ingredients (
            id INTEGER PRIMARY KEY, formula_id INTEGER,
            ingredient_name TEXT, ratio_percent REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE ingredient_prices (
            id INTEGER PRIMARY KEY, owner_open_id TEXT, ingredient_code TEXT,
            ingredient_name TEXT, price REAL, currency TEXT DEFAULT 'USD',
            unit TEXT DEFAULT 'ton', source TEXT, price_date DATE,
            UNIQUE(owner_open_id, ingredient_code, price_date)
        )
    ''')
    cursor.execute('''
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY, owner_open_id TEXT, name TEXT,
            company TEXT, phone TEXT, email TEXT, region TEXT, notes TEXT
        )
    ''')
    
    cursor.execute("INSERT INTO users VALUES ('user_a')")
    cursor.execute("INSERT INTO users VALUES ('system_public')")
    
    # 公共配方
    cursor.execute("INSERT INTO formulas VALUES (1, 'system_public', 'Nursery Diet 1', 'Swine', 'Nursery', NULL)")
    cursor.execute("INSERT INTO formula_ingredients VALUES (1, 1, 'Corn, grain', 60.0)")
    cursor.execute("INSERT INTO formula_ingredients VALUES (2, 1, 'Soybean meal, 48%', 25.0)")
    cursor.execute("INSERT INTO formula_ingredients VALUES (3, 1, 'Premix, swine', 15.0)")
    
    # 公共价格
    cursor.execute("INSERT INTO ingredient_prices VALUES (1, 'system_public', 'ING_CORN', 'Corn, grain', 180.0, 'USD', 'ton', 'public', '2026-03-29')")
    cursor.execute("INSERT INTO ingredient_prices VALUES (2, 'system_public', 'ING_SBM', 'Soybean meal, 48%', 350.0, 'USD', 'ton', 'public', '2026-03-29')")
    cursor.execute("INSERT INTO ingredient_prices VALUES (3, 'system_public', 'ING_PREMIX', 'Premix, swine', 450.0, 'USD', 'ton', 'public', '2026-03-29')")
    
    conn.commit()
    conn.close()
    
    return db_path, DatabasePool(db_path)


def test_harness_process_cost_query():
    """测试 Harness 处理成本查询"""
    print("\n🧪 测试：Harness 处理成本查询")
    
    db_path, pool = setup_test_db()
    try:
        harness = FeedSalesHarness(pool)
        
        result = harness.process('session_1', 'user_a', '计算 Nursery Diet 1 的成本')
        
        assert result['success'], f"应该成功: {result.get('error')}"
        assert result['task_type'] == 'formula_cost_query'
        assert 'total_cost' in result['data']
        
        print(f"  ✅ Harness 处理成功，任务类型: {result['task_type']}")
        
    finally:
        os.unlink(db_path)


def test_harness_process_set_price():
    """测试 Harness 处理设置私有价格"""
    print("\n🧪 测试：Harness 处理设置私有价格")
    
    db_path, pool = setup_test_db()
    try:
        harness = FeedSalesHarness(pool)
        
        result = harness.process('session_1', 'user_a', '设置玉米价格 175')
        
        assert result['success']
        assert result['task_type'] == 'price_manage'
        
        print(f"  ✅ 设置成功，任务类型: {result['task_type']}")
        
    finally:
        os.unlink(db_path)


def test_harness_process_add_customer():
    """测试 Harness 处理添加客户"""
    print("\n🧪 测试：Harness 处理添加客户")
    
    db_path, pool = setup_test_db()
    try:
        harness = FeedSalesHarness(pool)
        
        result = harness.process('session_1', 'user_a', '添加客户张三，电话 123456')
        
        assert result['success']
        assert result['task_type'] == 'customer_manage'
        
        print(f"  ✅ 添加成功，任务类型: {result['task_type']}")
        
    finally:
        os.unlink(db_path)


def test_harness_session_state():
    """测试 Harness 会话状态"""
    print("\n🧪 测试：Harness 会话状态")
    
    db_path, pool = setup_test_db()
    try:
        harness = FeedSalesHarness(pool)
        
        # 第一次请求
        harness.process('session_1', 'user_a', '计算 Nursery Diet 1 成本')
        
        # 检查会话状态
        state = harness.get_session_state('session_1')
        assert state.user_id == 'user_a'
        assert state.conversation_turn == 1
        
        # 第二次请求
        harness.process('session_1', 'user_a', '玉米价格')
        
        state = harness.get_session_state('session_1')
        assert state.conversation_turn == 2
        
        print(f"  ✅ 会话状态正确，轮次: {state.conversation_turn}")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - Harness 集成测试")
    print("=" * 60)
    
    tests = [
        test_harness_process_cost_query,
        test_harness_process_set_price,
        test_harness_process_add_customer,
        test_harness_session_state,
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