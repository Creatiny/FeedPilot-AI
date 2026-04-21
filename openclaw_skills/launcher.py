#!/usr/bin/env python3
"""
FeedSales Skills - Unified Launcher

统一的技能启动器，处理依赖注入和执行
支持查询限制、试用期管理、推荐机制
"""

import sys
import os
import json
import argparse
import asyncio
from pathlib import Path

# Set up paths - auto-detect project root from this file location
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'data' / 'feed_sales.db'

# Add base directory to Python path (not src)
sys.path.insert(0, str(BASE_DIR))


def get_subscription_service():
    """获取订阅服务实例"""
    from src.database.pool import DatabasePool
    from src.services.subscription_service import SubscriptionService
    
    db_pool = DatabasePool(str(DB_PATH))
    return SubscriptionService(db_pool)


def get_referral_service():
    """获取推荐服务实例"""
    from src.database.pool import DatabasePool
    from src.services.referral_service import ReferralService
    
    db_pool = DatabasePool(str(DB_PATH))
    return ReferralService(db_pool)


def check_query_limit(user_id: str, skill_name: str) -> dict:
    """
    检查查询限制
    
    Returns:
        None if allowed, or error dict if limit exceeded
    """
    from src.middleware.query_limit_middleware import QueryLimitMiddleware
    
    sub_service = get_subscription_service()
    middleware = QueryLimitMiddleware(sub_service)
    
    result = middleware.check_and_record(user_id, skill_name)
    
    if not result['allowed']:
        return {
            'success': False,
            'error': 'query_limit_exceeded',
            'message': result.get('message', 'Query limit exceeded'),
            'data': result
        }
    
    return None


def run_formula_cost(user_id: str, message: str) -> dict:
    """运行配方成本计算技能"""
    # 检查查询限制（已包含记录使用）
    limit_error = check_query_limit(user_id, 'formula-cost')
    if limit_error:
        return limit_error
    
    from src.database.pool import DatabasePool
    from src.services.calculation_service import CalculationService
    from skills.formula_cost_skill.skill import FormulaCostSkill
    
    db_pool = DatabasePool(str(DB_PATH))
    calculation_service = CalculationService(db_pool)
    skill = FormulaCostSkill(calculation_service)
    
    return asyncio.run(skill.execute(user_id, message))


def run_price_lookup(user_id: str, message: str) -> dict:
    """运行价格查询技能"""
    # 检查查询限制（已包含记录使用）
    limit_error = check_query_limit(user_id, 'price-lookup')
    if limit_error:
        return limit_error
    
    from src.database.pool import DatabasePool
    from src.services.price_service import PriceService
    from skills.price_lookup_skill.skill import PriceLookupSkill
    
    db_pool = DatabasePool(str(DB_PATH))
    price_service = PriceService(db_pool)
    skill = PriceLookupSkill(price_service)
    
    return asyncio.run(skill.execute(user_id, message))


def run_customer_record(user_id: str, message: str) -> dict:
    """运行客户记录管理技能"""
    # 检查查询限制（已包含记录使用）
    limit_error = check_query_limit(user_id, 'customer-record')
    if limit_error:
        return limit_error
    
    from src.database.pool import DatabasePool
    from src.services.customer_service import CustomerService
    from skills.customer_record_skill.skill import CustomerRecordSkill
    
    db_pool = DatabasePool(str(DB_PATH))
    customer_service = CustomerService(db_pool)
    skill = CustomerRecordSkill(customer_service)
    
    return asyncio.run(skill.execute(user_id, message))


def run_nutrition_analysis(user_id: str, message: str) -> dict:
    """运行营养分析技能"""
    # 检查查询限制（已包含记录使用）
    limit_error = check_query_limit(user_id, 'nutrition-analysis')
    if limit_error:
        return limit_error
    
    from src.database.pool import DatabasePool
    from src.services.formula_service import FormulaService
    from skills.nutrition_analysis_skill.skill import NutritionAnalysisSkill
    
    db_pool = DatabasePool(str(DB_PATH))
    formula_service = FormulaService(db_pool)
    skill = NutritionAnalysisSkill(formula_service)
    
    return asyncio.run(skill.execute(user_id, message))


def run_onboarding(user_id: str, message: str) -> dict:
    """运行新用户引导技能"""
    # onboarding 不检查限制
    from openclaw_skills.onboarding.skill import handle_onboarding
    return handle_onboarding(user_id, message)


def run_subscription(user_id: str, message: str) -> dict:
    """运行订阅管理技能"""
    # subscription 不检查限制
    sub_service = get_subscription_service()
    
    # 解析命令
    message = message.strip().lower()
    
    if message in ['status', '/status', 'subscription']:
        # 查询订阅状态
        status = sub_service.get_subscription_status(user_id)
        return {
            'success': True,
            'message': format_subscription_status(status),
            'data': status
        }
    
    elif message in ['trial', '/trial', 'start trial']:
        # 开始试用期
        result = sub_service.start_trial(user_id, days=7)
        return {
            'success': True,
            'message': f"Your 7-day free trial has started! You now have access to Starter features.\n\nTrial ends: {result['trial_ends_at'][:10]}",
            'data': result
        }
    
    elif message in ['upgrade', '/upgrade', 'plans']:
        # 显示升级选项
        return {
            'success': True,
            'message': format_plans_info(),
            'data': {'action': 'show_plans'}
        }
    
    else:
        # 默认显示状态
        status = sub_service.get_subscription_status(user_id)
        return {
            'success': True,
            'message': format_subscription_status(status),
            'data': status
        }


