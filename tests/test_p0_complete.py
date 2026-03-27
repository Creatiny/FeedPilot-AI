#!/usr/bin/env python3
"""
FeedSales AI - P0 完成全面测试

测试所有 P0 任务的功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository, PriceRepository


def test_database_pool():
    """测试 T03: DatabasePool"""
    print("\n🧪 测试 T03: DatabasePool...")
    
    pool = DatabasePool("data/feed_sales.db")
    
    # 测试连接
    assert pool.test_connection(), "连接测试失败"
    print("  ✅ 连接测试通过")
    
    # 测试单例模式
    pool2 = DatabasePool("data/feed_sales.db")
    assert pool is pool2, "单例模式失败"
    print("  ✅ 单例模式测试通过")
    
    return pool


def test_repository(pool: DatabasePool):
    """测试 T04: Repository"""
    print("\n🧪 测试 T04: Repository...")
    
    formula_repo = FormulaRepository(pool)
    price_repo = PriceRepository(pool)
    test_user = "test_p0_user"
    
    # 创建配方
    formula_data = {
        "name": "P0 测试配方",
        "stage_type": "保育",
        "notes": "P0 测试",
        "ingredients": [
            {"name": "玉米", "ratio": 60.0},
            {"name": "豆粕", "ratio": 25.0}
        ]
    }
    formula_id = formula_repo.create_formula(test_user, formula_data)
    assert formula_id > 0, "创建配方失败"
    print(f"  ✅ 创建配方成功 (ID: {formula_id})")
    
    # 获取配方
    formula = formula_repo.get_formula(test_user, "P0 测试配方")
    assert formula is not None, "获取配方失败"
    assert len(formula['ingredients']) == 2, "成分数量错误"
    print(f"  ✅ 获取配方成功 ({len(formula['ingredients'])} 个成分)")
    
    # 保存价格
    price_data = {
        "ingredient_code": "ING_CORN",
        "ingredient_name": "玉米",
        "price": 2800.00,
        "currency": "CNY",
        "unit": "ton",
        "source": "test",
        "price_date": "2026-03-27"
    }
    price_id = price_repo.save_price(test_user, price_data)
    assert price_id > 0, "保存价格失败"
    print(f"  ✅ 保存价格成功 (ID: {price_id})")
    
    # 获取价格
    price = price_repo.get_latest_price(test_user, "ING_CORN")
    assert price is not None, "获取价格失败"
    assert price['price'] == 2800.00, "价格数值错误"
    print(f"  ✅ 获取价格成功 ({price['price']} 元/吨)")
    
    # 清理
    formula_repo.delete_formula(test_user, formula_id)
    print("  ✅ 测试数据已清理")
    
    return True


def test_multi_tenant():
    """测试 T06: 多租户隔离"""
    print("\n🧪 测试 T06: 多租户隔离...")
    
    pool = DatabasePool("data/feed_sales.db")
    repo = FormulaRepository(pool)
    
    # 用户 A 创建配方
    formula_a = repo.create_formula("user_a", {
        "name": "隔离测试",
        "stage_type": "保育",
        "ingredients": [{"name": "玉米", "ratio": 60.0}]
    })
    
    # 用户 B 创建配方
    formula_b = repo.create_formula("user_b", {
        "name": "隔离测试",
        "stage_type": "保育",
        "ingredients": [{"name": "玉米", "ratio": 70.0}]
    })
    
    # 验证隔离
    result_a = repo.get_formula("user_a", "隔离测试")
    result_b = repo.get_formula("user_b", "隔离测试")
    
    assert result_a['ingredients'][0]['ratio'] == 60.0, "用户 A 数据错误"
    assert result_b['ingredients'][0]['ratio'] == 70.0, "用户 B 数据错误"
    print("  ✅ 数据隔离验证通过")
    
    # 清理
    repo.delete_formula("user_a", formula_a)
    repo.delete_formula("user_b", formula_b)
    
    return True


def test_skill_metadata():
    """测试 T07-T08: SKILL.md 配置"""
    print("\n🧪 测试 T07-T08: SKILL.md 配置...")
    
    skills_dir = Path("skills")
    required_skills = [
        "formula_cost_skill",
        "price_lookup_skill",
        "customer_record_skill",
        "nutrition_analysis_skill"
    ]
    
    for skill_name in required_skills:
        skill_path = skills_dir / skill_name / "SKILL.md"
        assert skill_path.exists(), f"技能不存在：{skill_name}"
        
        # 读取 frontmatter
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "name:" in content, f"{skill_name} 缺少 name"
            assert "description:" in content, f"{skill_name} 缺少 description"
        
        print(f"  ✅ {skill_name} 配置正确")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - P0 完成全面测试")
    print("=" * 60)
    
    try:
        # T03
        pool = test_database_pool()
        
        # T04
        test_repository(pool)
        
        # T06
        test_multi_tenant()
        
        # T07-T08
        test_skill_metadata()
        
        print("\n" + "=" * 60)
        print("✅ 所有 P0 测试通过！")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败：{e}")
        return False
    except Exception as e:
        print(f"\n❌ 未知错误：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
