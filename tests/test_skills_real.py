"""
FeedSales AI - 真实技能执行测试 (v1.7)

实际调用技能代码，验证功能完整性
使用 Service 层注入
"""

import asyncio
import logging
import sys
from pathlib import Path
import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.services.calculation_service import CalculationService
from src.services.price_service import PriceService
from skills.formula_cost_skill.skill import FormulaCostSkill
from skills.price_lookup_skill.skill import PriceLookupSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_formula_cost_skill():
    """测试配方成本计算技能 (v1.7)"""
    logger.info("\n========== 测试配方成本计算技能 ==========")
    
    # 初始化 (v1.7: 使用 Service 层)
    pool = DatabasePool("data/feed_sales.db")
    calc_service = CalculationService(pool)
    skill = FormulaCostSkill(calculation_service=calc_service)
    
    # 测试用例
    test_cases = [
        ("标准表达", "Nursery Diet 1成本"),
        ("口语表达", "Beef Cattle Finisher多少钱"),
        ("简化表达", "Broiler Starter成本"),
    ]
    
    passed = 0
    for name, message in test_cases:
        logger.info(f"\n测试：{name}")
        logger.info(f"输入：{message}")
        
        result = await skill.execute("test_user", message)
        
        if result.get('success'):
            data = result.get('data', {})
            logger.info(f"✅ 成功 - 成本：${data.get('cost_per_ton', 'N/A')}/ton")
            passed += 1
        else:
            logger.info(f"⚠️  失败 - {result.get('error', '未知')}")
    
    logger.info(f"\n========== 配方成本测试完成: {passed}/{len(test_cases)} ==========")
    assert passed >= 2, "至少应该通过 2 个测试"


@pytest.mark.asyncio
async def test_price_lookup_skill():
    """测试价格查询技能 (v1.7)"""
    logger.info("\n========== 测试价格查询技能 ==========")
    
    # 初始化 (v1.7: 使用 Service 层)
    pool = DatabasePool("data/feed_sales.db")
    price_service = PriceService(pool)
    skill = PriceLookupSkill(price_service=price_service)
    
    # 测试用例
    test_cases = [
        ("玉米价格", "corn price today"),
        ("豆粕价格", "soybean meal price"),
    ]
    
    passed = 0
    for name, message in test_cases:
        logger.info(f"\n测试：{name}")
        logger.info(f"输入：{message}")
        
        result = await skill.execute("test_user", message)
        
        if result.get('success'):
            data = result.get('data', {})
            logger.info(f"✅ 成功 - 价格：${data.get('price', 'N/A')}/ton")
            passed += 1
        else:
            logger.info(f"⚠️  失败 - {result.get('error', '未知')}")
    
    logger.info(f"\n========== 价格查询测试完成: {passed}/{len(test_cases)} ==========")
    assert passed >= 1, "至少应该通过 1 个测试"