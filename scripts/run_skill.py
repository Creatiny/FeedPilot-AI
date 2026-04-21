#!/usr/bin/env python3
"""
FeedSales AI - Unified Skill Runner

A command-line entry point for all skills.
Usage: python3 run_skill.py <skill_name> "<user_message>"
"""

import asyncio
import importlib.util
import json
import os
import re
import sys
from typing import Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)
sys.path.insert(0, os.path.join(WORKSPACE, "skills"))

DB_PATH = os.path.join(WORKSPACE, "data", "feed_sales.db")

from src.database.pool import DatabasePool
from src.services.calculation_service import CalculationService
from src.services.customer_service import CustomerService
from src.services.formula_service import FormulaService
from src.services.price_service import PriceService
from src.services.reminder_service import ReminderService


class ServiceResult:
    """Compatibility result object used by local adapters."""

    def __init__(self, success: bool, data=None, source=None, error_code=None, error_message=None):
        self.success = success
        self.data = data if data else {}
        self.source = source
        self.error_code = error_code
        self.error_message = error_message


_DB_POOL = DatabasePool(DB_PATH)


class SkillPriceService:
    def __init__(self):
        self._svc = PriceService(_DB_POOL)

    def get_price(self, user_id: str, ingredient_name: str):
        return self._svc.get_price(user_id, ingredient_name)

    def list_public_prices(self):
        return self._svc.list_public_prices()


class SkillFormulaService:
    def __init__(self):
        self._svc = FormulaService(_DB_POOL)

    def get_formula(self, user_id: str, formula_name: str):
        return self._svc.get_formula(user_id, formula_name)

    def list_formulas(self, user_id: str):
        return self._svc.list_formulas(user_id)


class SkillCalculationService:
    def __init__(self):
        self._svc = CalculationService(_DB_POOL)

    def calculate_cost(self, user_id: str, formula_name: str):
        return self._svc.calculate_cost(user_id, formula_name)


class SkillCustomerService:
    def __init__(self):
        self._svc = CustomerService(_DB_POOL)

    def create_customer(self, user_id: str, data: dict):
        return self._svc.create_customer(user_id, data)

    def list_customers(self, user_id: str):
        return self._svc.list_customers(user_id)

    def get_customer(self, user_id: str, name: str):
        return self._svc.get_customer(user_id, name)

    def update_customer(self, user_id: str, customer_id: int, data: dict):
        return self._svc.update_customer(user_id, customer_id, data)

    def delete_customer(self, user_id: str, customer_id: int):
        return self._svc.delete_customer(user_id, customer_id)


class SkillReminderService:
    def __init__(self):
        self._svc = ReminderService(_DB_POOL)

    def create_reminder(
        self,
        user_id: str,
        reminder_type: str,
        threshold: float,
        condition: str,
        ingredient: Optional[str] = None,
        ingredient_code: Optional[str] = None,
        formula: Optional[str] = None,
        formula_id: Optional[str] = None,
    ):
        return self._svc.create_reminder(
            user_id=user_id,
            reminder_type=reminder_type,
            threshold=threshold,
            condition=condition,
            ingredient=ingredient,
            ingredient_code=ingredient_code,
            formula=formula,
            formula_id=formula_id,
        )

    def list_reminders(self, user_id: str):
        return self._svc.list_reminders(user_id, enabled_only=False)

    def delete_reminder(self, user_id: str, reminder_id: str):
        list_result = self._svc.list_reminders(user_id, enabled_only=False)
        if not list_result.success:
            return list_result

        for reminder in list_result.data.get("reminders", []):
            full_id = str(reminder.get("id", ""))
            if full_id.startswith(reminder_id):
                return self._svc.delete_reminder(full_id, user_id)

        return ServiceResult(success=False, error_message=f"Reminder '{reminder_id}' not found")


_INGREDIENT_MAP = {
    "corn": {"name": "Corn, No.2 Yellow", "code": "ING_CORN"},
    "soybean": {"name": "Soybean meal, 48%", "code": "ING_SBM"},
    "soybean meal": {"name": "Soybean meal, 48%", "code": "ING_SBM"},
    "sbm": {"name": "Soybean meal, 48%", "code": "ING_SBM"},
    "wheat": {"name": "Wheat, grain", "code": "ING_WHEAT"},
    "barley": {"name": "Barley", "code": "ING_BARLEY"},
    "fish meal": {"name": "Fish meal, 65%", "code": "ING_FISHM"},
    "ddgs": {"name": "DDGS, 28%", "code": "ING_DDGS"},
    "limestone": {"name": "Limestone", "code": "ING_LIME"},
    "lysine": {"name": "L-Lysine HCl", "code": "ING_LYS"},
    "methionine": {"name": "DL-Methionine", "code": "ING_MET"},
}

_FORMULA_MAP = {
    "nursery": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
    "nursery diet": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
    "grower": {"name": "Grower Diet 1", "id": "FORMULA_GROWER_1"},
    "finishing": {"name": "Finishing Diet", "id": "FORMULA_FINISHING"},
    "broiler": {"name": "Broiler Starter", "id": "FORMULA_BROILER_STARTER"},
    "layer": {"name": "Layer Diet", "id": "FORMULA_LAYER"},
}


