"""
FeedSales AI - P0 完成全面测试 (v1.7)

测试所有 P0 任务的功能
"""

import sys
from pathlib import Path
import pytest

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


def test_repository():
    """测试 T04: Repository"""
    print("\n🧪 测试 T04: Repository...")
    
    pool = DatabasePool("data/feed_sales.db")
    formula_repo = FormulaRepository(pool)
    
    # 获取公共配方
    formulas = formula_repo.list_formulas("system_public")
    assert len(formulas) >= 1, "应该有公共配方"
    print(f"  ✅ 获取公共配方成功 ({len(formulas)} 个)")
    
    # 获取公共价格
    from src.services.price_service import PriceService
    service = PriceService(pool)
    result = service.list_public_prices()
    assert result.success, "获取公共价格失败"
    prices = result.data.get('prices', [])
    assert len(prices) >= 1, "应该有公共价格"
    print(f"  ✅ 获取公共价格成功 ({len(prices)} 个)")


def test_skill_metadata():
    """测试 T05: 技能元数据"""
    print("\n🧪 测试 T05: 技能元数据...")
    
    # 检查 SKILL.md 文件
    skill_files = [
        "skills/formula_cost_skill/SKILL.md",
        "skills/price_lookup_skill/SKILL.md",
        "skills/customer_record_skill/SKILL.md",
        "skills/nutrition_analysis_skill/SKILL.md",
    ]
    
    for skill_file in skill_files:
        import os
        path = os.path.join(str(Path(__file__).parent.parent), skill_file)
        assert os.path.exists(path), f"{skill_file} 不存在"
    
    print(f"  ✅ {len(skill_files)} 个技能 SKILL.md 存在")