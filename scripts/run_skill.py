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

# 共享 ingredient_code 映射（与 src/utils/ingredient_codes.py 保持一致）
_INGREDIENT_CODE_MAP = {
    'Corn': 'ING_CORN', 'Corn, #2 Yellow': 'ING_CORN', 'Corn, grain': 'ING_CORN',
    'Wheat': 'ING_WHEAT', 'Barley': 'ING_BARLEY', 'Rice': 'ING_RICE', 'Sorghum': 'ING_SORGHUM', 'Oats': 'ING_OATS',
    'Soybean meal': 'ING_SBM', 'Soybean meal, 48%': 'ING_SBM', 'Soybean': 'ING_SBM',
    'Canola meal': 'ING_CANOLA', 'Cottonseed meal': 'ING_COTTON', 'Fish meal': 'ING_FISHM', 'Fish meal, 60%': 'ING_FISHM',
    'DDGS': 'ING_DDGS', "Distiller's grains": 'ING_DDGS',
    'Limestone': 'ING_LIME', 'Dicalcium phosphate': 'ING_DCP', 'Dicalcium': 'ING_DCP',
    'Salt': 'ING_SALT', 'L-Lysine': 'ING_LYS', 'Lysine': 'ING_LYS',
    'DL-Methionine': 'ING_MET', 'Methionine': 'ING_MET',
    'Premix': 'ING_PREMIX', 'Vitamin premix': 'ING_PREMIX',
    'Alfalfa': 'ING_ALFALFA', 'Alfalfa meal': 'ING_ALFALFA',
    'Corn silage': 'ING_SILAGE', 'Grass hay': 'ING_HAY', 'Hay': 'ING_HAY',
    'Molasses': 'ING_MOLASSES', 'Water': 'ING_WATER',
}

def _generate_ingredient_code(name: str) -> str:
    """将原料名称转换为 ingredient_code"""
    if not name:
        return 'ING_UNKNOWN'
    name_lower = name.lower()
    for key, code in _INGREDIENT_CODE_MAP.items():
        if key.lower() in name_lower:
            return code
    first_word = name.split(',')[0].strip()
    return 'ING_' + first_word.upper().replace(' ', '_')[:15]


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
    """简化版 PriceService（使用 ingredient_code 精确匹配）"""
    
    def get_price(self, user_id: str, ingredient_name: str):
        # 将 name 转换为 ingredient_code
        ingredient_code = _generate_ingredient_code(ingredient_name)
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ingredient_code, ingredient_name, price, currency, unit, source, price_date
            FROM ingredient_prices
            WHERE owner_open_id = ? AND ingredient_code = ?
            ORDER BY price_date DESC LIMIT 1
        ''', (user_id, ingredient_code))
        row = cursor.fetchone()
        if not row:
            # 降级查公共价格
            cursor.execute('''
                SELECT ingredient_code, ingredient_name, price, currency, unit, source, price_date
                FROM ingredient_prices
                WHERE owner_open_id = 'system_public' AND ingredient_code = ?
                ORDER BY price_date DESC LIMIT 1
            ''', (ingredient_code,))
            row = cursor.fetchone()
            if row:
                conn.close()
                return ServiceResult(success=True, data=dict(row), source='public')
            conn.close()
            return ServiceResult(success=False, error_message=f"Ingredient '{ingredient_name}' ({ingredient_code}) not found")
        conn.close()
        return ServiceResult(success=True, data=dict(row), source='private' if user_id != 'system_public' else 'public')

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
        # 优先精确匹配
        cursor.execute('''
            SELECT * FROM formulas WHERE owner_open_id = ? AND name = ?
        ''', (user_id, formula_name))
        row = cursor.fetchone()
        if not row:
            # 降级到公共配方
            cursor.execute('''
                SELECT * FROM formulas WHERE owner_open_id = 'system_public' AND name = ?
            ''', (formula_name,))
            row = cursor.fetchone()
            source = 'public'
        else:
            source = 'private'
        if not row:
            conn.close()
            return ServiceResult(success=False, error_message=f"Formula '{formula_name}' not found")
        
        formula = dict(row)
        formula_id = formula['id']
        
        # 查询成分（含 ingredient_code）
        cursor.execute('''
            SELECT ingredient_name, ingredient_code, ratio_percent
            FROM formula_ingredients WHERE formula_id = ?
        ''', (formula_id,))
        ingredients = []
        for ing_row in cursor.fetchall():
            ingredients.append({
                'name': ing_row['ingredient_name'],
                'ingredient_code': ing_row['ingredient_code'],
                'ratio': ing_row['ratio_percent']
            })
        conn.close()
        
        formula['ingredients'] = ingredients
        return ServiceResult(success=True, data=formula, source=source)

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
            # 直接使用 ingredient_code 查询（精确匹配）
            price_result = self.price_service.get_price(user_id, name)
            if price_result.success:
                price = price_result.data.get('price', 0)
                cost = price * ratio / 100
                total_cost += cost
                # 使用 ingredient_code 作为 key
                code = ing.get('ingredient_code', _generate_ingredient_code(name))
                details.append({
                    'ingredient': name,
                    'ingredient_code': code,
                    'percentage': ratio,
                    'price': price,
                    'cost': round(cost, 2)
                })
                price_sources[code] = price_result.source
        
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
        # P0 FIX: 白名单验证字段名，防止 SQL 注入
        ALLOWED_FIELDS = {'name', 'phone', 'notes', 'animal_type', 'scale'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        if not filtered_data:
            conn.close()
            return ServiceResult(success=False, error_message="No valid fields to update")
        sets = ', '.join([f'{k} = ?' for k in filtered_data.keys()])
        cursor.execute(f'UPDATE customers SET {sets} WHERE id = ? AND owner_open_id = ?', 
                      list(filtered_data.values()) + [customer_id, user_id])
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