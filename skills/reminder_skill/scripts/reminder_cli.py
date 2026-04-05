#!/usr/bin/env python3
"""
Reminder CLI - 提醒命令行工具

用于创建、查看、删除提醒。
"""
import argparse
import json
import sys
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from reminder_service import ReminderService, normalize_ingredient, normalize_formula


# 数据库路径 - 使用绝对路径
DB_PATH = Path("/home/kenny/.openclaw/workspace-feedsales/data/feed_sales.db")


def create_reminder(args):
    """创建提醒"""
    service = ReminderService(str(DB_PATH))
    
    if args.type == "price":
        # 标准化原料名称
        ingredient_info = normalize_ingredient(args.ingredient)
        if not ingredient_info:
            print(f"❌ 无法识别原料: {args.ingredient}")
            print("支持的原料: 豆粕, 玉米, 鱼粉, DDGS, 小麦, 麸皮, 豆油, 磷酸氢钙, 石粉, 盐, 赖氨酸, 蛋氨酸, 苜蓿草粉")
            return 1
        
        reminder = service.create_reminder(
            user_id=args.user_id,
            reminder_type="price",
            threshold=args.threshold,
            condition=args.condition,
            ingredient=ingredient_info["name"],
            ingredient_code=ingredient_info["code"]
        )
        
        print(f"✅ 已创建价格提醒！")
        print(f"   原料: {ingredient_info['name']}")
        print(f"   条件: {'超过' if args.condition == 'above' else '低于'} ${args.threshold}/吨")
        print(f"   提醒 ID: {reminder['id']}")
        
    elif args.type == "formula_cost":
        # 标准化配方名称
        formula_info = normalize_formula(args.formula)
        if not formula_info:
            print(f"❌ 无法识别配方: {args.formula}")
            print("支持的配方: 保育料, 育肥料, 生长料, 肉鸡料, 蛋鸡料, 肉牛育肥料")
            return 1
        
        reminder = service.create_reminder(
            user_id=args.user_id,
            reminder_type="formula_cost",
            threshold=args.threshold,
            condition=args.condition,
            formula=formula_info["name"],
            formula_id=formula_info["id"]
        )
        
        print(f"✅ 已创建成本提醒！")
        print(f"   配方: {formula_info['name']}")
        print(f"   条件: {'超过' if args.condition == 'above' else '低于'} ${args.threshold}/吨")
        print(f"   提醒 ID: {reminder['id']}")
    
    return 0


def list_reminders(args):
    """查看提醒"""
    service = ReminderService(str(DB_PATH))
    reminders = service.list_reminders(args.user_id)
    
    if not reminders:
        print("📋 你还没有设置任何提醒")
        return 0
    
    print(f"📋 你的提醒列表 ({len(reminders)} 个)：\n")
    
    for i, r in enumerate(reminders, 1):
        if r["type"] == "price":
            target = r["ingredient"]
        else:
            target = r["formula"]
        
        condition = "超过" if r["condition"] == "above" else "低于"
        status = "✅" if r["enabled"] else "⏸️"
        
        print(f"{i}. {status} {target} {condition} ${r['threshold']}/吨")
        print(f"   ID: {r['id'][:8]}...")
        print()
    
    return 0


def delete_reminder(args):
    """删除提醒"""
    service = ReminderService(str(DB_PATH))
    
    # 先查看提醒
    reminder = service.get_reminder(args.reminder_id, args.user_id)
    if not reminder:
        print("❌ 未找到该提醒或无权限删除")
        return 1
    
    # 确认删除
    if reminder["type"] == "price":
        target = reminder["ingredient"]
    else:
        target = reminder["formula"]
    
    condition = "超过" if reminder["condition"] == "above" else "低于"
    print(f"要删除这个提醒吗？")
    print(f"  {target} {condition} ${reminder['threshold']}/吨")
    print()
    
    if not args.force:
        confirm = input("确认删除？(y/N): ")
        if confirm.lower() != "y":
            print("已取消")
            return 0
    
    # 执行删除
    success = service.delete_reminder(args.reminder_id, args.user_id)
    if success:
        print(f"✅ 已删除")
        return 0
    else:
        print("❌ 删除失败")
        return 1


def check_reminders(args):
    """检查所有提醒（用于 cron 任务）"""
    service = ReminderService(str(DB_PATH))
    reminders = service.get_all_enabled_reminders()
    
    print(f"检查 {len(reminders)} 个启用的提醒...")
    
    # TODO: 实现价格检查和通知逻辑
    # 这里需要：
    # 1. 查询最新价格
    # 2. 检查每个提醒的条件
    # 3. 触发时发送通知
    
    for r in reminders:
        print(f"  - {r['user_id']}: {r.get('ingredient') or r.get('formula')}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(description="FeedPilot AI 提醒工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # create 命令
    create_parser = subparsers.add_parser("create", help="创建提醒")
    create_parser.add_argument("--user-id", required=True, help="用户 ID")
    create_parser.add_argument("--type", choices=["price", "formula_cost"], required=True, help="提醒类型")
    create_parser.add_argument("--threshold", type=float, required=True, help="阈值 (美元/吨)")
    create_parser.add_argument("--condition", choices=["above", "below"], default="above", help="条件")
    create_parser.add_argument("--ingredient", help="原料名称 (type=price 时)")
    create_parser.add_argument("--formula", help="配方名称 (type=formula_cost 时)")
    create_parser.set_defaults(func=create_reminder)
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="查看提醒")
    list_parser.add_argument("--user-id", required=True, help="用户 ID")
    list_parser.set_defaults(func=list_reminders)
    
    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除提醒")
    delete_parser.add_argument("--user-id", required=True, help="用户 ID")
    delete_parser.add_argument("--reminder-id", required=True, help="提醒 ID")
    delete_parser.add_argument("--force", action="store_true", help="强制删除，不确认")
    delete_parser.set_defaults(func=delete_reminder)
    
    # check 命令
    check_parser = subparsers.add_parser("check", help="检查提醒")
    check_parser.set_defaults(func=check_reminders)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
