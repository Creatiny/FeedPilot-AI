#!/usr/bin/env python3
"""
FeedSales AI - 集成测试

测试完整的工作流程
"""

import sys
from pathlib import Path
import time

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository, PriceRepository
from src.integrations.barchart_api import BarchartAPIClient
from src.utils.error_handler import handle_errors, validate_input
from src.utils.rate_limiter import RateLimiter


class TestWorkflow:
    """集成测试工作流"""
    
    def __init__(self):
        """初始化测试环境"""
        self.pool = DatabasePool("data/feed_sales.db")
        self.formula_repo = FormulaRepository(self.pool)
        self.price_repo = PriceRepository(self.pool)
        self.barchart = BarchartAPIClient()
        self.test_user = "integration_test_user"
    
    def setup(self):
        """设置测试数据"""
        print("📦 设置测试数据...")
        
        # 创建测试配方
        self.formula_repo.create_formula(self.test_user, {
            "name": "集成测试配方",
            "stage_type": "保育",
            "notes": "集成测试",
            "ingredients": [
                {"name": "玉米", "ratio": 60.0},
                {"name": "豆粕", "ratio": 25.0},
                {"name": "预混料", "ratio": 15.0}
            ]
        })
        
        # 创建测试价格
        for ingredient in ["玉米", "豆粕", "预混料"]:
            self.price_repo.save_price(self.test_user, {
                "ingredient_code": f"ING_{ingredient}",
                "ingredient_name": ingredient,
                "price": 3000.00,
                "currency": "CNY",
                "unit": "ton",
                "source": "test",
                "price_date": "2026-03-27"
            })
        
        print("  ✅ 测试数据设置完成")
    
    def teardown(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        # 删除测试配方
        formula = self.formula_repo.get_formula(self.test_user, "集成测试配方")
        if formula:
            self.formula_repo.delete_formula(self.test_user, formula['id'])
        
        print("  ✅ 测试数据清理完成")
    
    @handle_errors(default_return=False)
    def test_formula_cost_workflow(self):
        """测试配方成本计算工作流"""
        print("\n🧪 测试工作流 1: 配方成本计算")
        
        # 1. 获取配方
        formula = self.formula_repo.get_formula(self.test_user, "集成测试配方")
        assert formula is not None, "获取配方失败"
        print(f"  ✅ 获取配方成功：{formula['name']}")
        
        # 2. 获取原料价格
        total_cost = 0.0
        for ingredient in formula['ingredients']:
            price_data = self.price_repo.get_latest_price(
                self.test_user,
                f"ING_{ingredient['name']}"
            )
            if price_data:
                cost = price_data['price'] * ingredient['ratio'] / 100.0
                total_cost += cost
                print(f"    - {ingredient['name']}: ¥{price_data['price']}/吨 × {ingredient['ratio']}% = ¥{cost:.2f}")
        
        # 3. 计算总成本
        assert total_cost > 0, "成本计算失败"
        print(f"  ✅ 成本计算成功：¥{total_cost:.2f}/吨")
        
        return True
    
    @handle_errors(default_return=False)
    def test_multi_tenant_workflow(self):
        """测试多租户隔离工作流"""
        print("\n🧪 测试工作流 2: 多租户隔离")
        
        # 创建两个用户的配方
        user_a = "user_a_integration"
        user_b = "user_b_integration"
        
        # 用户 A 创建配方
        formula_a_id = self.formula_repo.create_formula(user_a, {
            "name": "隔离测试配方",
            "stage_type": "保育",
            "ingredients": [{"name": "玉米", "ratio": 60.0}]
        })
        
        # 用户 B 创建配方
        formula_b_id = self.formula_repo.create_formula(user_b, {
            "name": "隔离测试配方",
            "stage_type": "保育",
            "ingredients": [{"name": "玉米", "ratio": 70.0}]
        })
        
        # 验证隔离
        result_a = self.formula_repo.get_formula(user_a, "隔离测试配方")
        result_b = self.formula_repo.get_formula(user_b, "隔离测试配方")
        
        assert result_a['ingredients'][0]['ratio'] == 60.0, "用户 A 数据错误"
        assert result_b['ingredients'][0]['ratio'] == 70.0, "用户 B 数据错误"
        
        print(f"  ✅ 用户 A 配方：{result_a['ingredients'][0]['ratio']}% 玉米")
        print(f"  ✅ 用户 B 配方：{result_b['ingredients'][0]['ratio']}% 玉米")
        print(f"  ✅ 数据隔离验证通过")
        
        # 清理
        self.formula_repo.delete_formula(user_a, formula_a_id)
        self.formula_repo.delete_formula(user_b, formula_b_id)
        
        return True
    
    @handle_errors(default_return=False)
    def test_rate_limit_workflow(self):
        """测试限流工作流"""
        print("\n🧪 测试工作流 3: API 限流")
        
        limiter = RateLimiter(max_calls=3, period=5.0)
        
        # 模拟 API 调用
        call_count = 0
        for i in range(5):
            if limiter.is_allowed():
                limiter.record_call()
                call_count += 1
                print(f"  ✅ 调用 {i+1} 成功")
            else:
                print(f"  ⏸️ 调用 {i+1} 被限流")
        
        assert call_count == 3, f"限流失效：{call_count} 次"
        print(f"  ✅ 限流器工作正常 (允许 {call_count}/5 次)")
        
        return True
    
    @handle_errors(default_return=False)
    def test_error_handling_workflow(self):
        """测试错误处理工作流"""
        print("\n🧪 测试工作流 4: 错误处理")
        
        # 测试数据库错误处理
        try:
            # 尝试获取不存在的配方
            formula = self.formula_repo.get_formula("nonexistent_user", "nonexistent_formula")
            assert formula is None, "应该返回 None"
            print(f"  ✅ 不存在的数据返回 None")
        except Exception as e:
            print(f"  ❌ 未处理的异常：{e}")
            return False
        
        # 测试输入验证
        @validate_input(["formula_name"])
        def get_formula_cost(formula_name):
            return f"成本：{formula_name}"
        
        try:
            result = get_formula_cost(formula_name="测试配方")
            print(f"  ✅ 输入验证通过：{result}")
        except Exception as e:
            print(f"  ❌ 输入验证失败：{e}")
            return False
        
        return True
    
    def run_all_tests(self):
        """运行所有集成测试"""
        print("=" * 60)
        print("FeedSales AI - 集成测试")
        print("=" * 60)
        
        try:
            # 设置测试数据
            self.setup()
            
            # 运行测试
            tests = [
                ("配方成本计算", self.test_formula_cost_workflow),
                ("多租户隔离", self.test_multi_tenant_workflow),
                ("API 限流", self.test_rate_limit_workflow),
                ("错误处理", self.test_error_handling_workflow),
            ]
            
            results = []
            for name, test_func in tests:
                result = test_func()
                results.append((name, result))
            
            # 清理测试数据
            self.teardown()
            
            # 汇总结果
            print("\n" + "=" * 60)
            print("集成测试结果汇总")
            print("=" * 60)
            
            passed = sum(1 for _, r in results if r)
            total = len(results)
            
            for name, result in results:
                status = "✅ 通过" if result else "❌ 失败"
                print(f"  {status}: {name}")
            
            print(f"\n总计：{passed}/{total} 通过")
            
            if passed == total:
                print("\n✅ 所有集成测试通过！")
                return True
            else:
                print(f"\n❌ {total - passed} 个测试失败")
                return False
                
        except Exception as e:
            print(f"\n❌ 集成测试异常：{e}")
            import traceback
            traceback.print_exc()
            self.teardown()
            return False


def main():
    """主函数"""
    workflow = TestWorkflow()
    success = workflow.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
