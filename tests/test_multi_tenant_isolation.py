"""FeedSales AI - Multi-Tenant Isolation Tests (v1.7)"""
import sys, pytest, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.database.pool import DatabasePool
from src.database.repository import FormulaRepository, PriceRepository, CustomerRepository

@pytest.fixture
def isolated_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as fp:
        db_path = fp.name
    pool = DatabasePool(db_path)
    with pool.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (open_id TEXT PRIMARY KEY)")
        cur.execute("CREATE TABLE IF NOT EXISTS formulas (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_open_id TEXT NOT NULL, name TEXT NOT NULL, animal_type TEXT, stage_type TEXT NOT NULL, notes TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, version INTEGER DEFAULT 1, UNIQUE(owner_open_id, name))")
        cur.execute("CREATE TABLE IF NOT EXISTS formula_ingredients (id INTEGER PRIMARY KEY AUTOINCREMENT, formula_id INTEGER NOT NULL, ingredient_name TEXT NOT NULL, ingredient_code TEXT, ratio_percent REAL NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE)")
        cur.execute("CREATE TABLE IF NOT EXISTS ingredient_prices (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_open_id TEXT NOT NULL, ingredient_code TEXT NOT NULL, ingredient_name TEXT NOT NULL, price REAL NOT NULL, currency TEXT DEFAULT 'USD', unit TEXT DEFAULT 'ton', source TEXT DEFAULT 'barchart', price_date DATE NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, version INTEGER DEFAULT 1, UNIQUE(ingredient_code, price_date, owner_open_id))")
        cur.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_open_id TEXT NOT NULL, name TEXT NOT NULL, phone TEXT, address TEXT, animal_type TEXT, scale INTEGER, notes TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, version INTEGER DEFAULT 1)")
        for u in ["user_alice", "user_bob", "user_charlie", "system_public"]:
            cur.execute("INSERT OR IGNORE INTO users (open_id) VALUES (?)", (u,))
        conn.commit()
    yield pool
    pass  # DatabasePool cleanup
    try: os.unlink(db_path)
    except: pass

class TestFormulaIsolation:
    def test_user_cannot_see_other_user_formula(self, isolated_db):
        r = FormulaRepository(isolated_db)
        r.create_formula("user_alice", {"name": "Secret", "stage_type": "Nursery", "notes": "Alice", "ingredients": [{"name": "Corn", "ratio": 60.0}]})
        assert r.get_formula("user_bob", "Secret") is None

    def test_same_name_formulas_different_users(self, isolated_db):
        r = FormulaRepository(isolated_db)
        r.create_formula("user_alice", {"name": "Common", "stage_type": "Nursery", "notes": "Alice", "ingredients": [{"name": "Corn", "ratio": 50.0}]})
        r.create_formula("user_bob", {"name": "Common", "stage_type": "Nursery", "notes": "Bob", "ingredients": [{"name": "Wheat", "ratio": 60.0}]})
        a = r.get_formula("user_alice", "Common")
        b = r.get_formula("user_bob", "Common")
        assert a is not None and b is not None
        assert a["notes"] == "Alice" and b["notes"] == "Bob"

    def test_list_formulas_isolation(self, isolated_db):
        r = FormulaRepository(isolated_db)
        for i in range(2): r.create_formula("user_alice", {"name": f"Alice{i}", "stage_type": "Nursery", "ingredients": [{"name": "Corn", "ratio": 50.0}]})
        for i in range(3): r.create_formula("user_bob", {"name": f"Bob{i}", "stage_type": "Finisher", "ingredients": [{"name": "Wheat", "ratio": 60.0}]})
        assert len(r.list_formulas("user_alice")) == 2
        assert len(r.list_formulas("user_bob")) == 3

    def test_update_formula_isolation(self, isolated_db):
        r = FormulaRepository(isolated_db)
        fid = r.create_formula("user_alice", {"name": "AliceF", "stage_type": "Nursery", "notes": "Original", "ingredients": [{"name": "Corn", "ratio": 50.0}]})
        assert r.update_formula("user_bob", fid, {"name": "Hacked", "stage_type": "Finisher", "notes": "Hacked", "ingredients": [{"name": "Wheat", "ratio": 100.0}]}) is False
        assert r.get_formula("user_alice", "AliceF")["notes"] == "Original"

    def test_delete_formula_isolation(self, isolated_db):
        r = FormulaRepository(isolated_db)
        fid = r.create_formula("user_alice", {"name": "AliceP", "stage_type": "Nursery", "ingredients": [{"name": "Corn", "ratio": 50.0}]})
        assert r.delete_formula("user_bob", fid) is False
        assert r.get_formula("user_alice", "AliceP") is not None

class TestPriceIsolation:
    def test_user_cannot_see_other_user_prices(self, isolated_db):
        r = PriceRepository(isolated_db)
        r.save_price("user_alice", {"ingredient_code": "CORN-P", "ingredient_name": "Private Corn", "price": 250.0, "price_date": "2024-01-15"})
        assert r.get_latest_price("user_bob", "CORN-P") is None

    def test_price_list_isolation(self, isolated_db):
        r = PriceRepository(isolated_db)
        r.save_price("user_alice", {"ingredient_code": "CORN-A", "ingredient_name": "Alice Corn", "price": 200.0, "price_date": "2024-01-15"})
        r.save_price("user_bob", {"ingredient_code": "CORN-B", "ingredient_name": "Bob Corn", "price": 180.0, "price_date": "2024-01-15"})
        ap = r.get_prices_by_date("user_alice", "2024-01-15")
        bp = r.get_prices_by_date("user_bob", "2024-01-15")
        assert len(ap) == 1 and ap[0]["ingredient_code"] == "CORN-A"
        assert len(bp) == 1 and bp[0]["ingredient_code"] == "CORN-B"

class TestCustomerIsolation:
    def test_user_cannot_see_other_user_customers(self, isolated_db):
        r = CustomerRepository(isolated_db)
        r.create_customer("user_alice", {"name": "AliceC", "phone": "555-0001"})
        assert r.get_customer("user_bob", "AliceC") is None

    def test_customer_list_isolation(self, isolated_db):
        r = CustomerRepository(isolated_db)
        for i in range(2): r.create_customer("user_alice", {"name": f"AliceC{i}", "phone": f"555-100{i}"})
        for i in range(3): r.create_customer("user_bob", {"name": f"BobC{i}", "phone": f"555-200{i}"})
        assert len(r.list_customers("user_alice")) == 2
        assert len(r.list_customers("user_bob")) == 3

    def test_update_customer_isolation(self, isolated_db):
        r = CustomerRepository(isolated_db)
        cid = r.create_customer("user_alice", {"name": "AliceC", "phone": "555-0001"})
        assert r.update_customer("user_bob", cid, {"name": "Hacked", "phone": "555-9999"}) is False
        assert r.get_customer("user_alice", "AliceC")["phone"] == "555-0001"

    def test_delete_customer_isolation(self, isolated_db):
        r = CustomerRepository(isolated_db)
        cid = r.create_customer("user_alice", {"name": "AliceC", "phone": "555-0001"})
        assert r.delete_customer("user_bob", cid) is False
        assert r.get_customer("user_alice", "AliceC") is not None
