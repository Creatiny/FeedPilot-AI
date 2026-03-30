#!/usr/bin/env python3
"""
FeedSales AI - Unified Skill Runner

A command-line entry point for all skills.
Usage: python3 run_skill.py <skill_name> "<user_message>"

Examples:
  python3 run_skill.py price_lookup "Barley price"
  python3 run_skill.py formula_cost "calculate Nursery Diet 1 cost"
  python3 run_skill.py nutrition "analyze Nursery Diet 1 nutrition"
  python3 run_skill.py customer "show all customers"
"""

import sys
import os
import json
import asyncio
import sqlite3
from datetime import date

# 添加 workspace 到 path
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE, 'src'))
sys.path.insert(0, os.path.join(WORKSPACE, 'skills'))

DB_PATH = os.path.join(WORKSPACE, 'data', 'feed_sales.db')


# ============== ServiceResult ==============
class ServiceResult:
    """服务返回结果"""
    def __init__(self, success: bool, data=None, source=None, error_code=None, error_message=None):
        self.success = success
        self.data = data if data else {}
        self.source = source
        self.error_code = error_code
        self.error_message = error_message


# ============== Simple Services ==============
class SimplePriceService:
    """简化版 PriceService"""
    
    def get_price(self, user_id: str, ingredient_name: str):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ingredient_code, ingredient_name, price, currency, unit, source, price_date
            FROM ingredient_prices
            WHERE owner_open_id = ? AND ingredient_name LIKE ?
            ORDER BY price_date DESC LIMIT 1
        ''', ('system_public', f'%{ingredient_name}%'))
        row = cursor.fetchone()
        conn.close()
        if row:
            return ServiceResult(success=True, data=dict(row), source='public')
        return ServiceResult(success=False, error_message=f"Ingredient '{ingredient_name}' not found")

    def list_public_prices(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ingredient_code, ingredient_name, price, currency, unit, source, price_date
            FROM ingredient_prices WHERE owner_open_id = 'system_public' ORDER BY ingredient_name
        ''')
        prices = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ServiceResult(success=True, data={'prices': prices, 'total': len(prices)})


class SimpleFormulaService:
    """简化版 FormulaService"""
    
    def get_formula(self, user_id: str, formula_name: str):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # 直接查询配方
        cursor.execute('''
            SELECT * FROM formulas WHERE name LIKE ? OR name LIKE ?
        ''', (f'%{formula_name}%', formula_name))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return ServiceResult(success=False, error_message=f"Formula '{formula_name}' not found")
        
        formula = dict(row)
        formula_id = formula['id']
        
        # 查询成分
        cursor.execute('''
            SELECT ingredient_name, ratio_percent FROM formula_ingredients WHERE formula_id = ?
        ''', (formula_id,))
        ingredients = []
        for ing_row in cursor.fetchall():
            ingredients.append({
                'name': ing_row['ingredient_name'], 
                'ratio': ing_row['ratio_percent']
            })
        conn.close()
        
        formula['ingredients'] = ingredients
        return ServiceResult(success=True, data=formula, source='public')

    def list_formulas(self, user_id: str):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, animal_type, stage_type FROM formulas ORDER BY name')
        formulas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ServiceResult(success=True, data={'formulas': formulas, 'total': len(formulas)})


class SimpleCalculationService:
    """简化版 CalculationService"""
    
    def __init__(self):
        self.price_service = SimplePriceService()
        self.formula_service = SimpleFormulaService()
    
    def calculate_cost(self, user_id: str, formula_name: str):
        formula_result = self.formula_service.get_formula(user_id, formula_name)
        if not formula_result.success:
            return formula_result
        
        formula = formula_result.data
        ingredients = formula.get('ingredients', [])
        
        total_cost = 0
        details = []
        price_sources = {}
        
        for ing in ingredients:
            name = ing.get('name', '')
            ratio = ing.get('ratio', 0)
            
            price_result = self.price_service.get_price(user_id, name)
            if price_result.success:
                price = price_result.data.get('price', 0)
                cost = price * ratio / 100
                total_cost += cost
                details.append({
                    'ingredient': name,
                    'percentage': ratio,
                    'price': price,
                    'cost': round(cost, 2)
                })
                price_sources[name] = price_result.source
        
        return ServiceResult(
            success=True,
            data={
                'formula_name': formula.get('name', formula_name),
                'animal_type': formula.get('animal_type'),
                'stage_type': formula.get('stage_type'),
                'total_cost': round(total_cost, 2),
                'details': details,
                'price_sources': price_sources
            },
            source='calculation'
        )


