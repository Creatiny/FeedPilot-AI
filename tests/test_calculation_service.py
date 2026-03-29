#!/usr/bin/env python3
"""
FeedSales AI - CalculationService 测试

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
from src.services.calculation_service import CalculationService, ServiceResult


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
            FOREIGN KEY (owner_open_id) REFERENCES users(open_id),
            UNIQUE(owner_open_id, name)
        )
    ''')
    
    # 创建成分表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formula_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            ratio_percent REAL NOT NULL,
            FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
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
    cursor.execute("INSERT INTO users (open_id) VALUES (?)", ('system_public',))
    
    # 插入公共配方
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
    
    # 插入公共价格
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
    
    pool = DatabasePool(db_path)
    return db_path, pool


def test_calculate_cost_public():
    """测试计算公共配方成本"""
    print("\n🧪 测试：计算公共配方成本")
    
    db_path, pool = setup_test_db()
    try:
        service = CalculationService(pool)
        
        result = service.calculate_cost('user_a', 'Nursery Diet 1')
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        assert 'total_cost' in result.data, "应该返回总成本"
        assert 'details' in result.data, "应该返回明细"
        assert result.data['formula_source'] == 'public', f"配方来源应该是 public，实际: {result.data['formula_source']}"
        
        # 计算预期成本
        # Corn: 180 * 60% = 108
        # Soybean: 350 * 25% = 87.5
        # Premix: 450 * 15% = 67.5
        # Total: 263.0
        expected = 108.0 + 87.5 + 67.5
        assert abs(result.data['total_cost'] - expected) < 0.01, f"成本计算错误: {result.data['total_cost']} != {expected}"
        
        print(f"  ✅ 成本计算正确: ${result.data['total_cost']:.2f}/ton")
        print(f"  ✅ 配方来源: {result.data['formula_source']}")
        
    finally:
        os.unlink(db_path)


def test_calculate_cost_with_private_price():
    """测试使用私有价格计算成本"""
    print("\n🧪 测试：使用私有价格计算成本")
    
    db_path, pool = setup_test_db()
    try:
        service = CalculationService(pool)
        
        # 设置私有价格
        from src.services.price_service import PriceService
        price_service = PriceService(pool)
        price_service.set_private_price('user_a', 'Corn, grain', 175.00)
        
        # 计算成本
        result = service.calculate_cost('user_a', 'Nursery Diet 1')
        
        assert result.success, f"应该成功，但返回: {result.error_message}"
        
        # 检查价格来源
        corn_detail = next((d for d in result.data['details'] if 'Corn' in d['name']), None)
        assert corn_detail is not None, "应该有玉米明细"
        assert corn_detail['price_source'] == 'private', f"玉米价格来源应该是 private，实际: {corn_detail['price_source']}"
        
        print(f"  ✅ 私有价格优先使用")
        print(f"  ✅ 价格来源标记正确: {corn_detail['price_source']}")
        
    finally:
        os.unlink(db_path)


def test_calculate_cost_missing_price():
    """测试缺少价格时计算成本"""
    print("\n🧪 测试：缺少价格时计算成本")
    
    db_path, pool = setup_test_db()
    try:
        import sqlite3
        # 添加一个没有价格的成分
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM formulas WHERE name = 'Nursery Diet 1'")
        formula_id = cursor.fetchone()[0]
        cursor.execute('''
            INSERT INTO formula_ingredients (formula_id, ingredient_name, ratio_percent)
            VALUES (?, ?, ?)
        ''', (formula_id, 'New Ingredient', 5.0))
        conn.commit()
        conn.close()
        
        pool = DatabasePool(db_path)
        service = CalculationService(pool)
        
        result = service.calculate_cost('user_a', 'Nursery Diet 1')
        
        assert result.success, "应该成功（使用默认价格）"
        assert 'missing_prices' in result.data, "应该标记缺失价格"
        assert 'New Ingredient' in result.data['missing_prices'], "New Ingredient 应该在缺失列表中"
        
        print("  ✅ 正确标记缺失价格")
        print(f"  ✅ 缺失: {result.data['missing_prices']}")
        
    finally:
        os.unlink(db_path)


def test_calculate_cost_nonexistent_formula():
    """测试计算不存在的配方成本"""
    print("\n🧪 测试：计算不存在的配方成本")
    
    db_path, pool = setup_test_db()
    try:
        service = CalculationService(pool)
        
        result = service.calculate_cost('user_a', 'Nonexistent Formula')
        
        assert not result.success, "应该失败"
        assert result.error_code == 'E002', f"错误码应该是 E002，实际: {result.error_code}"
        
        print("  ✅ 正确返回 E002 错误")
        
    finally:
        os.unlink(db_path)


def test_price_sources_summary():
    """测试价格来源汇总"""
    print("\n🧪 测试：价格来源汇总")
    
    db_path, pool = setup_test_db()
    try:
        service = CalculationService(pool)
        
        # 设置部分私有价格
        from src.services.price_service import PriceService
        price_service = PriceService(pool)
        price_service.set_private_price('user_a', 'Corn, grain', 175.00)
        
        result = service.calculate_cost('user_a', 'Nursery Diet 1')
        
        assert result.success
        assert 'price_sources' in result.data, "应该有价格来源汇总"
        
        sources = result.data['price_sources']
        assert 'Corn, grain' in sources, "应该有玉米价格来源"
        assert sources['Corn, grain'] == 'private', f"玉米来源应该是 private，实际: {sources['Corn, grain']}"
        assert sources['Soybean meal, 48%'] == 'public', f"豆粕来源应该是 public，实际: {sources['Soybean meal, 48%']}"
        
        print("  ✅ 价格来源汇总正确")
        print(f"  ✅ 来源: {sources}")
        
    finally:
        os.unlink(db_path)


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - CalculationService 测试 (TDD)")
    print("=" * 60)
    
    tests = [
        test_calculate_cost_public,
        test_calculate_cost_with_private_price,
        test_calculate_cost_missing_price,
        test_calculate_cost_nonexistent_formula,
        test_price_sources_summary,
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