"""
FeedSales AI - 数据库测试脚本 (v1.7)

测试 DatabasePool 和 Repository 功能
"""

import sys
from pathlib import Path
import pytest

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository, PriceRepository


def test_database_pool():
    """测试 DatabasePool"""
    print("🧪 测试 DatabasePool...")
    
    pool = DatabasePool("data/feed_sales.db")
    
    # 测试连接
    assert pool.test_connection(), "连接测试失败"
    print("✅ 连接测试通过")
    
    # 测试单例模式
    pool2 = DatabasePool("data/feed_sales.db")
    assert pool is pool2, "单例模式失败"
    print("✅ 单例模式测试通过")


def test_formula_repository(pool):
    """测试 FormulaRepository"""
    print("\n🧪 测试 FormulaRepository...")
    
    repo = FormulaRepository(pool)
    test_user = "test_user_pytest"
    
    # 列出公共配方
    formulas = repo.list_formulas("system_public")
    assert len(formulas) >= 1, "应该有公共配方"
    print(f"✅ 列出公共配方成功 (共 {len(formulas)} 个)")


def test_price_repository(pool):
    """测试 PriceRepository"""
    print("\n🧪 测试 PriceRepository...")
    
    from src.services.price_service import PriceService
    service = PriceService(pool)
    
    # 获取公共价格
    result = service.list_public_prices()
    assert result.success, "获取公共价格失败"
    prices = result.data.get('prices', [])
    assert len(prices) >= 1, "应该有公共价格"
    print(f"✅ 列出公共价格成功 (共 {len(prices)} 个)")