class ReminderSkill:
    def __init__(self, service: SkillReminderService):
        self.service = service

    async def execute(self, user_id: str, message: str) -> dict:
        msg_lower = message.lower()

        if "list" in msg_lower or "show" in msg_lower or "my reminder" in msg_lower or "reminders" in msg_lower:
            result = self.service.list_reminders(user_id)
            if result.success:
                reminders = result.data["reminders"]
                if not reminders:
                    return {
                        "success": True,
                        "message": "You have no reminders set. Create one:\n- Alert when corn > $90/ton\n- Remind me when soybean meal < $350/ton",
                    }
                lines = ["| ID | Type | Target | Condition |", "|----|------|--------|-----------|"]
                for r in reminders:
                    target = r.get("ingredient") or r.get("formula", "Unknown")
                    cond = "above" if r.get("condition") == "above" else "below"
                    lines.append(f"| {str(r.get('id', ''))[:8]} | {r.get('type')} | {target} | {cond} ${r.get('threshold')} |")
                return {"success": True, "message": "\n".join(lines)}
            return {"success": False, "error": result.error_message}

        if "delete" in msg_lower or "remove" in msg_lower or "cancel" in msg_lower:
            id_match = re.search(r"[a-f0-9]{8}", msg_lower)
            if id_match:
                reminder_id = id_match.group()
                result = self.service.delete_reminder(user_id, reminder_id)
                if result.success:
                    return {"success": True, "message": f"Reminder {reminder_id} deleted."}
                return {"success": False, "error": result.error_message}
            return {
                "success": False,
                "error": 'Please provide a reminder ID to delete. Example: "delete reminder 245f1bd9"',
            }

        price_pattern = r"(?:alert|remind|notify).*?(?:when|if)\s+(\w+(?:\s+\w+)?)\s+(?:exceeds?|goes?|falls?|drops?|above|below|>|<)\s*\$?(\d+(?:\.\d+)?)"
        match = re.search(price_pattern, msg_lower)

        if match:
            ingredient_name = match.group(1).strip()
            threshold = float(match.group(2))

            condition = "above"
            if any(w in msg_lower for w in ["below", "under", "<", "falls", "drops", "less"]):
                condition = "below"

            ingredient_info = _INGREDIENT_MAP.get(ingredient_name.lower())
            if ingredient_info:
                result = self.service.create_reminder(
                    user_id=user_id,
                    reminder_type="price",
                    threshold=threshold,
                    condition=condition,
                    ingredient=ingredient_info["name"],
                    ingredient_code=ingredient_info["code"],
                )
                if result.success:
                    cond_text = "exceeds" if condition == "above" else "falls below"
                    return {
                        "success": True,
                        "message": f"Price alert created!\n\n| Ingredient | Condition | Alert ID |\n|------------|-----------|----------|\n| {ingredient_info['name']} | {cond_text} ${threshold}/ton | {result.data['id']} |",
                    }
                return {"success": False, "error": result.error_message}

            formula_info = _FORMULA_MAP.get(ingredient_name.lower())
            if formula_info:
                result = self.service.create_reminder(
                    user_id=user_id,
                    reminder_type="formula_cost",
                    threshold=threshold,
                    condition=condition,
                    formula=formula_info["name"],
                    formula_id=formula_info["id"],
                )
                if result.success:
                    cond_text = "exceeds" if condition == "above" else "falls below"
                    return {
                        "success": True,
                        "message": f"Formula cost alert created!\n\n| Formula | Condition | Alert ID |\n|---------|-----------|----------|\n| {formula_info['name']} | {cond_text} ${threshold}/ton | {result.data['id']} |",
                    }
                return {"success": False, "error": result.error_message}

            return {
                "success": False,
                "error": f"Unknown ingredient or formula: '{ingredient_name}'. Supported: corn, soybean meal, wheat, barley, fish meal, DDGS, nursery diet, grower diet, finishing diet.",
            }

        return {
            "success": False,
            "error": 'Could not parse reminder request. Try: "Alert when corn > $100/ton" or "show my reminders"',
        }


def get_reminder_skill():
    return ReminderSkill(SkillReminderService())


def _load_module(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_price_lookup_skill():
    module = _load_module(
        "query_price",
        os.path.join(WORKSPACE, "skills/price_lookup_skill/scripts/query_price.py"),
    )
    return module.create_skill(SkillPriceService())


def get_formula_cost_skill():
    module = _load_module(
        "formula_cost",
        os.path.join(WORKSPACE, "skills/formula_cost_skill/skill.py"),
    )
    return module.FormulaCostSkill(SkillCalculationService())


def get_nutrition_skill():
    module = _load_module(
        "nutrition",
        os.path.join(WORKSPACE, "skills/nutrition_analysis_skill/skill.py"),
    )
    return module.NutritionAnalysisSkill(SkillFormulaService())


def get_customer_skill():
    module = _load_module(
        "customer",
        os.path.join(WORKSPACE, "skills/customer_record_skill/skill.py"),
    )
    return module.CustomerRecordSkill(SkillCustomerService())


SKILL_MAP = {
    "price_lookup": get_price_lookup_skill,
    "price": get_price_lookup_skill,
    "formula_cost": get_formula_cost_skill,
    "cost": get_formula_cost_skill,
    "nutrition": get_nutrition_skill,
    "analyze": get_nutrition_skill,
    "customer": get_customer_skill,
    "customers": get_customer_skill,
    "reminder": get_reminder_skill,
    "reminders": get_reminder_skill,
    "alert": get_reminder_skill,
}


async def run_skill(skill_name: str, user_message: str, user_id: str = "cli_user"):
    skill_factory = SKILL_MAP.get(skill_name)
    if not skill_factory:
        return {"success": False, "error": f"Unknown skill: {skill_name}. Available: {list(SKILL_MAP.keys())}"}

    skill = skill_factory()
    result = await skill.execute(user_id, user_message)
    return result


def main():
    if len(sys.argv) < 3:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": 'Usage: run_skill.py <skill_name> "<user_message>"',
                    "available_skills": list(SKILL_MAP.keys()),
                },
                indent=2,
            )
        )
        sys.exit(1)

    skill_name = sys.argv[1]
    user_message = sys.argv[2]

    result = asyncio.run(run_skill(skill_name, user_message))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
