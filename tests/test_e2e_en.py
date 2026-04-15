"""
FeedSales AI - English E2E Test Suite with Result Recording

All queries in English. Every test captures actual output for agent optimization.
Tests skills directly (bypassing TaskRouter) to validate skill-level correctness.

Result JSON saved to: tests/e2e_results.json
"""

import sys
import os
import json
import sqlite3
import asyncio
import logging
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Reset singleton before imports
from src.database.pool import DatabasePool
DatabasePool._instance = None
DatabasePool._lock = threading.Lock()

from src.database.pool import DatabasePool
from src.services.formula_service import FormulaService
from src.services.price_service import PriceService
from src.services.customer_service import CustomerService
from src.services.calculation_service import CalculationService
from skills.formula_cost_skill.skill import FormulaCostSkill
from skills.price_lookup_skill.skill import PriceLookupSkill
from skills.customer_record_skill.skill import CustomerRecordSkill
from skills.nutrition_analysis_skill.skill import NutritionAnalysisSkill

logging.basicConfig(level=logging.WARNING)

# ============================================================
# RESULT RECORDER
# ============================================================
class ResultRecorder:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def record(self, category, test_id, query, expected, actual_response, passed, detail=""):
        entry = {
            "test_id": test_id,
            "category": category,
            "query": query,
            "expected": expected,
            "actual": actual_response,
            "passed": passed,
            "detail": detail,
            "timestamp": datetime.now().isoformat(),
        }
        self.results.append(entry)
        if passed:
            self.passed += 1
            print(f"  PASS  [{test_id}] {query}")
        else:
            self.failed += 1
            print(f"  FAIL  [{test_id}] {query} -- {detail}")

    def save(self, path="tests/e2e_results.json"):
        summary = {
            "run_time": datetime.now().isoformat(),
            "total": self.passed + self.failed,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": f"{100*self.passed/(self.passed+self.failed):.1f}%" if (self.passed+self.failed) else "N/A",
            "results": self.results,
        }
        with open(path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\nResults saved to {path}")
        return summary

recorder = ResultRecorder()

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

# ============================================================
# DATABASE SETUP
# ============================================================
section("SETUP: Database & Seed Data")

TEST_DB = "data/feed_sales_e2e_en.db"
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

conn = sqlite3.connect(TEST_DB)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=OFF")
with open("src/database/schema.sql") as f:
    conn.executescript(f.read())

# Seed users
for uid in ["test_user_001", "test_user_002", "system_public"]:
    conn.execute("INSERT OR IGNORE INTO users (open_id) VALUES (?)", (uid,))
conn.commit()

# Seed formulas from JSON
with open("data/nrc_formulas_full.json") as f:
    formulas_data = json.load(f)

for fd in formulas_data:
    cur = conn.execute(
        "INSERT INTO formulas (owner_open_id, name, animal_type, stage_type, weight_range, notes) VALUES (?,?,?,?,?,?)",
        ("system_public", fd["name"], fd["animal_type"], fd["stage"], fd.get("weight_range",""), fd.get("source",""))
    )
    fid = cur.lastrowid
    for ing in fd.get("ingredients", []):
        conn.execute(
            "INSERT INTO formula_ingredients (formula_id, ingredient_name, ingredient_code, ratio_percent) VALUES (?,?,?,?)",
            (fid, ing["name"], ing.get("code",""), ing["ratio"])
        )

# Seed prices
PRICES = [
    ("ING_CORN","Corn",185.50), ("ING_SBM","Soybean meal",342.00),
    ("ING_WHEAT","Wheat",210.00), ("ING_BARLEY","Barley",175.00),
    ("ING_DDGS","DDGS",195.00), ("ING_FISHM","Fish meal",1850.00),
    ("ING_CANOLA","Canola meal",310.00), ("ING_COTTON","Cottonseed meal",290.00),
    ("ING_LIME","Limestone",115.00), ("ING_DCP","Dicalcium phosphate",680.00),
    ("ING_SALT","Salt",145.00), ("ING_LYS","L-Lysine",1250.00),
    ("ING_MET","DL-Methionine",2550.00), ("ING_PREMIX","Premix",480.00),
    ("ING_ALFALFA","Alfalfa",220.00), ("ING_RICE","Rice",320.00),
    ("ING_SORGHUM","Sorghum",178.00), ("ING_MOLASSES","Molasses",160.00),
    ("ING_SILAGE","Corn silage",55.00), ("ING_HAY","Grass hay",180.00),
    ("ING_MBM","Meat and bone meal",450.00), ("ING_OIL","Fish oil",950.00),
]
for code, name, price in PRICES:
    conn.execute(
        "INSERT INTO ingredient_prices (owner_open_id, ingredient_code, ingredient_name, price, price_date, source) VALUES (?,?,?,?,?,?)",
        ("system_public", code, name, price, "2026-04-15", "barchart")
    )

# Seed a test customer
conn.execute(
    "INSERT INTO customers (owner_open_id, name, phone, animal_type, scale, notes) VALUES (?,?,?,?,?,?)",
    ("test_user_001", "Smith Farm", "555-0100", "swine", 500, "Long-term customer")
)
conn.commit()
conn.close()

# Initialize pool + services
pool = DatabasePool(TEST_DB)
formula_svc = FormulaService(pool)
price_svc = PriceService(pool)
calc_svc = CalculationService(pool)
customer_svc = CustomerService(pool)

# Initialize skills
cost_skill = FormulaCostSkill(calc_svc)
price_skill = PriceLookupSkill(price_svc)
customer_skill = CustomerRecordSkill(customer_svc)
nutrition_skill = NutritionAnalysisSkill(formula_svc)

USER = "test_user_001"

# Helper: run async skill
def run(skill, user_id, message):
    return asyncio.get_event_loop().run_until_complete(skill.execute(user_id, message))

print("  Setup complete: services + skills initialized")

# ============================================================
# SECTION 1: FORMULA COST SKILL
# ============================================================
section("1. FORMULA COST SKILL")

COST_TESTS = [
    ("FC-01", "cost for Nursery Diet 1", "Returns cost with formula details"),
    ("FC-02", "cost for Grower Diet 1", "Returns cost for grower formula"),
    ("FC-03", "cost for Finisher Diet", "Returns cost for finisher formula"),
    ("FC-04", "cost for Broiler Starter", "Returns cost for broiler formula"),
    ("FC-05", "cost for Layer Diet", "Returns cost for layer formula"),
    ("FC-06", "cost for Lactating Cow Diet", "Returns cost for dairy formula"),
    ("FC-07", "cost for Beef Cattle Finisher", "Returns cost for beef formula"),
    ("FC-08", "cost for Trout Starter", "Returns cost for aquatic formula"),
    ("FC-09", "cost for Catfish Grower", "Returns cost for catfish formula"),
    ("FC-10", "calculate Nursery Diet 1 cost", "Alternate English phrasing"),
    ("FC-11", "Nursery Diet 1 price", "Price phrasing variant"),
    ("FC-12", "cost for Gestating Sow Diet", "Sow formula cost"),
    ("FC-13", "cost for Lactating Sow Diet", "Lactating sow formula"),
    ("FC-14", "cost for Turkey Starter", "Turkey formula cost"),
    ("FC-15", "cost for Nonexistent Formula", "Should return error"),
]

for tid, query, expected in COST_TESTS:
    resp = run(cost_skill, USER, query)
    ok = resp.get("success", False)
    if ok:
        data = resp["data"]
        detail = f"cost=${data.get('cost_per_ton','?')}/ton"
    else:
        detail = resp.get("error", "unknown error")
    # For nonexistent formula, success=False is expected
    if "Nonexistent" in query:
        ok = not resp.get("success", True)
        detail = "Correctly rejected" if ok else "Should have failed"
    recorder.record("formula_cost", tid, query, expected, resp, ok, detail)

# ============================================================
# SECTION 2: PRICE LOOKUP SKILL
# ============================================================
section("2. PRICE LOOKUP SKILL")

PRICE_TESTS = [
    ("PL-01", "price of Corn", "Returns Corn price"),
    ("PL-02", "price of Soybean meal", "Returns SBM price"),
    ("PL-03", "price of Fish meal", "Returns fish meal price"),
    ("PL-04", "price of Wheat", "Returns wheat price"),
    ("PL-05", "price of Limestone", "Returns limestone price"),
    ("PL-06", "price of Premix", "Returns premix price"),
    ("PL-07", "price of DDGS", "Returns DDGS price"),
    ("PL-08", "Corn price", "Short form query"),
    ("PL-09", "Soybean meal price", "Short form query"),
    ("PL-10", "L-Lysine price", "Additive price"),
    ("PL-11", "DL-Methionine price", "Additive price"),
    ("PL-12", "Dicalcium phosphate price", "Mineral price"),
    ("PL-13", "Salt price", "Salt price"),
    ("PL-14", "Alfalfa price", "Fiber source price"),
    ("PL-15", "show all prices", "Returns all price list"),
]

for tid, query, expected in PRICE_TESTS:
    resp = run(price_skill, USER, query)
    ok = resp.get("success", False)
    if ok:
        data = resp["data"]
        detail = f"price=${data.get('price','?')}/ton" if data.get("price") else f"{data.get('count','?')} prices listed"
    else:
        detail = resp.get("error", "unknown error")
    recorder.record("price_lookup", tid, query, expected, resp, ok, detail)

# ============================================================
# SECTION 3: CUSTOMER RECORD SKILL
# ============================================================
section("3. CUSTOMER RECORD SKILL")

CUST_TESTS = [
    ("CR-01", "show all customers", "Returns customer list"),
    ("CR-02", "list my customers", "Returns customer list"),
    ("CR-03", "find customer Smith Farm", "Finds existing customer"),
    ("CR-04", "search customer Smith", "Fuzzy search for Smith"),
    ("CR-05", "add customer Johnson Farm phone 555-0200", "Adds new customer"),
    ("CR-06", "add customer Brown Ranch swine phone 555-0300", "Adds with animal type"),
    ("CR-07", "get customer Johnson Farm", "Retrieves added customer"),
    ("CR-08", "how many customers do I have", "Returns count"),
    ("CR-09", "count customers", "Returns count"),
    ("CR-10", "update customer Johnson Farm phone 555-9999", "Updates phone"),
    ("CR-11", "delete customer Brown Ranch", "Deletes customer"),
    ("CR-12", "add customer", "Should fail: no name"),
]

for tid, query, expected in CUST_TESTS:
    resp = run(customer_skill, USER, query)
    ok = resp.get("success", False)
    if ok:
        data = resp["data"]
        msg = data.get("message", "")
        detail = msg[:80] if msg else str(data)[:80]
    else:
        detail = resp.get("error", "unknown error")[:80]
    # CR-12: adding without name should fail
    if tid == "CR-12":
        ok = not resp.get("success", True)
        detail = "Correctly rejected" if ok else "Should have failed"
    recorder.record("customer_record", tid, query, expected, resp, ok, detail)

# ============================================================
# SECTION 4: NUTRITION ANALYSIS SKILL
# ============================================================
section("4. NUTRITION ANALYSIS SKILL")

NUTR_TESTS = [
    ("NA-01", "analyze Nursery Diet 1 nutrition", "Returns nutrition analysis"),
    ("NA-02", "analyze Grower Diet 1 nutrition", "Returns nutrition for grower"),
    ("NA-03", "analyze Finisher Diet nutrition", "Returns nutrition for finisher"),
    ("NA-04", "analyze Broiler Starter nutrition", "Returns broiler nutrition"),
    ("NA-05", "analyze Layer Diet nutrition", "Returns layer nutrition"),
    ("NA-06", "analyze Lactating Cow Diet nutrition", "Returns dairy nutrition"),
    ("NA-07", "analyze Beef Cattle Finisher nutrition", "Returns beef nutrition"),
    ("NA-08", "analyze Trout Starter nutrition", "Returns trout nutrition"),
    ("NA-09", "analyze Catfish Grower nutrition", "Returns catfish nutrition"),
    ("NA-10", "analyze Gestating Sow Diet nutrition", "Returns sow nutrition"),
    ("NA-11", "analyze Lactating Sow Diet nutrition", "Returns lactating sow nutrition"),
    ("NA-12", "list all formulas nutrition", "Returns formula list"),
    ("NA-13", "analyze NonexistentFormula nutrition", "Should return error"),
]

for tid, query, expected in NUTR_TESTS:
    resp = run(nutrition_skill, USER, query)
    ok = resp.get("success", False)
    if ok:
        data = resp["data"]
        nutr = data.get("nutrition", {})
        detail = f"protein={nutr.get('protein','?')}%, Ca={nutr.get('calcium','?')}%"
    else:
        detail = resp.get("error", "unknown error")[:80]
    # NA-13: nonexistent should fail
    if tid == "NA-13":
        ok = not resp.get("success", True)
        detail = "Correctly rejected" if ok else "Should have failed"
    recorder.record("nutrition_analysis", tid, query, expected, resp, ok, detail)

# ============================================================
# SUMMARY & SAVE
# ============================================================
section("SUMMARY")
summary = recorder.save()
print(f"\n  Total: {summary['total']}  Passed: {summary['passed']}  Failed: {summary['failed']}  Rate: {summary['pass_rate']}")

# Cleanup
os.unlink(TEST_DB)
print("  Test DB cleaned up.")
