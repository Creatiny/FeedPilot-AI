#!/usr/bin/env python3
"""
FeedSales AI - 性能测试

测试数据库性能、并发性能、API 响应时间
"""

import sys
from pathlib import Path
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository, PriceRepository


class PerformanceTest:
    """性能测试"""
    
    def __init__(self):
        """初始化测试环境"""
        self.pool = DatabasePool("data/feed_sales.db")
        self.formula_repo = FormulaRepository(self.pool)
        self.price_repo = PriceRepository(self.pool)
        self.test_user = "performance_test_user"
    
    def setup(self):
        """设置测试数据"""
        print("📦 设置性能测试数据...")
        
        # 创建 100 个测试配方
        for i in range(100):
            self.formula_repo.create_formula(self.test_user, {
                "name": f"性能测试配方_{i}",
                "stage_type": "保育",
                "ingredients": [
                    {"name": "玉米", "ratio": 60.0},
                    {"name": "豆粕", "ratio": 25.0},
                    {"name": "预混料", "ratio": 15.0}
                ]
            })
        
        print("  ✅ 创建 100 个测试配方")
        
        # 创建 1000 条价格记录
        for i in range(1000):
            self.price_repo.save_price(self.test_user, {
                "ingredient_code": f"ING_{i}",
                "ingredient_name": f"原料_{i}",
                "price": 3000.00 + i,
                "currency": "CNY",
                "unit": "ton",
                "source": "test",
                "price_date": "2026-03-27"
            })
        
        print("  ✅ 创建 1000 条价格记录")
    
    def teardown(self):
        """清理测试数据"""
        print("\n🧹 清理性能测试数据...")
        
        # 删除所有测试配方
        formulas = self.formula_repo.list_formulas(self.test_user)
        for formula in formulas:
            if formula['name'].startswith("性能测试配方_"):
                self.formula_repo.delete_formula(self.test_user, formula['id'])
        
        print(f"  ✅ 删除 {len(formulas)} 个测试配方")
    
    def test_single_query_performance(self):
        """测试单次查询性能"""
        print("\n🧪 性能测试 1: 单次查询性能")
        
        times = []
        
        # 测试 100 次查询
        for i in range(100):
            start = time.time()
            self.formula_repo.get_formula(self.test_user, "性能测试配方_50")
            end = time.time()
            times.append((end - start) * 1000)  # 转换为毫秒
        
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        p95_time = statistics.quantiles(times, n=4)[2]  # 95 百分位
        
        print(f"  样本数：{len(times)}")
        print(f"  平均时间：{avg_time:.2f}ms")
        print(f"  最小时间：{min_time:.2f}ms")
        print(f"  最大时间：{max_time:.2f}ms")
        print(f"  P95 时间：{p95_time:.2f}ms")
        
        # 性能标准：平均 < 10ms, P95 < 50ms
        assert avg_time < 10, f"平均时间过长：{avg_time:.2f}ms"
        assert p95_time < 50, f"P95 时间过长：{p95_time:.2f}ms"
        
        print(f"  ✅ 单次查询性能达标")
        return True
    
    def test_concurrent_performance(self):
        """测试并发性能"""
        print("\n🧪 性能测试 2: 并发性能")
        
        def query_formula(index):
            start = time.time()
            self.formula_repo.get_formula(self.test_user, f"性能测试配方_{index % 100}")
            end = time.time()
            return (end - start) * 1000
        
        # 测试 10 个并发
        times = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(query_formula, i) for i in range(100)]
            for future in as_completed(futures):
                times.append(future.result())
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=4)[2]
        
        print(f"  并发数：10")
        print(f"  样本数：{len(times)}")
        print(f"  平均时间：{avg_time:.2f}ms")
        print(f"  P95 时间：{p95_time:.2f}ms")
        
        # 性能标准：平均 < 50ms, P95 < 200ms
        assert avg_time < 50, f"平均时间过长：{avg_time:.2f}ms"
        assert p95_time < 200, f"P95 时间过长：{p95_time:.2f}ms"
        
        print(f"  ✅ 并发性能达标")
        return True
    
    def test_database_size(self):
        """测试数据库大小"""
        print("\n🧪 性能测试 3: 数据库大小")
        
        import os
        db_path = Path("data/feed_sales.db")
        db_size = db_path.stat().st_size / 1024 / 1024  # MB
        
        print(f"  数据库文件：{db_path}")
        print(f"  数据库大小：{db_size:.2f}MB")
        
        # 性能标准：< 100MB
        assert db_size < 100, f"数据库过大：{db_size:.2f}MB"
        
        print(f"  ✅ 数据库大小达标")
        return True
    
    def test_memory_usage(self):
        """测试内存使用"""
        print("\n🧪 性能测试 4: 内存使用")
        
        import tracemalloc
        tracemalloc.start()
        
        # 执行 1000 次查询
        for i in range(1000):
            self.formula_repo.get_formula(self.test_user, "性能测试配方_50")
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        current_mb = current / 1024 / 1024
        peak_mb = peak / 1024 / 1024
        
        print(f"  当前内存：{current_mb:.2f}MB")
        print(f"  峰值内存：{peak_mb:.2f}MB")
        
        # 性能标准：峰值 < 50MB
        assert peak_mb < 50, f"峰值内存过大：{peak_mb:.2f}MB"
        
        print(f"  ✅ 内存使用达标")
        return True
    
    def run_all_tests(self):
        """运行所有性能测试"""
        print("=" * 60)
        print("FeedSales AI - 性能测试")
        print("=" * 60)
        
        try:
            # 设置测试数据
            self.setup()
            
            # 运行测试
            tests = [
                ("单次查询性能", self.test_single_query_performance),
                ("并发性能", self.test_concurrent_performance),
                ("数据库大小", self.test_database_size),
                ("内存使用", self.test_memory_usage),
            ]
            
            results = []
            for name, test_func in tests:
                result = test_func()
                results.append((name, result))
            
            # 清理测试数据
            self.teardown()
            
            # 汇总结果
            print("\n" + "=" * 60)
            print("性能测试结果汇总")
            print("=" * 60)
            
            passed = sum(1 for _, r in results if r)
            total = len(results)
            
            for name, result in results:
                status = "✅ 通过" if result else "❌ 失败"
                print(f"  {status}: {name}")
            
            print(f"\n总计：{passed}/{total} 通过")
            
            if passed == total:
                print("\n✅ 所有性能测试通过！")
                return True
            else:
                print(f"\n❌ {total - passed} 个测试失败")
                return False
                
        except Exception as e:
            print(f"\n❌ 性能测试异常：{e}")
            import traceback
            traceback.print_exc()
            self.teardown()
            return False


def main():
    """主函数"""
    test = PerformanceTest()
    success = test.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