def run_referral(user_id: str, message: str) -> dict:
    """运行推荐机制技能"""
    # referral 不检查限制
    referral_service = get_referral_service()
    
    message_lower = message.strip().lower()
    
    if message_lower in ['link', '/referral', 'my link', 'stats']:
        # 获取推荐统计
        stats = referral_service.get_referral_stats(user_id)
        return {
            'success': True,
            'message': format_referral_stats(stats),
            'data': stats
        }
    
    elif message_lower.startswith('ref_'):
        # 处理推荐码
        result = referral_service.process_referral(
            referral_code=message_lower,
            new_user_id=user_id
        )
        return {
            'success': result['success'],
            'message': result['message'],
            'data': result
        }
    
    else:
        # 默认显示推荐信息
        stats = referral_service.get_referral_stats(user_id)
        return {
            'success': True,
            'message': format_referral_stats(stats),
            'data': stats
        }


def format_referral_stats(stats: dict) -> str:
    """格式化推荐统计信息"""
    lines = [
        "**Your Referral Program**",
        f"Referrals: {stats['referral_count']}",
        f"Bonus days earned: {stats['total_bonus_days']}",
        f"",
        f"Your link: {stats['referral_link']}",
    ]
    
    if stats['is_permanent_free']:
        lines.append("\n🎉 You have permanent free Pro access!")
    elif stats['referral_count'] >= 2:
        lines.append(f"\nOnly {3 - stats['referral_count']} more referral(s) for permanent free Pro!")
    
    lines.append("\nShare your link with friends. When they sign up, you both get 7 extra days free!")
    
    return '\n'.join(lines)


def handle_referral_signup(user_id: str, referrer_id: str) -> dict:
    """处理推荐注册"""
    from src.database.pool import DatabasePool
    import sqlite3
    
    db_pool = DatabasePool(str(DB_PATH))
    
    with db_pool.get_connection() as conn:
        cursor = conn.cursor()
        
        # 检查是否已经注册过
        cursor.execute("""
            SELECT id FROM referrals WHERE referee_id = ?
        """, (user_id,))
        
        if cursor.fetchone():
            return {
                'success': False,
                'message': 'You have already used a referral link.',
                'data': {}
            }
        
        # 检查推荐人是否存在
        cursor.execute("""
            SELECT id FROM users WHERE open_id = ?
        """, (referrer_id,))
        
        if not cursor.fetchone():
            return {
                'success': False,
                'message': 'Invalid referral link.',
                'data': {}
            }
        
        # 不能推荐自己
        if user_id == referrer_id:
            return {
                'success': False,
                'message': 'You cannot refer yourself.',
                'data': {}
            }
        
        # 创建推荐记录
        cursor.execute("""
            INSERT INTO referrals (referrer_id, referee_id, status, bonus_days)
            VALUES (?, ?, 'completed', 7)
        """, (referrer_id, user_id))
        
        # 给双方添加奖励
        sub_service = get_subscription_service()
        sub_service.add_referral_bonus(referrer_id, 7)
        sub_service.add_referral_bonus(user_id, 7)
        
        conn.commit()
    
    return {
        'success': True,
        'message': 'Welcome! You and your friend both received 7 extra days free!',
        'data': {'referrer_id': referrer_id, 'bonus_days': 7}
    }


def format_subscription_status(status: dict) -> str:
    """格式化订阅状态消息"""
    lines = [
        f"**Your Subscription**",
        f"Plan: {status['plan_name']}",
    ]
    
    if status['is_in_trial']:
        lines.append(f"Trial: {status['trial_days_left']} days left")
    
    if status['queries_per_day'] == -1:
        lines.append("Queries: Unlimited")
    else:
        lines.append(f"Queries: {status['queries_per_day']}/day")
    
    if status['referral_bonus_days'] > 0:
        lines.append(f"Bonus days: {status['referral_bonus_days']}")
    
    lines.append("\nType /upgrade to see available plans.")
    
    return '\n'.join(lines)


def format_plans_info() -> str:
    """格式化计划信息"""
    return """**Available Plans**

**Free** - $0
• 3 queries per day
• 5 customers max
• Basic features

**Starter** - $9.9/month
• 50 queries per day
• 50 customers max
• All basic features + reminders

**Pro** - $39.99/month
• Unlimited queries
• 200 customers
• All features + nutrition analysis

Type /trial to start your 7-day free trial!"""


SKILLS = {
    'formula-cost': run_formula_cost,
    'price-lookup': run_price_lookup,
    'customer-record': run_customer_record,
    'nutrition-analysis': run_nutrition_analysis,
    'onboarding': run_onboarding,
    'subscription': run_subscription,
    'referral': run_referral,
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