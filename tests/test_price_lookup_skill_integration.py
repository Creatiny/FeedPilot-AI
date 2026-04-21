"""
FeedSales AI - PriceLookupSkill 集成测试 (v1.7)

测试技能走 PriceService 统一接口
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.services.price_service import PriceService
from skills.price_lookup_skill.skill import PriceLookupSkill


@pytest.mark.asyncio
async def test_query_public_price():
    """测试查询公共价格"""
    print("\n🧪 测试：查询公共价格")
    
    pool = DatabasePool("data/feed_sales.db")
    service = PriceService(pool)
    skill = PriceLookupSkill(price_service=service)
    
    result = await skill.execute('test_user', 'corn price today')
    
    assert result['success'], f"应该成功: {result.get('error')}"
    assert result['data']['price'] > 0
    assert result['data']['source'] in ['public', 'private']
    
    print(f"  ✅ 查询成功: ${result['data']['price']}/ton")


@pytest.mark.asyncio
async def test_query_soybean_price():
    """测试查询豆粕价格"""
    print("\n🧪 测试：查询豆粕价格")
    
    pool = DatabasePool("data/feed_sales.db")
    service = PriceService(pool)
    skill = PriceLookupSkill(price_service=service)
    
    result = await skill.execute('test_user', 'soybean meal price')
    
    assert result['success'], f"应该成功: {result.get('error')}"
    assert result['data']['price'] > 0
    
    print(f"  ✅ 查询成功: ${result['data']['price']}/ton")


@pytest.mark.asyncio
async def test_list_prices():
    """测试列出价格"""
    print("\n🧪 测试：列出价格")
    
    pool = DatabasePool("data/feed_sales.db")
    service = PriceService(pool)
    skill = PriceLookupSkill(price_service=service)
    
    result = await skill.execute('test_user', 'show all prices')
    
    assert result['success']
    assert result['data']['count'] >= 1
    
    print(f"  ✅ 列出 {result['data']['count']} 个价格")