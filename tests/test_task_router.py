#!/usr/bin/env python3
"""
FeedSales AI - TaskRouter 测试

TDD: 先写测试，再写实现
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.harness.task_router import TaskRouter


def test_classify_formula_cost_query():
    """测试配方成本查询分类"""
    print("\n🧪 测试：配方成本查询分类")
    
    router = TaskRouter()
    
    messages = [
        "计算保育料 1 号的成本",
        "保育料多少钱一吨",
        "查一下育肥料的成本",
        "配方成本计算",
    ]
    
    for msg in messages:
        result = router.classify(msg)
        assert result == 'formula_cost_query', f"'{msg}' 应该分类为 formula_cost_query，实际: {result}"
    
    print("  ✅ 配方成本查询分类正确")


def test_classify_formula_manage():
    """测试配方管理分类"""
    print("\n🧪 测试：配方管理分类")
    
    router = TaskRouter()
    
    messages = [
        "创建一个新配方",
        "修改我的保育料",
        "删除育肥料配方",
        "查看我的所有配方",
        "列出配方",
    ]
    
    for msg in messages:
        result = router.classify(msg)
        assert result == 'formula_manage', f"'{msg}' 应该分类为 formula_manage，实际: {result}"
    
    print("  ✅ 配方管理分类正确")


def test_classify_price_query():
    """测试价格查询分类"""
    print("\n🧪 测试：价格查询分类")
    
    router = TaskRouter()
    
    messages = [
        "今天玉米价格",
        "查询豆粕价格",
        "鱼粉多少钱",
        "原料价格查询",
    ]
    
    for msg in messages:
        result = router.classify(msg)
        assert result == 'price_query', f"'{msg}' 应该分类为 price_query，实际: {result}"
    
    print("  ✅ 价格查询分类正确")


def test_classify_price_manage():
    """测试价格管理分类"""
    print("\n🧪 测试：价格管理分类")
    
    router = TaskRouter()
    
    messages = [
        "设置我的玉米价格 180",
        "更新豆粕价格",
        "我的原料价格列表",
    ]
    
    for msg in messages:
        result = router.classify(msg)
        assert result == 'price_manage', f"'{msg}' 应该分类为 price_manage，实际: {result}"
    
    print("  ✅ 价格管理分类正确")


def test_classify_customer_manage():
    """测试客户管理分类"""
    print("\n🧪 测试：客户管理分类")
    
    router = TaskRouter()
    
    messages = [
        "添加客户张三",
        "创建新客户",
        "查看客户列表",
        "删除客户李四",
    ]
    
    for msg in messages:
        result = router.classify(msg)
        assert result == 'customer_manage', f"'{msg}' 应该分类为 customer_manage，实际: {result}"
    
    print("  ✅ 客户管理分类正确")


def test_classify_quote_generate():
    """测试报价生成分类"""
    print("\n🧪 测试：报价生成分类")
    
    router = TaskRouter()
    
    messages = [
        "给客户张三生成报价",
        "做个报价单",
        "开一份报价",
    ]
    
    for msg in messages:
        result = router.classify(msg)
        assert result == 'quote_generate', f"'{msg}' 应该分类为 quote_generate，实际: {result}"
    
    print("  ✅ 报价生成分类正确")


def test_classify_nutrition_analysis():
    """测试营养分析分类"""
    print("\n🧪 测试：营养分析分类")
    
    router = TaskRouter()
    
    messages = [
        "分析保育料的营养",
        "营养分析",
        "配方营养成分",
    ]
    
    for msg in messages:
        result = router.classify(msg)
        assert result == 'nutrition_analysis', f"'{msg}' 应该分类为 nutrition_analysis，实际: {result}"
    
    print("  ✅ 营养分析分类正确")


def test_classify_unknown():
    """测试未知类型分类"""
    print("\n🧪 测试：未知类型分类")
    
    router = TaskRouter()
    
    messages = [
        "你好",
        "今天天气怎么样",
        "随便聊聊",
    ]
    
    for msg in messages:
        result = router.classify(msg)
        assert result == 'unknown', f"'{msg}' 应该分类为 unknown，实际: {result}"
    
    print("  ✅ 未知类型分类正确")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - TaskRouter 测试 (TDD)")
    print("=" * 60)
    
    tests = [
        test_classify_formula_cost_query,
        test_classify_formula_manage,
        test_classify_price_query,
        test_classify_price_manage,
        test_classify_customer_manage,
        test_classify_quote_generate,
        test_classify_nutrition_analysis,
        test_classify_unknown,
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