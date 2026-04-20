#!/usr/bin/env python3
"""
FeedSales AI - JSON 数据迁移脚本

将历史 JSON 数据迁移到 SQLite 数据库
"""

import json
import sys
from pathlib import Path
from datetime import date

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository, PriceRepository


def migrate_formulas(json_path: str, repo: FormulaRepository, owner_open_id: str = "default_user"):
    """迁移配方数据"""
    print(f"📦 迁移配方数据：{json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        formulas = json.load(f)
    
    count = 0
    for formula_name, ingredients in formulas.items():
        try:
            # 准备配方数据
            formula_data = {
                "name": formula_name,
                "stage_type": "unknown",
                "notes": "从 JSON 迁移",
                "ingredients": [
                    {"name": name, "ratio": float(ratio)}
                    for name, ratio in ingredients.items()
                ]
            }
            
            # 创建配方
            repo.create_formula(owner_open_id, formula_data)
            count += 1
            print(f"  ✅ 迁移配方：{formula_name}")
            
        except Exception as e:
            print(f"  ❌ 迁移失败 {formula_name}: {e}")
    
    print(f"✅ 配方迁移完成：{count}/{len(formulas)}")
    return count


def migrate_prices(json_path: str, repo: PriceRepository, owner_open_id: str = "default_user"):
    """迁移价格数据"""
    print(f"📦 迁移价格数据：{json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        prices = json.load(f)
    
    count = 0
    for item in prices:
        try:
            # 准备价格数据
            price_data = {
                "ingredient_code": item.get("code", f"ING_{item.get('name', 'UNKNOWN')}"),
                "ingredient_name": item.get("name", "Unknown"),
                "price": float(item.get("price", 0)),
                "currency": item.get("currency", "CNY"),
                "unit": item.get("unit", "ton"),
                "source": item.get("source", "json"),
                "price_date": item.get("date", str(date.today()))
            }
            
            # 保存价格
            repo.save_price(owner_open_id, price_data)
            count += 1
            print(f"  ✅ 迁移价格：{price_data['ingredient_name']}")
            
        except Exception as e:
            print(f"  ❌ 迁移失败 {item.get('name', 'Unknown')}: {e}")
    
    print(f"✅ 价格迁移完成：{count}/{len(prices)}")
    return count


def main():
    """主函数"""
    print("=" * 60)
    print("FeedSales AI - JSON 数据迁移")
    print("=" * 60)
    
    # 初始化数据库
    pool = DatabasePool("data/feed_sales.db")
    formula_repo = FormulaRepository(pool)
    price_repo = PriceRepository(pool)
    
    # 数据目录
    data_dir = Path("data/json")
    
    if not data_dir.exists():
        print(f"⚠️ JSON 数据目录不存在：{data_dir}")
        print("跳过迁移，直接使用空数据库")
        return True
    
    # 迁移配方
    formulas_json = data_dir / "formulas.json"
    if formulas_json.exists():
        migrate_formulas(str(formulas_json), formula_repo)
    
    # 迁移价格
    prices_json = data_dir / "prices.json"
    if prices_json.exists():
        migrate_prices(str(prices_json), price_repo)
    
    print("\n" + "=" * 60)
    print("✅ 数据迁移完成！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
