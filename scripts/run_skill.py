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
        missing_prices = []
        
        # Default prices fallback
        DEFAULT_PRICES = {
            'Corn': 180.00, 'Soybean meal': 350.00, 'Fish meal': 1800.00,
            'Wheat': 200.00, 'Limestone': 120.00, 'Premix': 450.00,
            'Dicalcium phosphate': 650.00, 'Salt': 150.00,
            'L-Lysine': 1200.00, 'Methionine': 2500.00,
        }
        
        for ing in ingredients:
            name = ing.get('name', '')
            ratio = ing.get('ratio', 0)
            code = ing.get('ingredient_code', _generate_ingredient_code(name))
            # 直接使用 ingredient_code 查询（精确匹配）
            price_result = self.price_service.get_price(user_id, name)
            if price_result.success:
                price = price_result.data.get('price', 0)
                source = price_result.source
            else:
                # Fallback to default price
                price = 300.0
                for key, default_p in DEFAULT_PRICES.items():
                    if key.lower() in name.lower():
                        price = default_p
                        break
                source = 'default'
                missing_prices.append(name)
            
            cost = price * ratio / 100
            total_cost += cost
            details.append({
                'name': name,
                'ingredient_code': code,
                'ratio': ratio,
                'price': price,
                'cost': round(cost, 2),
                'price_source': source,
            })
            price_sources[code] = source
        
        return ServiceResult(
            success=True,
            data={
                'formula_name': formula.get('name', formula_name),
                'animal_type': formula.get('animal_type'),
                'stage_type': formula.get('stage_type'),
                'total_cost': round(total_cost, 2),
                'currency': 'USD',
                'unit': 'ton',
                'details': details,
                'price_sources': price_sources,
                'missing_prices': missing_prices,
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


# ============== Simple Reminder Service ==============
class SimpleReminderService:
    """简化版 ReminderService"""
    
    def __init__(self):
        pass
    
    def _get_conn(self):
        return sqlite3.connect(DB_PATH)
    
    def create_reminder(self, user_id: str, reminder_type: str, threshold: float, 
                        condition: str, ingredient: str = None, ingredient_code: str = None,
                        formula: str = None, formula_id: str = None):
        import uuid
        from datetime import datetime
        reminder_id = str(uuid.uuid4())[:8]  # 短 ID 便于用户记忆
        now = datetime.now().isoformat()
        
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (id, user_id, type, ingredient, ingredient_code, formula, formula_id, threshold, condition, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (reminder_id, user_id, reminder_type, ingredient, ingredient_code, formula, formula_id, threshold, condition, now))
        conn.commit()
        conn.close()
        return ServiceResult(success=True, data={'id': reminder_id, 'ingredient': ingredient, 'threshold': threshold, 'condition': condition})
    
    def list_reminders(self, user_id: str):
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT id, type, ingredient, formula, threshold, condition, enabled, created_at FROM reminders WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return ServiceResult(success=True, data={'reminders': [dict(r) for r in rows], 'count': len(rows)})
    
    def delete_reminder(self, user_id: str, reminder_id: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        # 支持 8 字符短 ID 匹配
        if len(reminder_id) >= 8:
            cursor.execute('DELETE FROM reminders WHERE user_id = ? AND id LIKE ?', (user_id, f'{reminder_id}%'))
        else:
            cursor.execute('DELETE FROM reminders WHERE user_id = ? AND id = ?', (user_id, reminder_id))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted > 0:
            return ServiceResult(success=True, data={'deleted': deleted})
        return ServiceResult(success=False, error_message=f"Reminder '{reminder_id}' not found")


# ============== Reminder Skill ==============
# 原料名称映射
_INGREDIENT_MAP = {
    'corn': {'name': 'Corn, No.2 Yellow', 'code': 'ING_CORN'},
    'soybean': {'name': 'Soybean meal, 48%', 'code': 'ING_SBM'},
    'soybean meal': {'name': 'Soybean meal, 48%', 'code': 'ING_SBM'},
    'sbm': {'name': 'Soybean meal, 48%', 'code': 'ING_SBM'},
    'wheat': {'name': 'Wheat, grain', 'code': 'ING_WHEAT'},
    'barley': {'name': 'Barley', 'code': 'ING_BARLEY'},
    'fish meal': {'name': 'Fish meal, 65%', 'code': 'ING_FISHM'},
    'ddgs': {'name': 'DDGS, 28%', 'code': 'ING_DDGS'},
    'limestone': {'name': 'Limestone', 'code': 'ING_LIME'},
    'lysine': {'name': 'L-Lysine HCl', 'code': 'ING_LYS'},
    'methionine': {'name': 'DL-Methionine', 'code': 'ING_MET'},
}

# 配方名称映射
_FORMULA_MAP = {
    'nursery': {'name': 'Nursery Diet 1', 'id': 'FORMULA_NURSERY_1'},
    'nursery diet': {'name': 'Nursery Diet 1', 'id': 'FORMULA_NURSERY_1'},
    'grower': {'name': 'Grower Diet 1', 'id': 'FORMULA_GROWER_1'},
    'finishing': {'name': 'Finishing Diet', 'id': 'FORMULA_FINISHING'},
    'broiler': {'name': 'Broiler Starter', 'id': 'FORMULA_BROILER_STARTER'},
    'layer': {'name': 'Layer Diet', 'id': 'FORMULA_LAYER'},
}


class ReminderSkill:
    """提醒技能"""
    
    def __init__(self, service: SimpleReminderService):
        self.service = service
    
    async def execute(self, user_id: str, message: str) -> dict:
        """执行提醒操作"""
        import re
        msg_lower = message.lower()
        
        # 查看提醒列表
        if 'list' in msg_lower or 'show' in msg_lower or 'my reminder' in msg_lower or 'reminders' in msg_lower:
            result = self.service.list_reminders(user_id)
            if result.success:
                reminders = result.data['reminders']
                if not reminders:
                    return {'success': True, 'message': 'You have no reminders set. Create one:\n• "Alert when corn > $90/ton"\n• "Remind me when soybean meal < $350/ton"'}
                lines = [f"| ID | Type | Target | Condition |", "|----|------|--------|-----------|"]
                for r in reminders:
                    target = r.get('ingredient') or r.get('formula', 'Unknown')
                    cond = 'above' if r['condition'] == 'above' else 'below'
                    lines.append(f"| {r['id'][:8]} | {r['type']} | {target} | {cond} ${r['threshold']} |")
                return {'success': True, 'message': '\n'.join(lines)}
            return {'success': False, 'error': result.error_message}
        
        # 删除提醒
        if 'delete' in msg_lower or 'remove' in msg_lower or 'cancel' in msg_lower:
            # 提取 ID (8 位十六进制)
            id_match = re.search(r'[a-f0-9]{8}', msg_lower)
            if id_match:
                reminder_id = id_match.group()
                result = self.service.delete_reminder(user_id, reminder_id)
                if result.success:
                    return {'success': True, 'message': f"✅ Reminder {reminder_id} deleted."}
                return {'success': False, 'error': result.error_message}
            return {'success': False, 'error': 'Please provide a reminder ID to delete. Example: "delete reminder 245f1bd9"'}
        
        # 创建提醒
        # 匹配: "alert when X above/below $Y" 或 "remind me when X exceeds/falls below $Y"
        price_pattern = r'(?:alert|remind|notify).*?(?:when|if)\s+(\w+(?:\s+\w+)?)\s+(?:exceeds?|goes?|falls?|drops?|above|below|>|<)\s*\$?(\d+(?:\.\d+)?)'
        match = re.search(price_pattern, msg_lower)
        
        if match:
            ingredient_name = match.group(1).strip()
            threshold = float(match.group(2))
            
            # 判断条件
            condition = 'above'
            if any(w in msg_lower for w in ['below', 'under', '<', 'falls', 'drops', 'less']):
                condition = 'below'
            
            # 查找原料
            ingredient_info = _INGREDIENT_MAP.get(ingredient_name.lower())
            if ingredient_info:
                result = self.service.create_reminder(
                    user_id=user_id,
                    reminder_type='price',
                    threshold=threshold,
                    condition=condition,
                    ingredient=ingredient_info['name'],
                    ingredient_code=ingredient_info['code']
                )
                if result.success:
                    cond_text = 'exceeds' if condition == 'above' else 'falls below'
                    return {'success': True, 'message': f"✅ Price alert created!\n\n| Ingredient | Condition | Alert ID |\n|------------|-----------|----------|\n| {ingredient_info['name']} | {cond_text} ${threshold}/ton | {result.data['id']} |"}
                return {'success': False, 'error': result.error_message}
            
            # 查找配方
            formula_info = _FORMULA_MAP.get(ingredient_name.lower())
            if formula_info:
                result = self.service.create_reminder(
                    user_id=user_id,
                    reminder_type='formula_cost',
                    threshold=threshold,
                    condition=condition,
                    formula=formula_info['name'],
                    formula_id=formula_info['id']
                )
                if result.success:
                    cond_text = 'exceeds' if condition == 'above' else 'falls below'
                    return {'success': True, 'message': f"✅ Formula cost alert created!\n\n| Formula | Condition | Alert ID |\n|---------|-----------|----------|\n| {formula_info['name']} | {cond_text} ${threshold}/ton | {result.data['id']} |"}
                return {'success': False, 'error': result.error_message}
            
            return {'success': False, 'error': f"Unknown ingredient or formula: '{ingredient_name}'. Supported: corn, soybean meal, wheat, barley, fish meal, DDGS, nursery diet, grower diet, finishing diet."}
        
        return {'success': False, 'error': 'Could not parse reminder request. Try: "Alert when corn > $100/ton" or "show my reminders"'}


def get_reminder_skill():
    """初始化 ReminderSkill"""
    return ReminderSkill(SimpleReminderService())


# ============== Subscription & Referral Services ==============
# (Migrated from src/services/subscription_service.py and src/services/referral_service.py)

import hashlib
from datetime import datetime, timedelta


class SimpleSubscriptionService:
    """Simplified subscription service for Hermes skill execution."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_conn(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_subscription_status(self, user_id: str) -> dict:
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
        )
        subscription = cursor.fetchone()

        if subscription is None:
            cursor.execute(
                "INSERT INTO subscriptions (user_id, plan_id, is_in_trial, referral_bonus_days) VALUES (?, 1, 0, 0)",
                (user_id,)
            )
            conn.commit()
            cursor.execute(
                "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
            )
            subscription = cursor.fetchone()

        cursor.execute(
            "SELECT * FROM subscription_plans WHERE id = ?",
            (subscription['plan_id'],)
        )
        plan = cursor.fetchone()

        trial_days_left = 0
        if subscription['is_in_trial'] and subscription['trial_ends_at']:
            trial_ends = datetime.fromisoformat(subscription['trial_ends_at'])
            now = datetime.now()
            if trial_ends > now:
                trial_days_left = (trial_ends - now).days + 1

        return {
            'user_id': user_id,
            'plan_name': plan['name'],
            'plan_display_name': plan['display_name'],
            'queries_per_day': plan['queries_per_day'],
            'is_in_trial': bool(subscription['is_in_trial']),
            'trial_days_left': trial_days_left,
            'referral_bonus_days': subscription['referral_bonus_days'] or 0,
            'pro_bonus_months': subscription['pro_bonus_months'] or 0,
        }

    def start_trial(self, user_id: str, days: int = 7) -> dict:
        self.get_subscription_status(user_id)  # ensure user exists

        now = datetime.now()
        trial_ends = now + timedelta(days=days)

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE subscriptions SET is_in_trial = 1, trial_started_at = ?, trial_ends_at = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (now.isoformat(), trial_ends.isoformat(), user_id)
        )
        conn.commit()
        conn.close()

        return {
            'success': True,
            'trial_days': days,
            'trial_ends_at': trial_ends.isoformat()
        }

    def check_query_limit(self, user_id: str) -> dict:
        status = self.get_subscription_status(user_id)
        queries_per_day = status['queries_per_day']

        if queries_per_day == -1:
            return {'allowed': True, 'queries_remaining': -1}

        today = datetime.now().date().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT query_count FROM daily_usage WHERE user_id = ? AND usage_date = ?",
            (user_id, today)
        )
        result = cursor.fetchone()
        used = result['query_count'] if result else 0
        conn.close()

        remaining = queries_per_day - used

        if remaining > 0:
            return {'allowed': True, 'queries_remaining': remaining}
        else:
            return {
                'allowed': False,
                'queries_remaining': 0,
                'message': f"Daily limit reached ({queries_per_day} queries/day). Upgrade for more."
            }

    def record_usage(self, user_id: str) -> None:
        self.get_subscription_status(user_id)

        today = datetime.now().date().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO daily_usage (user_id, usage_date, query_count) VALUES (?, ?, 1) ON CONFLICT(user_id, usage_date) DO UPDATE SET query_count = query_count + 1, updated_at = CURRENT_TIMESTAMP",
            (user_id, today)
        )
        conn.commit()
        conn.close()


class SimpleReferralService:
    """Simplified referral service for Hermes skill execution."""

    BONUS_DAYS_PER_REFERRAL = 7
    REFERRALS_FOR_PRO_BONUS = 3

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._sub_service = SimpleSubscriptionService(db_path)
        self._referral_code_cache = {}

    def _get_conn(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # Telegram bot username for deep-link referrals
    BOT_USERNAME = os.getenv("FEEDPILOT_BOT_USERNAME", "feedpilot_bot")

    def get_referral_link(self, user_id: str) -> str:
        self._sub_service.get_subscription_status(user_id)
        hash_obj = hashlib.md5(user_id.encode())
        referral_code = hash_obj.hexdigest()[:8]
        full_code = f"ref_{referral_code}"
        self._referral_code_cache[full_code] = user_id
        return f"https://t.me/{self.BOT_USERNAME}?start={full_code}"

    def get_referral_stats(self, user_id: str) -> dict:
        self._sub_service.get_subscription_status(user_id)
        referral_link = self.get_referral_link(user_id)

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        referral_count = result["count"] if result else 0

        cursor.execute(
            "SELECT referral_bonus_days, pro_bonus_months, plan_id FROM subscriptions WHERE user_id = ?",
            (user_id,)
        )
        sub = cursor.fetchone()
        total_bonus_days = sub["referral_bonus_days"] if sub and sub["referral_bonus_days"] else 0
        pro_bonus_months = sub["pro_bonus_months"] if sub and sub["pro_bonus_months"] else 0

        is_permanent_pro = bool(pro_bonus_months > 0)
        plan_name = "free"
        if sub:
            cursor.execute(
                "SELECT name FROM subscription_plans WHERE id = ?",
                (sub["plan_id"],)
            )
            plan = cursor.fetchone()
            if plan:
                plan_name = plan["name"]

        conn.close()

        return {
            "referral_count": referral_count,
            "total_bonus_days": total_bonus_days,
            "pro_bonus_months": pro_bonus_months,
            "referral_link": referral_link,
            "is_permanent_pro": is_permanent_pro,
            "plan_name": plan_name,
        }

    def process_referral(self, referrer_id: str, referee_id: str, bonus_days: int = 7) -> dict:
        if referrer_id == referee_id:
            return {"success": False, "message": "You cannot refer yourself."}

        self._sub_service.get_subscription_status(referrer_id)
        self._sub_service.get_subscription_status(referee_id)

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM referrals WHERE referee_id = ?",
            (referee_id,)
        )
        if cursor.fetchone():
            conn.close()
            return {"success": False, "message": "User has already been referred."}

        cursor.execute(
            "SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ?",
            (referrer_id,)
        )
        current_count = cursor.fetchone()["count"]

        cursor.execute(
            "INSERT INTO referrals (referrer_id, referee_id, bonus_days) VALUES (?, ?, ?)",
            (referrer_id, referee_id, self.BONUS_DAYS_PER_REFERRAL)
        )

        cursor.execute(
            "UPDATE subscriptions SET referral_bonus_days = COALESCE(referral_bonus_days, 0) + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (self.BONUS_DAYS_PER_REFERRAL, referrer_id)
        )
        cursor.execute(
            "UPDATE subscriptions SET referral_bonus_days = COALESCE(referral_bonus_days, 0) + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (self.BONUS_DAYS_PER_REFERRAL, referee_id)
        )

        new_count = current_count + 1
        pro_bonus_awarded = False

        if new_count >= self.REFERRALS_FOR_PRO_BONUS:
            cursor.execute(
                "UPDATE subscriptions SET pro_bonus_months = COALESCE(pro_bonus_months, 0) + 1, plan_id = 3, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (referrer_id,)
            )
            pro_bonus_awarded = True

        conn.commit()
        conn.close()

        message = f"Bonus applied! Both users received {self.BONUS_DAYS_PER_REFERRAL} bonus days!"
        if pro_bonus_awarded:
            message += f" Plus 1 month Pro for the referrer (now at {new_count} referrals)!"

        return {
            "success": True,
            "bonus_days": self.BONUS_DAYS_PER_REFERRAL,
            "pro_bonus_awarded": pro_bonus_awarded,
            "message": message,
            "referral_count": new_count
        }

    def _decode_referral_code(self, referral_code: str) -> str:
        if not referral_code or not referral_code.startswith("ref_"):
            return None

        if referral_code in self._referral_code_cache:
            return self._referral_code_cache[referral_code]

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM subscriptions")
        users = cursor.fetchall()
        conn.close()

        for user in users:
            user_id = user["user_id"]
            hash_obj = hashlib.md5(user_id.encode())
            code = f"ref_{hash_obj.hexdigest()[:8]}"
            if code == referral_code:
                self._referral_code_cache[referral_code] = user_id
                return user_id

        return None


# ============== Subscription Skill ==============
class SubscriptionSkill:
    """Check subscription status, start trial."""

    def __init__(self):
        self._sub_service = SimpleSubscriptionService(DB_PATH)

    async def execute(self, user_id: str, message: str) -> dict:
        msg_lower = message.lower().strip()

        if msg_lower in ['trial', '/trial', 'start trial']:
            result = self._sub_service.start_trial(user_id, days=7)
            if result.get('success'):
                trial_ends = result['trial_ends_at'][:10]
                return {
                    'success': True,
                    'data': {
                        '_markdown': f"Your 7-day free trial has started! You now have access to Starter features.\n\nTrial ends: {trial_ends}",
                    }
                }
            return {'success': False, 'error': result.get('error', 'Failed to start trial')}

        # Default: show subscription status
        status = self._sub_service.get_subscription_status(user_id)
        lines = [
            f"Plan: {status['plan_display_name']}",
            f"Queries per day: {'Unlimited' if status['queries_per_day'] == -1 else status['queries_per_day']}",
        ]

        if status['is_in_trial']:
            lines.append(f"Trial: {status['trial_days_left']} days left")

        if status['referral_bonus_days'] > 0:
            lines.append(f"Referral bonus: {status['referral_bonus_days']} days")

        if status['pro_bonus_months'] > 0:
            lines.append(f"Pro bonus: {status['pro_bonus_months']} months")

        remaining = self._sub_service.check_query_limit(user_id)
        if remaining['allowed']:
            if remaining['queries_remaining'] > 0:
                lines.append(f"Queries remaining today: {remaining['queries_remaining']}")
        else:
            lines.append(f"Daily limit reached. Upgrade to Pro for unlimited.")

        return {
            'success': True,
            'data': {'_markdown': '\n'.join(lines)}
        }


# ============== Referral Skill ==============
class ReferralSkill:
    """Handle referral: show link, stats, process codes."""

    def __init__(self):
        self._referral_service = SimpleReferralService(DB_PATH)
        self._sub_service = SimpleSubscriptionService(DB_PATH)

    async def execute(self, user_id: str, message: str) -> dict:
        msg_lower = message.lower().strip()

        if msg_lower in ['link', '/referral', 'my link', 'stats', 'my stats', 'referral stats']:
            stats = self._referral_service.get_referral_stats(user_id)
            referral_link = self._referral_service.get_referral_link(user_id)
            lines = [
                f"Your referral link: {referral_link}",
                f"Referrals: {stats['referral_count']}",
                f"Bonus days earned: {stats['total_bonus_days']}",
            ]
            if stats['pro_bonus_months'] > 0:
                lines.append(f"Pro bonus: {stats['pro_bonus_months']} months")
                lines.append("You have permanent Pro access!")
            elif stats['referral_count'] >= 3:
                lines.append("Each new referral = 1 month Pro for you!")
            else:
                needed = max(0, 3 - stats['referral_count'])
                lines.append(f"{needed} more referral(s) for 1 month Pro!")

            return {
                'success': True,
                'data': {'_markdown': '\n'.join(lines)}
            }

        # Process a referral code (e.g., "ref_abc12345")
        if msg_lower.startswith('ref_'):
            referrer_id = self._referral_service._decode_referral_code(msg_lower)
            if referrer_id is None:
                return {'success': False, 'error': 'Invalid referral code.'}
            if referrer_id == user_id:
                return {'success': False, 'error': 'You cannot use your own referral code.'}

            result = self._referral_service.process_referral(referrer_id, user_id)
            if result['success']:
                return {
                    'success': True,
                    'data': {
                        '_markdown': f"Referral bonus applied!\n\n{result['message']}"
                    }
                }
            return {'success': False, 'error': result.get('message', 'Failed to process referral')}

        # Default: show referral info
        stats = self._referral_service.get_referral_stats(user_id)
        return {
            'success': True,
            'data': {
                '_markdown': f"Your referral link: ref_{hashlib.md5(user_id.encode()).hexdigest()[:8]}\n\nShare it with friends — both of you get 7 bonus days!\n3+ referrals = 1 month Pro per referral!"
            }
        }


# ============== Onboarding Skill ==============
class OnboardingSkill:
    """
    Two-track onboarding funnel:
      - Step 0: Plan selection (Basic vs Pro trial)
      - Step 1: Guided first action (track-specific)
      - Step 2: Feature demo completion + referral
      - Upsell triggers: limit hit, basic-user accessing Pro features
    """

    BASIC_PLAN_ID = 1
    PRO_PLAN_ID = 2
    TRIAL_DAYS = 7
    UPSELL_THRESHOLD = 3  # queries before prompting Pro upgrade

    # Step constants
    STEP_WELCOME = 0      # Show welcome + plan selection
    STEP_PLAN_SELECT = 1  # Await A or P choice
    STEP_GUIDED_ACTION = 2 # User is trying features
    STEP_DEMO_COMPLETE = 3

    def __init__(self):
        self._sub_service = SimpleSubscriptionService(DB_PATH)
        self._referral_service = SimpleReferralService(DB_PATH)

    def _get_conn(self):
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_onboarding_state(self, user_id: str) -> dict:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Migration: add new columns if schema is from old version
        cursor.execute("PRAGMA table_info(user_onboarding)")
        columns = {row[1] for row in cursor.fetchall()}
        if "chosen_track" not in columns:
            cursor.execute("ALTER TABLE user_onboarding ADD COLUMN chosen_track TEXT DEFAULT NULL")
        if "queries_in_session" not in columns:
            cursor.execute("ALTER TABLE user_onboarding ADD COLUMN queries_in_session INTEGER DEFAULT 0")
        if "completed_at" not in columns:
            cursor.execute("ALTER TABLE user_onboarding ADD COLUMN completed_at TEXT DEFAULT NULL")
        conn.commit()

        cursor.execute(
            "SELECT user_id, onboarding_step, chosen_track, queries_in_session, "
            "onboarding_started_at, completed_at FROM user_onboarding WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "user_id": row[0],
                "step": row[1],
                "track": row[2],
                "queries_in_session": row[3] or 0,
                "started_at": row[4],
                "completed_at": row[5]
            }
        return {"step": self.STEP_WELCOME, "track": None, "queries_in_session": 0}

    def _update_onboarding_state(self, user_id: str, step: int, track: str = None, queries: int = None):
        from datetime import datetime
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        if step == self.STEP_WELCOME:
            # Just set step=1 to advance from welcome to plan select
            cursor.execute('''
                INSERT INTO user_onboarding (user_id, onboarding_step, onboarding_started_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    onboarding_step = excluded.onboarding_step,
                    onboarding_started_at = COALESCE(user_onboarding.onboarding_started_at, excluded.onboarding_started_at)
            ''', (user_id, step, now))
        elif track is not None:
            cursor.execute('''
                INSERT INTO user_onboarding (user_id, onboarding_step, chosen_track, queries_in_session, onboarding_started_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    onboarding_step = excluded.onboarding_step,
                    chosen_track = excluded.chosen_track,
                    queries_in_session = COALESCE(excluded.queries_in_session, queries_in_session),
                    onboarding_started_at = COALESCE(user_onboarding.onboarding_started_at, excluded.onboarding_started_at)
            ''', (user_id, step, track, queries or 0, now))
        else:
            cursor.execute('''
                INSERT INTO user_onboarding (user_id, onboarding_step, completed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    onboarding_step = excluded.onboarding_step,
                    completed_at = CASE WHEN excluded.onboarding_step = 3 THEN ? ELSE user_onboarding.completed_at END
            ''', (user_id, step, now if step == self.STEP_DEMO_COMPLETE else now, now if step == self.STEP_DEMO_COMPLETE else now))

        conn.commit()
        conn.close()

    def _increment_queries(self, user_id: str) -> int:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_onboarding (user_id, queries_in_session)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                queries_in_session = (user_onboarding.queries_in_session + 1)
        ''', (user_id,))
        conn.commit()
        cursor.execute('SELECT queries_in_session FROM user_onboarding WHERE user_id = ?', (user_id,))
        q = cursor.fetchone()
        conn.close()
        return q[0] if q else 0

    def _get_referral_link(self, user_id: str) -> str:
        return self._referral_service.get_referral_link(user_id)

    def _build_upgrade_cta(self, user_id: str) -> str:
        """Build a Pro upgrade CTA with user's referral link."""
        referral_link = self._get_referral_link(user_id)
        return f"""
━━━━━━━━━━━━━━━━━━━━━━━
🚀 **Unlock Pro — $29/month**
━━━━━━━━━━━━━━━━━━━━━━━
✓ Unlimited queries (no daily cap)
✓ All feed formulas (Nursery, Breeder, Broiler, Layer...)
✓ Customer management CRM
✓ AI-powered nutrition analysis vs NRC standards
✓ Priority support

Share to extend your access:
🔗 {referral_link}

Each friend who joins = +7 days Pro FREE!
3+ referrals = each gets 1 month Pro FREE."""

    async def execute(self, user_id: str, message: str) -> dict:
        message_lower = message.lower().strip()
        state = self._get_onboarding_state(user_id)
        sub = self._sub_service.get_subscription_status(user_id)

        # === STEP 0: Welcome — show plan selection to new/free users ===
        if state["step"] == self.STEP_WELCOME:
            # Check if user already has an active trial or Pro
            is_trial = sub.get("is_in_trial")
            plan_name = sub.get("plan_name", "free")
            trial_days_left = sub.get("trial_days_left", 0)

            if plan_name == "pro":
                return {
                    "success": True,
                    "data": {
                        "_markdown": """🦅 **You're a Pro user!**

Welcome back. Here's your quick-start menu:

1️⃣ **Price Check** — corn, soybean meal, wheat...
2️⃣ **Formula Cost** — nursery, grower, finisher, broiler, layer...
3️⃣ **Customer CRM** — add, search, manage customers
4️⃣ **Nutrition Analysis** — compare vs NRC standards
5️⃣ **Referral Stats** — see your referral count & bonus days

What would you like to try?"""
                    }
                }

            if is_trial and trial_days_left > 0:
                return {
                    "success": True,
                    "data": {
                        "_markdown": f"""👋 Welcome back! Your **Pro trial** has {trial_days_left} days left.

Here's what you can do:

1️⃣ **Price Check** — live ingredient prices
2️⃣ **Formula Cost** — all formula types (Starter, Grower, Finisher...)
3️⃣ **Customer CRM** — manage your feed customers
4️⃣ **Nutrition Analysis** — AI vs NRC standard comparison
5️⃣ **Referral Program** — share your link for bonus days

What would you like to try?"""
                    }
                }

            # New user or free user — show plan selection, advance to STEP_PLAN_SELECT
            self._update_onboarding_state(user_id, self.STEP_PLAN_SELECT)
            return {
                "success": True,
                "data": {
                    "_markdown": """🐔 **Welcome to FeedPilot AI!**
Your pocket feed formulation assistant.

━━━━━━━━━━━━━━━━━━━━━━━
**Choose your plan:**
━━━━━━━━━━━━━━━━━━━━━━━

**Type A** — Basic (FREE)
• 10 price queries/day
• Price lookup (corn, soybean meal, wheat...)
• Basic formula cost calculation
• Good for trying things out

**Type P** — Pro Trial (7 DAYS FREE)
• Everything in Basic, PLUS:
• ✦ Unlimited queries
• ✦ All feed formulas (Nursery, Breeder, Broiler, Layer, Finisher...)
• ✦ Customer CRM management
• ✦ AI nutrition analysis vs NRC standards
• ✦ Price trend alerts
• No credit card required

━━━━━━━━━━━━━━━━━━━━━━━
**Type A or P to get started →**
━━━━━━━━━━━━━━━━━━━━━━━
"""
                }
            }

        # === STEP 1: User chose a track ===
        elif state["step"] == self.STEP_PLAN_SELECT:
            chosen = None
            if message_lower in ["a", "basic", "free", "1"]:
                chosen = "basic"
                self._update_onboarding_state(user_id, self.STEP_GUIDED_ACTION, track="basic")
                return {
                    "success": True,
                    "data": {
                        "_markdown": """✅ **Basic plan activated** (10 queries/day)

Let's start with a quick demo — try checking an ingredient price:

**Type an ingredient name** (e.g. corn, soybean meal, wheat, fish meal)
or type **'all'** to see all prices."""
                    }
                }

            elif message_lower in ["p", "pro", "trial", "2", "pro trial"]:
                chosen = "pro"
                self._sub_service.start_trial(user_id, days=self.TRIAL_DAYS)
                self._update_onboarding_state(user_id, self.STEP_GUIDED_ACTION, track="pro")
                return {
                    "success": True,
                    "data": {
                        "_markdown": f"""🎁 **{self.TRIAL_DAYS}-day Pro trial ACTIVATED!**
No credit card required.

You now have full access to:
✓ Unlimited queries
✓ All feed formulas
✓ Customer CRM
✓ AI nutrition analysis

**Let's start with your first Pro feature — try calculating a formula cost:**

Type your formula, for example:
`corn 60%, soybean meal 25%, premix 5%, limestone 10%`

Or type **'example'** to see a sample nursery diet calculation with full cost breakdown."""
                    }
                }

            elif message_lower in ["upgrade", "up", "pro", "subscribe", "buy"]:
                # Free user requesting Pro directly
                self._sub_service.start_trial(user_id, days=self.TRIAL_DAYS)
                self._update_onboarding_state(user_id, self.STEP_GUIDED_ACTION, track="pro")
                return {
                    "success": True,
                    "data": {
                        "_markdown": f"""🎁 **{self.TRIAL_DAYS}-day Pro trial ACTIVATED!**

Let's calculate your first formula. Type your ingredients:
`corn 60%, soybean meal 25%, premix 5%`

Or type **'example'** for a full nursery diet cost breakdown."""
                    }
                }

            else:
                return {
                    "success": True,
                    "data": {
                        "_markdown": "Please type **A** for Basic (free) or **P** for Pro trial (7 days free) to continue."
                    }
                }

        # === STEP 2: Guided first action ===
        if state["step"] == self.STEP_GUIDED_ACTION:
            track = state.get("track", "basic")

            # Increment query count
            q_count = self._increment_queries(user_id)

            # Basic user hitting upsell threshold → trigger upgrade CTA
            if track == "basic" and q_count >= self.UPSELL_THRESHOLD:
                return {
                    "success": True,
                    "data": {
                        "_markdown": f"""🔔 **You've used {q_count} queries on Basic**

You've seen the basics — ready to unlock full access?

{self._build_upgrade_cta(user_id)}

**Just type P or 'upgrade' to start your free Pro trial →**"""
                    }
                }

            # Continue guided action based on track
            if track == "basic":
                return {
                    "success": True,
                    "data": {
                        "_markdown": f"""📊 **Basic plan: {10 - q_count} queries left today**

Try checking prices or calculating a simple formula cost.

**Quick examples:**
• "corn price" — check corn
• "soybean meal price" — check SBM
• "example formula" — see a sample calculation

**Type 'upgrade'** anytime to unlock Pro features!"""
                    }
                }
            else:  # pro track
                return {
                    "success": True,
                    "data": {
                        "_markdown": """🧮 **Pro trial active — unlimited queries!**

Try one of these Pro features:

**Formula Cost** — type your formula:
`corn 60%, soybean meal 25%, premix 5%, limestone 10%`

**Customer CRM** — type:
`add customer John Farm, phone 555-1234`

**Nutrition Analysis** — type:
`analyze Nursery Diet 1 vs NRC standards`

Or type **'example'** for a full nursery diet breakdown with cost + nutrition data."""
                    }
                }

        # === STEP 3: Demo complete — show referral + Pro upsell ===
        if state["step"] == self.STEP_DEMO_COMPLETE:
            referral_link = self._get_referral_link(user_id)
            return {
                "success": True,
                "data": {
                    "_markdown": f"""🎉 **You've completed the demo!**

Your quick-start menu:
• **corn price** — check any ingredient
• **formula cost** — calculate feed cost
• **add customer** — CRM management
• **subscription** — check your plan & usage
• **referral** — share for bonus days

{self._build_upgrade_cta(user_id)}

Keep going with any command, or type **'upgrade'** to start your Pro trial!"""
                }
            }

        # Fallback
        return {
            "success": True,
            "data": {
                "_markdown": """Type **'onboard'** to restart the guided tour, or type any command to continue."""
            }
        }


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
    'reminder': get_reminder_skill,
    'reminders': get_reminder_skill,
    'alert': get_reminder_skill,
    'subscription': SubscriptionSkill,
    'onboarding': OnboardingSkill,
    '/onboard': OnboardingSkill,
    'onboard': OnboardingSkill,
    'getstarted': OnboardingSkill,
    'start': OnboardingSkill,
    'upgrade': OnboardingSkill,
    'free trial': OnboardingSkill,
    'pro trial': OnboardingSkill,
    'referral': ReferralSkill,
    '/referral': ReferralSkill,
    'my referral': ReferralSkill,
    'referral link': ReferralSkill,
    'my link': ReferralSkill,
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