#!/usr/bin/env python3
"""
FeedSales AI - P1 任务测试

测试 Barchart API、错误处理、限流器
"""

import sys
from pathlib import Path
import time

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.barchart_api import BarchartAPIClient
from src.utils.error_handler import handle_errors, validate_input, retry_on_failure, log_execution_time
from src.utils.rate_limiter import RateLimiter, PredefinedLimiters


def test_barchart_api():
    """测试 T11: Barchart API"""
    print("\n🧪 测试 T11: Barchart API...")
    
    client = BarchartAPIClient()
    
    # 测试配置检查
    import os
    if not os.getenv("BARCHART_API_KEY"):
        print("  ⚠️ BARCHART_API_KEY 未配置，跳过 API 测试")
        print("  ✅ 客户端初始化成功")
        return True
    
    # 测试连接
    if client.test_connection():
        print("  ✅ API 连接成功")
    else:
        print("  ❌ API 连接失败")
        return False
    
    # 测试获取价格
    corn_price = client.get_commodity_price("ZC")
    if corn_price:
        print(f"  ✅ 获取玉米价格成功：${corn_price['price']}")
    else:
        print("  ❌ 获取价格失败")
        return False
    
    # 测试单位转换
    price_cny = client.convert_to_cny_ton(5.0, "玉米")
    if price_cny > 0:
        print(f"  ✅ 单位转换成功：¥{price_cny}/吨")
    else:
        print("  ❌ 单位转换失败")
        return False
    
    return True


def test_error_handler():
    """测试 T13: 错误处理装饰器"""
    print("\n🧪 测试 T13: 错误处理装饰器...")
    
    # 测试 handle_errors
    @handle_errors(default_return={"error": "失败"})
    def success_func():
        return {"success": True}
    
    @handle_errors(default_return={"error": "失败"})
    def fail_func():
        raise ValueError("测试错误")
    
    result1 = success_func()
    assert result1["success"] == True, "成功情况失败"
    print("  ✅ handle_errors 成功情况测试通过")
    
    result2 = fail_func()
    assert "error" in result2, "失败情况未返回错误"
    print("  ✅ handle_errors 失败情况测试通过")
    
    # 测试 validate_input
    @validate_input(["name", "value"])
    def validated_func(name, value):
        return f"{name}: {value}"
    
    result3 = validated_func(name="test", value=123)
    assert result3 == "test: 123", "输入验证通过但结果错误"
    print("  ✅ validate_input 成功情况测试通过")
    
    try:
        validated_func(name="test")  # 缺少 value
        print("  ❌ validate_input 未捕获缺失字段")
        return False
    except ValueError:
        print("  ✅ validate_input 缺失字段测试通过")
    
    # 测试 retry_on_failure
    attempt_count = 0
    
    @retry_on_failure(max_attempts=3, delay=0.1)
    def retry_func():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError("临时错误")
        return "成功"
    
    result4 = retry_func()
    assert result4 == "成功", "重试失败"
    assert attempt_count == 3, f"重试次数错误：{attempt_count}"
    print(f"  ✅ retry_on_failure 测试通过 (重试 {attempt_count} 次)")
    
    # 测试 log_execution_time
    @log_execution_time()
    def slow_func():
        time.sleep(0.1)
        return "完成"
    
    result5 = slow_func()
    assert result5 == "完成", "执行时间测试失败"
    print("  ✅ log_execution_time 测试通过")
    
    return True


def test_rate_limiter():
    """测试 T14: Rate Limiter"""
    print("\n🧪 测试 T14: Rate Limiter...")
    
    # 创建限流器：3 秒内最多 2 次
    limiter = RateLimiter(max_calls=2, period=3.0)
    
    # 测试 is_allowed
    assert limiter.is_allowed() == True, "首次调用应该允许"
    limiter.record_call()
    assert limiter.is_allowed() == True, "第二次调用应该允许"
    limiter.record_call()
    assert limiter.is_allowed() == False, "第三次调用应该被限流"
    print("  ✅ is_allowed 和 record_call 测试通过")
    
    # 测试 get_remaining_calls
    remaining = limiter.get_remaining_calls()
    assert remaining == 0, f"剩余次数错误：{remaining}"
    print(f"  ✅ get_remaining_calls 测试通过 (剩余 {remaining} 次)")
    
    # 测试 wait_if_needed
    time.sleep(3.5)  # 等待限流重置
    assert limiter.wait_if_needed(timeout=1.0) == True, "等待后应该允许调用"
    print("  ✅ wait_if_needed 测试通过")
    
    # 测试 limit 装饰器
    call_count = 0
    
    @limiter.limit(key="test_decorator", timeout=1.0)
    def decorated_func():
        nonlocal call_count
        call_count += 1
        return "调用成功"
    
    # 重置限流器
    limiter.calls["test_decorator"] = []
    
    result = decorated_func()
    assert result == "调用成功", "装饰器调用失败"
    assert call_count == 1, f"调用次数错误：{call_count}"
    print("  ✅ limit 装饰器测试通过")
    
    # 测试预定义限流器
    assert PredefinedLimiters.barchart.max_calls == 100, "Barchart 限流器配置错误"
    assert PredefinedLimiters.dashscope.max_calls == 1000, "DashScope 限流器配置错误"
    print("  ✅ 预定义限流器测试通过")
    
    return True


def run_all_tests():
    """运行所有 P1 测试"""
    print("=" * 60)
    print("FeedSales AI - P1 任务测试")
    print("=" * 60)
    
    tests = [
        ("T11: Barchart API", test_barchart_api),
        ("T13: 错误处理", test_error_handler),
        ("T14: 限流器", test_rate_limiter),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试异常：{e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n✅ 所有 P1 测试通过！")
        return True
    else:
        print(f"\n❌ {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
