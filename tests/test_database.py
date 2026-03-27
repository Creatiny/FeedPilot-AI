#!/usr/bin/env python3
"""
FeedSales AI - 数据库测试脚本

测试 DatabasePool 和 Repository 功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository, PriceRepository


def test_database_pool():
    """测试 DatabasePool"""
    print("🧪 测试 DatabasePool...")
    
    # 使用环境变量配置数据库路径
    import os
    db_path = os.getenv("DATABASE_URL", "data/feed_sales.db")
    pool = DatabasePool(db_path)
    
    # 测试连接
    assert pool.test_connection(), "连接测试失败"
    print("✅ 连接测试通过")
    
    # 测试单例模式
    pool2 = DatabasePool("data/feed_sales.db")
    assert pool is pool2, "单例模式失败"
    print("✅ 单例模式测试通过")
    
    return pool


def test_formula_repository(pool: DatabasePool):
    """测试 FormulaRepository"""
    print("\n🧪 测试 FormulaRepository...")
    
    repo = FormulaRepository(pool)
    test_user = "test_user_001"
    
    # 创建配方
    formula_data = {
        "name": "测试配方 1 号",
        "stage_type": "保育",
        "notes": "测试备注",
        "ingredients": [
            {"name": "玉米", "ratio": 60.0},
            {"name": "豆粕", "ratio": 25.0},
            {"name": "预混料", "ratio": 15.0}
        ]
    }
    
    formula_id = repo.create_formula(test_user, formula_data)
    assert formula_id > 0, "创建配方失败"
    print(f"✅ 创建配方成功 (ID: {formula_id})")
    
    # 获取配方
    formula = repo.get_formula(test_user, "测试配方 1 号")
    assert formula is not None, "获取配方失败"
    assert len(formula['ingredients']) == 3, "成分数量错误"
    print(f"✅ 获取配方成功 ({len(formula['ingredients'])} 个成分)")
    
    # 列出配方
    formulas = repo.list_formulas(test_user)
    assert len(formulas) >= 1, "列出配方失败"
    print(f"✅ 列出配方成功 (共 {len(formulas)} 个)")
    
    # 更新配方
    formula_data['notes'] = "更新备注"
    success = repo.update_formula(test_user, formula_id, formula_data)
    assert success, "更新配方失败"
    print("✅ 更新配方成功")
    
    # 删除配方
    success = repo.delete_formula(test_user, formula_id)
    assert success, "删除配方失败"
    print("✅ 删除配方成功")
    
    return repo


def test_price_repository(pool: DatabasePool):
    """测试 PriceRepository"""
    print("\n🧪 测试 PriceRepository...")
    
    repo = PriceRepository(pool)
    test_user = "test_user_001"
    
    # 保存价格
    price_data = {
        "ingredient_code": "ING_CORN",
        "ingredient_name": "玉米",
        "price": 2800.00,
        "currency": "CNY",
        "unit": "ton",
        "source": "barchart",
        "price_date": "2026-03-27"
    }
    
    price_id = repo.save_price(test_user, price_data)
    assert price_id > 0, "保存价格失败"
    print(f"✅ 保存价格成功 (ID: {price_id})")
    
    # 获取最新价格
    price = repo.get_latest_price(test_user, "ING_CORN")
    assert price is not None, "获取价格失败"
    assert price['price'] == 2800.00, "价格数值错误"
    print(f"✅ 获取价格成功 ({price['price']} 元/吨)")
    
    return repo


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - 数据库测试")
    print("=" * 60)
    
    try:
        # 测试 DatabasePool
        pool = test_database_pool()
        
        # 测试 FormulaRepository
        test_formula_repository(pool)
        
        # 测试 PriceRepository
        test_price_repository(pool)
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败：{e}")
        return False
    except Exception as e:
        print(f"\n❌ 未知错误：{e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
