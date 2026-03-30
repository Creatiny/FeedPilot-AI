"""
FeedSales AI - 多租户隔离测试 (v1.7)

验证不同用户数据隔离
"""

import sys
from pathlib import Path
import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.repository import FormulaRepository


def test_multi_tenant_isolation(test_db):
    """测试多租户数据隔离"""
    print("🧪 测试多租户数据隔离...")
    
    repo = FormulaRepository(test_db)
    
    # 用户 A 创建配方
    formula_a_data = {
        "name": "Test Formula A",
        "stage_type": "Nursery",
        "notes": "User A formula",
        "ingredients": [
            {"name": "Corn", "ratio": 60.0},
            {"name": "Soybean meal", "ratio": 25.0}
        ]
    }
    formula_a_id = repo.create_formula("user_a", formula_a_data)
    assert formula_a_id > 0, "用户 A 创建配方失败"
    print(f"✅ 用户 A 创建配方成功 (ID: {formula_a_id})")
    
    # 用户 B 创建配方（同名）
    formula_b_data = {
        "name": "Test Formula A",
        "stage_type": "Nursery",
        "notes": "User B formula",
        "ingredients": [
            {"name": "Corn", "ratio": 65.0},
            {"name": "Soybean meal", "ratio": 20.0}
        ]
    }
    formula_b_id = repo.create_formula("user_b", formula_b_data)
    assert formula_b_id > 0, "用户 B 创建配方失败"
    print(f"✅ 用户 B 创建配方成功 (ID: {formula_b_id})")
    
    # 用户 A 只能看到自己的配方
    result_a = repo.get_formula("user_a", "Test Formula A")
    assert result_a is not None, "用户 A 获取配方失败"
    assert result_a['notes'] == "User A formula", "用户 A 获取了错误的配方"
    print(f"✅ 用户 A 获取配方成功 (notes: {result_a['notes']})")
    
    # 用户 B 只能看到自己的配方
    result_b = repo.get_formula("user_b", "Test Formula A")
    assert result_b is not None, "用户 B 获取配方失败"
    assert result_b['notes'] == "User B formula", "用户 B 获取了错误的配方"
    print(f"✅ 用户 B 获取配方成功 (notes: {result_b['notes']})")
    
    # 验证数据隔离
    formulas_a = repo.list_formulas("user_a")
    formulas_b = repo.list_formulas("user_b")
    assert len(formulas_a) >= 1, f"用户 A 应该有配方"
    assert len(formulas_b) >= 1, f"用户 B 应该有配方"
    print(f"✅ 数据隔离验证通过")


def test_public_formula_access(test_db):
    """测试公共配方访问"""
    print("\n🧪 测试公共配方访问...")
    
    repo = FormulaRepository(test_db)
    
    # 列出公共配方
    public_formulas = repo.list_formulas("system_public")
    assert len(public_formulas) >= 1, "应该有公共配方"
    print(f"✅ 公共配方列表成功: {len(public_formulas)} 个")