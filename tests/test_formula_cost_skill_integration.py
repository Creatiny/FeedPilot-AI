#!/usr/bin/env python3
"""
FeedSales AI - FormulaCostSkill 集成测试

测试技能走 CalculationService 统一接口
"""

import sys
import tempfile
import os
import threading
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.services.calculation_service import CalculationService
from skills.formula_cost_skill.skill import FormulaCostSkill


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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            open_id TEXT PRIMARY KEY
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_open_id TEXT NOT NULL,
            name TEXT NOT NULL,
            animal_type TEXT,
            stage_type TEXT NOT NULL,
            notes TEXT,
            UNIQUE(owner_open_id, name)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formula_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            ratio_percent REAL NOT NULL
        )
    ''')
    
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
            UNIQUE(owner_open_id, ingredient_code, price_date)
        )
    ''')
    
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('user_a',))
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('system_public',))
    
    cursor.execute('''
        INSERT INTO formulas (owner_open_id, name, animal_type, stage_type)
        VALUES (?, ?, ?, ?)
    ''', ('system_public', 'Nursery Diet 1', 'Swine', 'Nursery'))
    formula_id = cursor.lastrowid
    
    cursor.execute('''
        INSERT INTO formula_ingredients (formula_id, ingredient_name, ratio_percent)
        VALUES (?, ?, ?)
    ''', (formula_id, 'Corn, grain', 60.0))
    cursor.execute('''
        INSERT INTO formula_ingredients (formula_id, ingredient_name, ratio_percent)
        VALUES (?, ?, ?)
    ''', (formula_id, 'Soybean meal, 48%', 25.0))
    cursor.execute('''
        INSERT INTO formula_ingredients (formula_id, ingredient_name, ratio_percent)
        VALUES (?, ?, ?)
    ''', (formula_id, 'Premix, swine', 15.0))
    
    cursor.execute('''
        INSERT INTO ingredient_prices (owner_open_id, ingredient_code, ingredient_name, price, price_date)
        VALUES (?, ?, ?, ?, ?)
    ''', ('system_public', 'ING_CORN', 'Corn, grain', 180.00, '2026-03-29'))
    cursor.execute('''
        INSERT INTO ingredient_prices (owner_open_id, ingredient_code, ingredient_name, price, price_date)
        VALUES (?, ?, ?, ?, ?)
    ''', ('system_public', 'ING_SBM', 'Soybean meal, 48%', 350.00, '2026-03-29'))
    cursor.execute('''
        INSERT INTO ingredient_prices (owner_open_id, ingredient_code, ingredient_name, price, price_date)
        VALUES (?, ?, ?, ?, ?)
    ''', ('system_public', 'ING_PREMIX', 'Premix, swine', 450.00, '2026-03-29'))
    
    conn.commit()
    conn.close()
    
    return db_path, DatabasePool(db_path)


def test_skill_execute_with_service():
    """测试技能使用 CalculationService"""
    print("\n🧪 测试：技能使用 CalculationService")
    
    db_path, pool = setup_test_db()
    try:
        # 创建服务
        calc_service = CalculationService(pool)
        
        # 创建技能（注入服务）- v1.7 API: calculation_service=
        skill = FormulaCostSkill(calculation_service=calc_service)
        
        # 执行技能
        import asyncio
        result = asyncio.run(skill.execute('user_a', 'Nursery Diet 1成本'))
        
        assert result['success'], f"应该成功: {result.get('error', result.get('error_message'))}"
        assert 'data' in result, "应该返回数据"
        assert 'cost_per_ton' in result['data'], "应该返回每吨成本"
        assert result['data']['cost_per_ton'] > 0, "成本应该大于 0"
        
        print(f"  ✅ 技能执行成功，成本: ${result['data']['cost_per_ton']:.2f}/ton")
        
    finally:
        os.unlink(db_path)


def test_skill_returns_price_sources():
    """测试技能返回价格来源"""
    print("\n🧪 测试：技能返回价格来源")
    
    db_path, pool = setup_test_db()
    try:
        calc_service = CalculationService(pool)
        skill = FormulaCostSkill(calculation_service=calc_service)
        
        import asyncio
        result = asyncio.run(skill.execute('user_a', 'Nursery Diet 1 成本'))
        
        assert result['success']
        assert 'price_sources' in result['data'], "应该返回价格来源"
        
        sources = result['data']['price_sources']
        print(f"  ✅ 价格来源: {sources}")
        
    finally:
        os.unlink(db_path)


def test_skill_handles_missing_formula():
    """测试技能处理不存在的配方"""
    print("\n🧪 测试：技能处理不存在的配方")
    
    db_path, pool = setup_test_db()
    try:
        calc_service = CalculationService(pool)
        skill = FormulaCostSkill(calculation_service=calc_service)
        
        import asyncio
        result = asyncio.run(skill.execute('user_a', '计算不存在的配方成本'))
        
        assert not result['success'], "应该失败"
        assert result.get('error'), "应该返回错误信息"
        
        print("  ✅ 正确处理不存在的配方")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - FormulaCostSkill 集成测试")
    print("=" * 60)
    
    tests = [
        test_skill_execute_with_service,
        test_skill_returns_price_sources,
        test_skill_handles_missing_formula,
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