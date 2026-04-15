#!/usr/bin/env python3
"""
FeedSales Skills - Unified Launcher

统一的技能启动器，处理依赖注入和执行
"""

import sys
import os
import json
import argparse
import asyncio
from pathlib import Path

# Set up paths - import from base directory to maintain package structure
BASE_DIR = Path('/home/kenny/.openclaw/workspace-feedsales')
DB_PATH = BASE_DIR / 'data' / 'feed_sales.db'

# Add base directory to Python path (not src)
sys.path.insert(0, str(BASE_DIR))


def run_formula_cost(user_id: str, message: str) -> dict:
    """运行配方成本计算技能"""
    from src.database.pool import DatabasePool
    from src.services.calculation_service import CalculationService
    from skills.formula_cost_skill.skill import FormulaCostSkill
    
    db_pool = DatabasePool(str(DB_PATH))
    calculation_service = CalculationService(db_pool)
    skill = FormulaCostSkill(calculation_service)
    
    return asyncio.run(skill.execute(user_id, message))


def run_price_lookup(user_id: str, message: str) -> dict:
    """运行价格查询技能"""
    from src.database.pool import DatabasePool
    from src.services.price_service import PriceService
    from skills.price_lookup_skill.skill import PriceLookupSkill
    
    db_pool = DatabasePool(str(DB_PATH))
    price_service = PriceService(db_pool)
    skill = PriceLookupSkill(price_service)
    
    return asyncio.run(skill.execute(user_id, message))


def run_customer_record(user_id: str, message: str) -> dict:
    """运行客户记录管理技能"""
    from src.database.pool import DatabasePool
    from src.services.customer_service import CustomerService
    from skills.customer_record_skill.skill import CustomerRecordSkill
    
    db_pool = DatabasePool(str(DB_PATH))
    customer_service = CustomerService(db_pool)
    skill = CustomerRecordSkill(customer_service)
    
    return asyncio.run(skill.execute(user_id, message))


def run_nutrition_analysis(user_id: str, message: str) -> dict:
    """运行营养分析技能"""
    from src.database.pool import DatabasePool
    from src.services.formula_service import FormulaService
    from skills.nutrition_analysis_skill.skill import NutritionAnalysisSkill
    
    db_pool = DatabasePool(str(DB_PATH))
    formula_service = FormulaService(db_pool)
    skill = NutritionAnalysisSkill(formula_service)
    
    return asyncio.run(skill.execute(user_id, message))


SKILLS = {
    'formula-cost': run_formula_cost,
    'price-lookup': run_price_lookup,
    'customer-record': run_customer_record,
    'nutrition-analysis': run_nutrition_analysis,
}


def main():
    parser = argparse.ArgumentParser(description='FeedSales Skills Launcher')
    parser.add_argument('--skill', required=True, choices=list(SKILLS.keys()), help='Skill name')
    parser.add_argument('--user-id', required=True, help='User ID')
    parser.add_argument('--message', required=True, help='User message')
    parser.add_argument('--db-path', default=str(DB_PATH), help='Database path')
    
    args = parser.parse_args()
    
    try:
        runner = SKILLS[args.skill]
        result = runner(args.user_id, args.message)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()