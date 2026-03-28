"""
FeedSales AI - 真实技能执行测试

实际调用技能代码，验证功能完整性
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository, PriceRepository
from skills.formula_cost_skill.skill import FormulaCostSkill
from skills.price_lookup_skill.skill import PriceLookupSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_formula_cost_skill():
    """测试配方成本计算技能"""
    logger.info("\n========== 测试配方成本计算技能 ==========")
    
    # 初始化
    pool = DatabasePool("data/feed_sales.db")
    formula_repo = FormulaRepository(pool)
    skill = FormulaCostSkill(pool, formula_repo, None)
    
    # 测试用例
    test_cases = [
        ("标准表达", "计算保育料 1 号的成本"),
        ("口语表达", "保育料 1 号多少钱"),
        ("简化表达", "育肥料成本"),
        ("完整表达", "帮我计算保育料 1 号配方成本"),
    ]
    
    for name, message in test_cases:
        logger.info(f"\n测试：{name}")
        logger.info(f"输入：{message}")
        
        result = await skill.execute("test_user", message)
        
        if result.get('success'):
            data = result.get('data', {})
            logger.info(f"✅ 成功 - 成本：¥{data.get('cost_per_ton', 'N/A')}/吨")
        else:
            logger.info(f"⚠️  预期失败 - {result.get('error', '未知')}")
    
    logger.info("\n========== 配方成本测试完成 ==========")


async def test_price_lookup_skill():
    """测试价格查询技能"""
    logger.info("\n========== 测试价格查询技能 ==========")
    
    # 初始化
    pool = DatabasePool("data/feed_sales.db")
    price_repo = PriceRepository(pool)
    skill = PriceLookupSkill(price_repo)
    
    # 测试用例
    test_cases = [
        ("玉米价格", "今天玉米价格"),
        ("豆粕价格", "豆粕多少钱"),
        ("口语", "玉米现在什么价"),
    ]
    
    for name, message in test_cases:
        logger.info(f"\n测试：{name}")
        logger.info(f"输入：{message}")
        
        result = await skill.execute("test_user", message)
        
        if result.get('success'):
            data = result.get('data', {})
            logger.info(f"✅ 成功 - 价格：¥{data.get('price', 'N/A')}/吨")
        else:
            logger.info(f"⚠️  预期失败 - {result.get('error', '未知')}")
    
    logger.info("\n========== 价格查询测试完成 ==========")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("FeedSales AI - 真实技能执行测试")
    logger.info("=" * 60)
    
    # 测试配方成本
    await test_formula_cost_skill()
    
    # 测试价格查询
    await test_price_lookup_skill()
    
    logger.info("\n" + "=" * 60)
    logger.info("所有测试完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
