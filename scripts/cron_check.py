#!/usr/bin/env python3
"""
FeedSales AI - Cron Price/Formula Check Script

严格遵循架构设计文档：
- 通过 Service 层访问数据（不是直接 sqlite3）
- 通过 CalculationService 计算配方成本（整合价格 + 配方）
- 输出固定格式，供 cron job 解析
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.pool import DatabasePool
from src.services.price_service import PriceService
from src.services.formula_service import FormulaService
from src.services.calculation_service import CalculationService

DB_PATH = PROJECT_ROOT / 'data' / 'feed_sales.db'
DB = DatabasePool(str(DB_PATH))

def get_price(ingredient_name: str) -> dict | None:
    """通过 PriceService 获取公共价格（设计文档指定方式）"""
    ps = PriceService(DB)
    r = ps.get_public_price(ingredient_name)
    return r.data if r.success else None

def calculate_formula_cost(formula_name: str, user_id: str = 'system_public') -> dict | None:
    """通过 CalculationService 计算配方成本（设计文档指定方式）"""
    cs = CalculationService(DB)
    result = cs.calculate_cost(user_id, formula_name)
    if result.success:
        return result.data
    return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: cron_check.py <price|formula> <name>")
        sys.exit(1)

    check_type = sys.argv[1]
    name = sys.argv[2]

    if check_type == "price":
        d = get_price(name)
        if d:
            print(f"{d['ingredient_name']}|{d['price']}|{d.get('price_date','N/A')}|{d.get('source','public')}")
        else:
            print("NOT_FOUND")

    elif check_type == "formula":
        result = calculate_formula_cost(name)
        if result:
            print(f"TOTAL_COST|{result['total_cost']:.2f}")
            for detail in result.get('details', []):
                ing_name = detail.get('name', '')
                price = detail.get('price', 0)
                ratio = detail.get('ratio', 0)
                cost = detail.get('cost', 0)
                source = detail.get('price_source', 'unknown')
                print(f"  {ing_name}: ${price}/ton x {ratio}% = ${cost:.2f}/ton [{source}]")
        else:
            print("FORMULA_NOT_FOUND")
