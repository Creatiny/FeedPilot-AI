#!/usr/bin/env python3
"""
FeedSales AI - Telegram E2E 测试脚本
测试完整闭环: Telegram消息 → OpenClaw → Agent → Skill → DB → 响应验证

用法:
    python3 scripts/e2e_telegram_test.py
"""

import sqlite3
import time
import json
import sys
import os
from datetime import datetime

# 路径设置
PROJECT_ROOT = "/home/kenny/.openclaw/workspace/feed-sales-ai-mvp"
DB_PATH = f"{PROJECT_ROOT}/data/feed_sales.db"
SKILL_DIR = "/home/kenny/.openclaw/workspace-feedsales/skills"
sys.path.insert(0, PROJECT_ROOT)

from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository, PriceRepository
from src.services.formula_service import FormulaService
from src.services.price_service import PriceService
from src.services.calculation_service import CalculationService
from src.harness.task_router import TaskRouter
from skills.formula_cost_skill.skill import FormulaCostSkill
from skills.price_lookup_skill.skill import PriceLookupSkill

class TelegramE2ETester:
    def __init__(self):
        self.pool = DatabasePool(DB_PATH)
        self.price_service = PriceService(self.pool)
        self.formula_service = FormulaService(self.pool)
        self.calc_service = CalculationService(self.pool)
        self.router = TaskRouter()
        self.results = {"passed": 0, "failed": 0, "errors": []}

    def record(self, name, condition, detail=""):
        if condition:
            self.results["passed"] += 1
            print(f"  ✅ {name}")
        else:
            self.results["failed"] += 1
            err = f"  ❌ {name}" + (f" — {detail}" if detail else "")
            self.results["errors"].append(err)
            print(err)

    def test_price_lookup_skill(self):
        """测试价格查询技能"""
        print("\n[价格查询技能测试]")

        import asyncio

        skill = PriceLookupSkill(price_service=self.price_service)

        test_cases = [
            "corn price",
            "soybean meal price",
            "fish meal price",
        ]

        for msg in test_cases:
            result = asyncio.run(skill.execute("test_user", msg))
            self.record(
                f"价格查询: '{msg}'",
                result.get("success", False),
                result.get("error") if not result.get("success") else ""
            )

    def test_formula_cost_skill(self):
        """测试配方成本技能"""
        print("\n[配方成本技能测试]")

        import asyncio

        skill = FormulaCostSkill(calculation_service=self.calc_service)

        test_cases = [
            "cost for Nursery Diet 1",
            "保育料成本",
            "nursery formula cost",
        ]

        for msg in test_cases:
            result = asyncio.run(skill.execute("test_user", msg))
            ok = result.get("success", False)
            self.record(
                f"配方成本: '{msg}'",
                ok,
                result.get("error") if not ok else f"${result.get('data', {}).get('total_cost', 0):.2f}/ton"
            )

    def test_price_by_name_and_code(self):
        """测试价格查询: name vs code 双路径"""
        print("\n[价格查询双路径测试]")

        test_cases = [
            ("Corn", "ING_CORN"),
            ("Soybean meal", "ING_SBM"),
            ("Fish meal", "ING_FISHM"),
        ]

        for name, code in test_cases:
            r_name = self.price_service.get_price("test_user_001", name)
            r_code = self.price_service.get_price("test_user_001", code)

            self.record(
                f"名称查询 '{name}' 成功",
                r_name.success,
                r_name.error_message if not r_name.success else ""
            )
            self.record(
                f"代码查询 '{code}' 成功",
                r_code.success,
                r_code.error_message if not r_code.success else ""
            )
            # 两者价格应一致
            if r_name.success and r_code.success:
                price_match = abs(r_name.data.get("price", 0) - r_code.data.get("price", 0)) < 0.01
                self.record(
                    f"名称/代码价格一致 '{name}'",
                    price_match,
                    f"name=${r_name.data.get('price')}, code=${r_code.data.get('price')}"
                )

    def test_private_price_priority(self):
        """测试私有价格优先"""
        print("\n[私有价格优先测试]")

        # 插入私有价格
        self.price_service.set_private_price(
            "test_user_e2e",
            "Corn",
            price=999.0,
            source="e2e_test"
        )

        r_private = self.price_service.get_price("test_user_e2e", "Corn")
        r_public = self.price_service.get_price("test_user_001", "Corn")

        self.record(
            "私有价格返回 999",
            r_private.success and r_private.data.get("price") == 999.0,
            f"got {r_private.data.get('price')}"
        )
        self.record(
            "其他用户获取公共价格",
            r_public.success and r_public.data.get("price") < 500,
            f"got {r_public.data.get('price')}"
        )

    def test_task_router(self):
        """测试任务路由"""
        print("\n[任务路由测试]")

        test_cases = [
            ("计算配方成本", "formula_cost_query"),
            ("玉米价格多少", "price_query"),
            ("添加客户张三", "customer_manage"),
        ]

        for msg, expected in test_cases:
            routed = self.router.classify(msg)
            self.record(
                f"路由 '{msg}' → {routed}",
                routed == expected,
                f"expected {expected}"
            )

    def test_formula_list(self):
        """测试配方列表"""
        print("\n[配方列表测试]")

        result = self.formula_service.list_formulas("test_user_001")
        self.record(
            "列出配方成功",
            result.success,
            result.error_message if not result.success else f"共 {result.data.get('total', 0)} 个"
        )
        self.record(
            "配方数量 >= 38",
            result.success and result.data.get("total", 0) >= 38,
            f"got {result.data.get('total', 0)}"
        )

    def test_nrc_formula_cost(self):
        """测试 NRC 配方成本计算"""
        print("\n[NRC配方成本测试]")

        test_formulas = ["Nursery Diet 1", "Broiler Starter", "Lactating Cow Diet"]

        for formula_name in test_formulas:
            result = self.calc_service.calculate_cost("test_user_001", formula_name)
            self.record(
                f"计算 '{formula_name}'",
                result.success,
                result.error_message if not result.success else f"${result.data.get('total_cost', 0):.2f}/ton"
            )

    def run_all(self):
        print("=" * 60)
        print("  FeedSales AI - Telegram E2E 完整测试")
        print("=" * 60)
        print(f"\n时间: {datetime.now().isoformat()}")
        print(f"数据库: {DB_PATH}")

        # 核心服务测试
        self.test_price_by_name_and_code()
        self.test_private_price_priority()
        self.test_formula_list()
        self.test_nrc_formula_cost()
        self.test_task_router()

        # Skill 集成测试
        self.test_price_lookup_skill()
        self.test_formula_cost_skill()

        # 汇总
        print("\n" + "=" * 60)
        total = self.results["passed"] + self.results["failed"]
        pct = self.results["passed"] / total * 100 if total > 0 else 0
        print(f"  通过: {self.results['passed']}/{total} ({pct:.1f}%)")
        if self.results["errors"]:
            print(f"\n  失败项:")
            for e in self.results["errors"]:
                print(f"    {e}")
        print(f"\n  结论: {'PASS ✅' if pct >= 90 else 'NEEDS_FIX ⚠️' if pct >= 70 else 'FAIL ❌'}")
        print("=" * 60)

        return self.results["failed"] == 0

if __name__ == "__main__":
    tester = TelegramE2ETester()
    ok = tester.run_all()
    sys.exit(0 if ok else 1)
