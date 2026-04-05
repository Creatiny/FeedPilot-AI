#!/usr/bin/env python3
"""
FeedSales AI - ResultValidator 测试

TDD: 先写测试，再写实现
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.harness.result_validator import ResultValidator, ValidationResult


def test_validate_cost_result_success():
    """测试验证成功的成本结果"""
    print("\n🧪 测试：验证成功的成本结果")
    
    validator = ResultValidator()
    
    result = {
        'total_cost': 263.00,
        'details': [
            {'name': 'Corn', 'cost': 108.00, 'price_source': 'public'},
            {'name': 'Soybean', 'cost': 87.50, 'price_source': 'public'},
            {'name': 'Premix', 'cost': 67.50, 'price_source': 'public'},
        ]
    }
    
    validation = validator.validate_cost_result(result)
    
    assert validation.valid, f"应该通过验证: {validation.errors}"
    assert len(validation.errors) == 0, "不应该有错误"
    
    print("  ✅ 成本结果验证通过")


def test_validate_cost_result_negative():
    """测试验证负数成本"""
    print("\n🧪 测试：验证负数成本")
    
    validator = ResultValidator()
    
    result = {
        'total_cost': -100.00,
        'details': []
    }
    
    validation = validator.validate_cost_result(result)
    
    assert not validation.valid, "应该不通过验证"
    assert any('必须大于 0' in e for e in validation.errors), "应该提示成本必须大于 0"
    
    print("  ✅ 正确拦截负数成本")


def test_validate_cost_result_mismatch():
    """测试验证明细和与总成本不匹配"""
    print("\n🧪 测试：验证明细和与总成本不匹配")
    
    validator = ResultValidator()
    
    result = {
        'total_cost': 300.00,  # 明细和 = 263，不匹配
        'details': [
            {'name': 'Corn', 'cost': 108.00, 'price_source': 'public'},
            {'name': 'Soybean', 'cost': 87.50, 'price_source': 'public'},
            {'name': 'Premix', 'cost': 67.50, 'price_source': 'public'},
        ]
    }
    
    validation = validator.validate_cost_result(result)
    
    assert not validation.valid, "应该不通过验证"
    assert any('不等于' in e for e in validation.errors), "应该提示明细和与总成本不一致"
    
    print("  ✅ 正确拦截明细和与总成本不匹配")


def test_validate_cost_result_missing_source():
    """测试验证缺失价格来源"""
    print("\n🧪 测试：验证缺失价格来源")
    
    validator = ResultValidator()
    
    result = {
        'total_cost': 100.00,
        'details': [
            {'name': 'Corn', 'cost': 100.00},  # 缺少 price_source
        ]
    }
    
    validation = validator.validate_cost_result(result)
    
    assert not validation.valid, "应该不通过验证"
    assert any('价格来源' in e for e in validation.errors), "应该提示缺失价格来源"
    
    print("  ✅ 正确拦截缺失价格来源")


def test_validate_formula_success():
    """测试验证成功的配方"""
    print("\n🧪 测试：验证成功的配方")
    
    validator = ResultValidator()
    
    formula = {
        'name': 'Test Formula',
        'ingredients': [
            {'name': 'Corn', 'ratio': 60.0},
            {'name': 'Soybean', 'ratio': 25.0},
            {'name': 'Premix', 'ratio': 15.0},
        ]
    }
    
    validation = validator.validate_formula(formula)
    
    assert validation.valid, f"应该通过验证: {validation.errors}"
    
    print("  ✅ 配方验证通过")


def test_validate_formula_ratio_not_100():
    """测试验证成分比例不等于 100%"""
    print("\n🧪 测试：验证成分比例不等于 100%")
    
    validator = ResultValidator()
    
    formula = {
        'name': 'Test Formula',
        'ingredients': [
            {'name': 'Corn', 'ratio': 50.0},
            {'name': 'Soybean', 'ratio': 30.0},
            # 总和 = 80%，不等于 100%
        ]
    }
    
    validation = validator.validate_formula(formula)
    
    assert not validation.valid, "应该不通过验证"
    assert any('100%' in e for e in validation.errors), "应该提示比例不等于 100%"
    
    print("  ✅ 正确拦截比例不等于 100%")


def test_validate_customer_success():
    """测试验证成功的客户"""
    print("\n🧪 测试：验证成功的客户")
    
    validator = ResultValidator()
    
    customer = {
        'name': 'John Smith',
        'phone': '555-1234',
    }
    
    validation = validator.validate_customer(customer)
    
    assert validation.valid, f"应该通过验证: {validation.errors}"
    
    print("  ✅ 客户验证通过")


def test_validate_customer_missing_name():
    """测试验证缺失客户名称"""
    print("\n🧪 测试：验证缺失客户名称")
    
    validator = ResultValidator()
    
    customer = {
        'phone': '555-1234',
        # 缺少 name
    }
    
    validation = validator.validate_customer(customer)
    
    assert not validation.valid, "应该不通过验证"
    assert any('名称' in e for e in validation.errors), "应该提示缺失名称"
    
    print("  ✅ 正确拦截缺失客户名称")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - ResultValidator 测试 (TDD)")
    print("=" * 60)
    
    tests = [
        test_validate_cost_result_success,
        test_validate_cost_result_negative,
        test_validate_cost_result_mismatch,
        test_validate_cost_result_missing_source,
        test_validate_formula_success,
        test_validate_formula_ratio_not_100,
        test_validate_customer_success,
        test_validate_customer_missing_name,
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