class SimpleCustomerService:
    """简化版 CustomerService"""
    
    def create_customer(self, user_id: str, data: dict):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customers (owner_open_id, name, phone, notes)
            VALUES (?, ?, ?, ?)
        ''', (user_id, data.get('name'), data.get('phone'), data.get('notes', '')))
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        return ServiceResult(success=True, data={'id': customer_id, **data})
    
    def list_customers(self, user_id: str):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE owner_open_id = ? ORDER BY name', (user_id,))
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ServiceResult(success=True, data={'customers': customers, 'total': len(customers)})
    
    def get_customer(self, user_id: str, name: str):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE owner_open_id = ? AND name LIKE ?', (user_id, f'%{name}%'))
        row = cursor.fetchone()
        conn.close()
        if row:
            return ServiceResult(success=True, data=dict(row))
        return ServiceResult(success=False, error_message=f"Customer '{name}' not found")
    
    def update_customer(self, user_id: str, customer_id: int, data: dict):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        sets = ', '.join([f'{k} = ?' for k in data.keys()])
        cursor.execute(f'UPDATE customers SET {sets} WHERE id = ? AND owner_open_id = ?', 
                      list(data.values()) + [customer_id, user_id])
        conn.commit()
        conn.close()
        return ServiceResult(success=True)
    
    def delete_customer(self, user_id: str, customer_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM customers WHERE id = ? AND owner_open_id = ?', (customer_id, user_id))
        conn.commit()
        conn.close()
        return ServiceResult(success=True)


# ============== Skill Factories ==============
def get_price_lookup_skill():
    """初始化 PriceLookupSkill"""
    # 直接导入脚本文件
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "query_price", 
        os.path.join(WORKSPACE, 'skills/price_lookup_skill/scripts/query_price.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # create_skill 接受可选的 price_service 参数
    return module.create_skill(SimplePriceService())


def get_formula_cost_skill():
    """初始化 FormulaCostSkill"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "formula_cost", 
        os.path.join(WORKSPACE, 'skills/formula_cost_skill/skill.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FormulaCostSkill(SimpleCalculationService())


def get_nutrition_skill():
    """初始化 NutritionAnalysisSkill"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "nutrition", 
        os.path.join(WORKSPACE, 'skills/nutrition_analysis_skill/skill.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.NutritionAnalysisSkill(SimpleFormulaService())


def get_customer_skill():
    """初始化 CustomerRecordSkill"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "customer", 
        os.path.join(WORKSPACE, 'skills/customer_record_skill/skill.py')
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CustomerRecordSkill(SimpleCustomerService())


# ============== Main Entry ==============
SKILL_MAP = {
    'price_lookup': get_price_lookup_skill,
    'price': get_price_lookup_skill,
    'formula_cost': get_formula_cost_skill,
    'cost': get_formula_cost_skill,
    'nutrition': get_nutrition_skill,
    'analyze': get_nutrition_skill,
    'customer': get_customer_skill,
    'customers': get_customer_skill,
}


async def run_skill(skill_name: str, user_message: str, user_id: str = 'cli_user'):
    """运行指定 skill"""
    skill_factory = SKILL_MAP.get(skill_name)
    if not skill_factory:
        return {'success': False, 'error': f"Unknown skill: {skill_name}. Available: {list(SKILL_MAP.keys())}"}
    
    skill = skill_factory()
    result = await skill.execute(user_id, user_message)
    return result


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            'success': False, 
            'error': 'Usage: run_skill.py <skill_name> "<user_message>"',
            'available_skills': list(SKILL_MAP.keys())
        }, indent=2))
        sys.exit(1)
    
    skill_name = sys.argv[1]
    user_message = sys.argv[2]
    
    result = asyncio.run(run_skill(skill_name, user_message))
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()