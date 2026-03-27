#!/usr/bin/env python3
"""
FeedSales AI - 多租户隔离测试

验证不同用户数据隔离
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository


def test_multi_tenant_isolation():
    """测试多租户数据隔离"""
    print("🧪 测试多租户数据隔离...")
    
    pool = DatabasePool("data/feed_sales.db")
    repo = FormulaRepository(pool)
    
    # 用户 A 创建配方
    formula_a_data = {
        "name": "保育料",
        "stage_type": "保育",
        "notes": "用户 A 的配方",
        "ingredients": [
            {"name": "玉米", "ratio": 60.0},
            {"name": "豆粕", "ratio": 25.0}
        ]
    }
    formula_a_id = repo.create_formula("user_a", formula_a_data)
    print(f"✅ 用户 A 创建配方成功 (ID: {formula_a_id})")
    
    # 用户 B 创建配方
    formula_b_data = {
        "name": "保育料",
        "stage_type": "保育",
        "notes": "用户 B 的配方",
        "ingredients": [
            {"name": "玉米", "ratio": 65.0},
            {"name": "豆粕", "ratio": 20.0}
        ]
    }
    formula_b_id = repo.create_formula("user_b", formula_b_data)
    print(f"✅ 用户 B 创建配方成功 (ID: {formula_b_id})")
    
    # 用户 A 只能看到自己的配方
    result_a = repo.get_formula("user_a", "保育料")
    assert result_a is not None, "用户 A 获取配方失败"
    assert result_a['notes'] == "用户 A 的配方", "用户 A 获取了错误的配方"
    assert result_a['ingredients'][0]['ratio'] == 60.0, "用户 A 的成分比例错误"
    print(f"✅ 用户 A 获取配方成功 (成分：{result_a['ingredients'][0]['ratio']}% 玉米)")
    
    # 用户 B 只能看到自己的配方
    result_b = repo.get_formula("user_b", "保育料")
    assert result_b is not None, "用户 B 获取配方失败"
    assert result_b['notes'] == "用户 B 的配方", "用户 B 获取了错误的配方"
    assert result_b['ingredients'][0]['ratio'] == 65.0, "用户 B 的成分比例错误"
    print(f"✅ 用户 B 获取配方成功 (成分：{result_b['ingredients'][0]['ratio']}% 玉米)")
    
    # 验证数据隔离
    formulas_a = repo.list_formulas("user_a")
    formulas_b = repo.list_formulas("user_b")
    assert len(formulas_a) == 1, f"用户 A 应该有 1 个配方，实际 {len(formulas_a)} 个"
    assert len(formulas_b) == 1, f"用户 B 应该有 1 个配方，实际 {len(formulas_b)} 个"
    print(f"✅ 数据隔离验证通过 (用户 A: {len(formulas_a)} 个，用户 B: {len(formulas_b)} 个)")
    
    # 清理测试数据
    repo.delete_formula("user_a", formula_a_id)
    repo.delete_formula("user_b", formula_b_id)
    print("✅ 测试数据已清理")
    
    return True


def test_owner_open_id_fallback():
    """测试 owner_open_id 降级策略"""
    print("\n🧪 测试 owner_open_id 降级策略...")
    
    from skills.base_skill import BaseSkill
    
    class MockContext:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    skill = BaseSkill()
    
    # 测试 1: 有 owner_open_id
    context1 = MockContext(_meta={'owner_open_id': 'user_123'})
    context1.get_meta = lambda k: context1._meta.get(k)
    result1 = skill.get_owner_open_id(context1)
    assert result1 == 'user_123', f"应该返回 user_123，实际 {result1}"
    print("✅ 测试 1 通过：从 meta 获取 owner_open_id")
    
    # 测试 2: 降级到 user_id
    context2 = MockContext(user_id='456')
    result2 = skill.get_owner_open_id(context2)
    assert result2 == 'user_456', f"应该返回 user_456，实际 {result2}"
    print("✅ 测试 2 通过：降级到 user_id")
    
    # 测试 3: 使用默认值
    context3 = MockContext()
    result3 = skill.get_owner_open_id(context3)
    assert result3 == 'default_user', f"应该返回 default_user，实际 {result3}"
    print("✅ 测试 3 通过：使用默认值")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - 多租户隔离测试")
    print("=" * 60)
    
    try:
        # 测试多租户隔离
        test_multi_tenant_isolation()
        
        # 测试降级策略
        test_owner_open_id_fallback()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
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
