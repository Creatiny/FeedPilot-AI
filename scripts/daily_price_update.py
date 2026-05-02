#!/usr/bin/env python3
"""
FeedPilot AI - Daily Price Updater

Fetches real market prices for feed ingredients and updates the SQLite database.
Supports multiple data sources with automatic fallback.

Data Sources (in priority order):
1. yfinance (Yahoo Finance) - FREE, no API key needed
2. Alpha Vantage - FREE tier (25 calls/day), requires API key
3. Barchart OnDemand - requires API key
4. Reference prices - built-in fallback (always works)

Environment Variables:
    BARCHART_API_KEY    - Barchart API key
    ALPHA_VANTAGE_KEY   - Alpha Vantage API key
    DB_PATH             - Path to SQLite database (default: ../data/feed_sales.db)

Usage:
    python3 daily_price_update.py
    python3 daily_price_update.py --dry-run
    python3 daily_price_update.py --source yfinance

Cron Setup (daily 6:00 AM ET = 10:00 UTC):
    0 10 * * * cd /tmp/feedpilot-ai && /usr/bin/python3 scripts/daily_price_update.py >> logs/price_update.log 2>&1
"""

import os
import sys
import json
import time
import logging
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

# Add project paths
WORKSPACE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(WORKSPACE / "src"))

# Logging setup
LOG_DIR = WORKSPACE / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"price_update_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", str(WORKSPACE / "data" / "feed_sales.db"))

# ============================================
# Unit Conversion Constants
# ============================================

# CBOT futures: cents per bushel -> USD per metric ton
# 1 metric ton = 1000 kg
# Corn: 1 bushel = 25.40 kg -> 39.37 bu/ton
# Soybeans: 1 bushel = 27.22 kg -> 36.74 bu/ton
# Wheat: 1 bushel = 27.22 kg -> 36.74 bu/ton
# Soybean meal: USD per short ton (already in ton units, but short ton = 0.907 metric ton)
# Soybean oil: cents per pound -> USD per metric ton
CONVERSION_FACTORS = {
    "Corn, #2 Yellow": {"bu_per_ton": 39.37, "unit": "cents/bu"},
    "Soybeans, No.1 Yellow": {"bu_per_ton": 36.74, "unit": "cents/bu"},
    "Soybean meal, 48%": {"short_to_metric": 0.907, "unit": "USD/short_ton"},
    "Wheat, No.2 Soft Red": {"bu_per_ton": 36.74, "unit": "cents/bu"},
    "Soybean oil, crude": {"lb_per_ton": 2204.62, "unit": "cents/lb"},
    "Oats, #2 White CBOT": {"bu_per_ton": 32.00, "unit": "cents/bu"},
    "Sugar, white granulated": {"lb_per_ton": 2204.62, "unit": "cents/lb"},
}

# ============================================
# Reference Prices (fallback when all APIs fail)
# Updated monthly based on USDA/Feedstuffs market reports
# ============================================

REFERENCE_PRICES = {
    # Grains & Energy
    "Corn, #2 Yellow": 180.00,
    "Corn, grain": 180.00,
    "Soybeans, No.1 Yellow": 430.00,
    "Soybean meal, 48%": 350.00,
    "Soybean meal, 47.5%": 340.00,
    "Wheat, No.2 Soft Red": 190.00,
    "Wheat, SRW CBOT": 230.00,
    "Barley": 158.00,
    "Oats, #2 White CBOT": 150.00,
    "Rice bran": 140.00,
    "Rice polishings": 160.00,
    "Sorghum, #2 Yellow": 220.00,
    "DDGS, 10% fat": 175.00,
    "DDGS, 28% protein": 180.00,
    "Corn gluten meal, 60%": 468.00,
    "Wheat middlings": 190.00,
    "Wheat gluten": 800.00,
    "Brewers dried grains": 170.00,
    "Rye grain": 150.00,
    "Millet": 180.00,
    "Triticale": 140.00,

    # Proteins
    "Fish meal, 65%": 1800.00,
    "Fish meal, 72%": 1800.00,
    "Blood meal, porcine": 1025.00,
    "Blood meal, ruminant": 950.00,
    "Feather meal, 80%": 350.00,
    "Hydrolyzed feather meal": 350.00,
    "Meat and bone meal, ruminant": 275.00,
    "Meat and bone meal, porcine": 315.00,
    "Poultry by-product meal": 380.00,
    "Shrimp meal": 1200.00,
    "Squid meal": 1500.00,
    "Canola meal, 36%": 280.00,
    "Cottonseed meal, 41%": 245.00,
    "Peanut meal, 45%": 240.00,
    "Sunflower meal": 137.00,
    "Sesame meal": 220.00,
    "Palm kernel meal": 150.00,
    "Coconut meal (Copra)": 180.00,
    "Copra meal": 180.00,
    "Linseed meal": 195.00,
    "Safflower meal": 170.00,
    "Lupins, sweet": 260.00,
    "Faba beans": 240.00,
    "Lentils": 350.00,
    "Field peas": 220.00,
    "Soy flour, defatted": 600.00,
    "Soybean hulls, pellets": 135.00,
    "Soybean oil, crude": 1320.00,
    "Choice white grease": 960.00,
    "Tallow, bleachable": 1160.00,
    "Yellow grease": 800.00,
    "Crab meal": 600.00,

    # Forages
    "Alfalfa hay, early bloom": 220.00,
    "Alfalfa hay, supreme": 280.00,
    "Alfalfa meal, dehydrated": 355.00,
    "Alfalfa pellets, suncured": 220.00,
    "Alfalfa silage": 90.00,
    "Grass hay, early bloom": 180.00,
    "Grass hay, late bloom": 130.00,
    "Grass hay, mature": 150.00,
    "Timothy hay": 200.00,
    "Oat hay": 140.00,
    "Rye hay": 120.00,
    "Wheat hay": 110.00,
    "Pasture, fresh": 100.00,
    "Corn silage": 65.00,
    "Barley silage": 60.00,
    "Wheat silage": 55.00,
    "Oat silage": 55.00,
    "Sorghum silage": 50.00,
    "Straw, barley": 75.00,
    "Straw, wheat": 80.00,

    # Minerals & Additives
    "Dicalcium phosphate": 650.00,
    "Monocalcium phosphate": 700.00,
    "Limestone, ag": 120.00,
    "Salt, white": 150.00,
    "Iodized salt": 400.00,
    "Sodium bicarbonate": 400.00,
    "Potassium chloride": 350.00,
    "Magnesium oxide": 550.00,
    "Copper sulfate": 2000.00,
    "Zinc oxide": 2500.00,
    "Zinc sulfate": 1500.00,
    "Ferrous sulfate": 500.00,
    "Manganese sulfate": 800.00,
    "Selenium yeast": 10000.00,

    # Amino Acids & Vitamins
    "L-Lysine HCl": 1200.00,
    "DL-Methionine": 2500.00,
    "Threonine, 98%": 1500.00,
    "Tryptophan, 98%": 5000.00,
    "Choline chloride, 60%": 800.00,
    "Taurine": 15000.00,
    "Vitamin A premix": 4500.00,
    "Vitamin D3 premix": 5000.00,
    "Vitamin E premix": 6500.00,
    "Vitamin B12 premix": 20000.00,
    "Vitamin K3": 7000.00,
    "Vitamin C": 8000.00,
    "Riboflavin (Vitamin B2)": 10000.00,
    "Niacin": 5000.00,
    "Pantothenic acid": 6000.00,
    "Folic acid": 12000.00,
    "Biotin, 2%": 15000.00,

    # Premixes & Specialty
    "Premix, swine": 420.00,
    "Premix, beef": 400.00,
    "Premix, dairy": 480.00,
    "Premix, broiler": 520.00,
    "Premix, layer": 550.00,
    "Premix, sow": 460.00,
    "Premix, calf": 500.00,
    "Premix, heifer": 420.00,
    "Premix, turkey": 480.00,
    "Premix, sheep": 380.00,
    "Premix, goat": 400.00,
    "Premix, cat": 600.00,
    "Premix, dog": 550.00,
    "Premix, trout": 700.00,
    "Premix, catfish": 500.00,
    "Premix, duck": 450.00,
    "Premix, duck breeder": 480.00,
    "Premix, ewe": 420.00,
    "Premix, doe": 400.00,
    "Vitamin/mineral premix": 3500.00,

    # Milk & Dairy By-products
    "Milk replacer, calf": 2800.00,
    "Whey, dried": 1200.00,
    "Skim milk powder": 2500.00,
    "Whole milk powder": 3200.00,
    "Casein": 5000.00,

    # Other
    "Molasses, cane": 180.00,
    "Molasses, beet": 160.00,
    "Sugar, white granulated": 800.00,
    "Beet pulp, dried": 150.00,
    "Citrus pulp, dried": 120.00,
    "Brewer's yeast, dried": 1200.00,
    "Yeast, dried brewers": 800.00,
    "Yeast, dried torula": 900.00,
    "Lecithin": 3000.00,
    "Fish oil": 2000.00,
    "Water": 1.00,
    "Urea, feed grade": 400.00,
    "Urea": 400.00,
    "Vinegar (acidifier)": 300.00,
    "Pollen, bee collected": 8000.00,
    "Pollen substitute patty": 2500.00,
    "AP23 pollen substitute": 3200.00,
    "MegaBee pollen substitute": 3500.00,
    "Fondant, bee feed": 1000.00,
    "Honey, for feeding": 3000.00,
    "High fructose corn syrup, 55%": 600.00,
    "Creatine": 5000.00,
    "Betaine": 3000.00,
    "Organic acids blend": 1500.00,
    "Essential oils blend": 10000.00,
    "Probiotics": 15000.00,
    "Prebiotics": 8000.00,
    "Enzyme phytase": 20000.00,
    "Antioxidant": 600.00,
    "Mold inhibitor": 300.00,
    "Almond hulls": 100.00,
    "Bakery by-product": 140.00,
    "Corn, #2 Yellow CBOT": 180.00,
    "Corn silage": 65.00,

    # Chinese aliases
    "\u7389\u7c73": 180.00,
    "\u8c46\u7c95": 350.00,
    "\u9884\u6df7\u6599": 450.00,
}


# ============================================
# Database Operations
# ============================================

def get_db_connection():
    """Get SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_existing_price_codes() -> set:
    """Get set of ingredient_codes that already have public prices."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT ingredient_code FROM ingredient_prices WHERE owner_open_id = 'system_public'"
    )
    codes = {row["ingredient_code"] for row in cursor.fetchall()}
    conn.close()
    return codes


def get_ingredients_needing_prices() -> List[Dict]:
    """Get all distinct ingredients from public formulas, deduplicated by code.
    For codes with multiple names, returns the most frequently used name."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get the most common name for each ingredient_code
    cursor.execute("""
        SELECT fi.ingredient_code, fi.ingredient_name, COUNT(*) as usage_count
        FROM formula_ingredients fi
        JOIN formulas f ON fi.formula_id = f.id
        WHERE f.owner_open_id = 'system_public'
        GROUP BY fi.ingredient_code, fi.ingredient_name
        ORDER BY fi.ingredient_code, usage_count DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    # Deduplicate: keep only the most frequent name per code
    code_best_name = {}
    for row in rows:
        code = row["ingredient_code"]
        if code not in code_best_name:
            code_best_name[code] = dict(row)

    return list(code_best_name.values())


def save_prices(prices: List[Dict], source_tag: str = "auto") -> int:
    """Save prices to database. Returns number of records inserted/updated."""
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = 0

    for price_data in prices:
        cursor.execute("""
            INSERT INTO ingredient_prices
            (owner_open_id, ingredient_code, ingredient_name, price, currency, unit, price_date, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ingredient_code, price_date, owner_open_id) DO UPDATE SET
                price = excluded.price,
                source = excluded.source,
                updated_at = CURRENT_TIMESTAMP
        """, (
            "system_public",
            price_data["ingredient_code"],
            price_data["ingredient_name"],
            round(price_data["price"], 2),
            "USD",
            "ton",
            today,
            f"{source_tag}",
        ))
        updated += 1

    conn.commit()
    conn.close()
    return updated


# ============================================
# Price Fetchers
# ============================================

def fetch_yfinance_prices() -> List[Dict]:
    """
    Fetch CBOT futures prices via Yahoo Finance (yfinance).
    Returns list of price dicts with ingredient_code, ingredient_name, price.
    """
    try:
        import yfinance as yf
    except ImportError:
        logger.warning("yfinance not installed. Run: pip install yfinance")
        return []

    symbols = {
        "ZC=F": ("ING_CORN", "Corn, #2 Yellow"),
        "ZS=F": ("ING_SBEAN", "Soybeans, No.1 Yellow"),
        "ZM=F": ("ING_SBM", "Soybean meal, 48%"),
        "ZW=F": ("ING_WHEAT", "Wheat, No.2 Soft Red"),
        "ZL=F": ("ING_21DD435B", "Soybean oil, crude"),
        "ZO=F": ("ING_OATS", "Oats, #2 White CBOT"),
        "SB=F": ("ING_SUGAR", "Sugar, white granulated"),
    }

    results = []
    for sym, (code, name) in symbols.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="5d")
            if hist.empty:
                logger.warning(f"yfinance: No data for {sym} ({name})")
                continue

            last_price = float(hist["Close"].iloc[-1])
            conv = CONVERSION_FACTORS.get(name)

            if conv:
                if conv["unit"] == "cents/bu":
                    # Convert cents/bu to USD/ton
                    price_usd_ton = (last_price / 100.0) * conv["bu_per_ton"]
                elif conv["unit"] == "USD/short_ton":
                    # Convert short ton to metric ton
                    price_usd_ton = last_price / conv["short_to_metric"]
                elif conv["unit"] == "cents/lb":
                    # Convert cents/lb to USD/ton
                    price_usd_ton = (last_price / 100.0) * conv["lb_per_ton"]
                else:
                    price_usd_ton = last_price
            else:
                price_usd_ton = last_price

            results.append({
                "ingredient_code": code,
                "ingredient_name": name,
                "price": round(price_usd_ton, 2),
                "raw_price": last_price,
                "raw_unit": conv["unit"] if conv else "USD",
            })
            logger.info(f"yfinance: {name} = ${round(price_usd_ton, 2)}/ton (raw: {last_price})")
            time.sleep(1.0)  # Be polite to Yahoo Finance

        except Exception as e:
            logger.warning(f"yfinance failed for {sym}: {e}")

    return results


def fetch_alpha_vantage_prices(api_key: str) -> List[Dict]:
    """
    Fetch commodity ETF prices via Alpha Vantage API.
    Free tier supports TIME_SERIES_DAILY for ETFs but NOT futures.
    Uses ETF price change % to adjust reference prices.
    """
    import urllib.request

    # ETF symbols that Alpha Vantage free tier supports
    # CORN = Teucrium Corn Fund, SOYB = Teucrium Soybean Fund, WEAT = Teucrium Wheat Fund
    etf_map = {
        "CORN": ("ING_CORN", "Corn, #2 Yellow", "Corn, grain"),
        "SOYB": ("ING_SBEAN", "Soybeans, No.1 Yellow", "Soybeans, No.1 Yellow"),
        "WEAT": ("ING_WHEAT", "Wheat, No.2 Soft Red", "Wheat middlings"),
    }

    etf_changes = {}  # symbol -> change_pct

    for symbol in etf_map:
        try:
            url = (
                f"https://www.alphavantage.co/query?"
                f"function=TIME_SERIES_DAILY&"
                f"symbol={symbol}&"
                f"apikey={api_key}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())

            if "Time Series (Daily)" not in data:
                info = data.get("Information", data.get("Error Message", "Unknown"))
                logger.warning(f"Alpha Vantage: No data for {symbol}: {str(info)[:120]}")
                time.sleep(1.0)
                continue

            daily = data["Time Series (Daily)"]
            dates = sorted(daily.keys(), reverse=True)
            if len(dates) < 2:
                logger.warning(f"Alpha Vantage: Not enough history for {symbol}")
                continue

            today_close = float(daily[dates[0]]["4. close"])
            prev_close = float(daily[dates[1]]["4. close"])
            change_pct = (today_close - prev_close) / prev_close

            etf_changes[symbol] = {
                "today": today_close,
                "previous": prev_close,
                "change_pct": change_pct,
            }
            logger.info(
                f"Alpha Vantage ETF: {symbol} = ${today_close:.2f} "
                f"(was ${prev_close:.2f}, change: {change_pct:+.2%})"
            )
            time.sleep(1.2)  # Free tier: max 5 calls/minute

        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {symbol}: {e}")

    if not etf_changes:
        return []

    # Apply ETF change % to reference prices to get adjusted prices
    results = []
    for symbol, (code, api_name, ref_name) in etf_map.items():
        if symbol not in etf_changes:
            continue
        change_pct = etf_changes[symbol]["change_pct"]
        if ref_name in REFERENCE_PRICES:
            base_price = REFERENCE_PRICES[ref_name]
            adjusted = base_price * (1 + change_pct)
            results.append({
                "ingredient_code": code,
                "ingredient_name": api_name,
                "price": round(adjusted, 2),
                "raw_price": etf_changes[symbol]["today"],
                "raw_unit": f"ETF_{symbol}",
                "change_pct": round(change_pct * 100, 2),
            })
            logger.info(
                f"Alpha Vantage adjusted: {api_name} = ${adjusted:.2f}/ton "
                f"(base ${base_price:.2f} * {1+change_pct:.4f})"
            )

    return results


def fetch_barchart_prices(api_key: str) -> List[Dict]:
    """Fetch prices via Barchart OnDemand API."""
    import urllib.request

    symbols = {
        "ZC": ("ING_CORN", "Corn, #2 Yellow", "cents/bu", 39.37),
        "ZS": ("ING_SBEAN", "Soybeans, No.1 Yellow", "cents/bu", 36.74),
        "ZM": ("ING_SBM", "Soybean meal, 48%", "USD/short_ton", 0.907),
        "ZW": ("ING_WHEAT", "Wheat, No.2 Soft Red", "cents/bu", 36.74),
    }

    results = []
    for sym, (code, name, unit, factor) in symbols.items():
        try:
            url = (
                f"https://www.barchart.com/ondemand/api/v1/market/v2/futures/prices?"
                f"symbols={sym}&"
                f"fields=last,change,changePercent&"
                f"apikey={api_key}"
            )
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            if data.get("status", {}).get("code") != 200:
                logger.warning(f"Barchart: API error for {sym}")
                continue

            last = float(data["result"][0]["last"])
            if unit == "cents/bu":
                price_usd_ton = (last / 100.0) * factor
            elif unit == "USD/short_ton":
                price_usd_ton = last / factor
            else:
                price_usd_ton = last

            results.append({
                "ingredient_code": code,
                "ingredient_name": name,
                "price": round(price_usd_ton, 2),
                "raw_price": last,
                "raw_unit": unit,
            })
            logger.info(f"Barchart: {name} = ${round(price_usd_ton, 2)}/ton")

        except Exception as e:
            logger.warning(f"Barchart failed for {sym}: {e}")

    return results


def fetch_reference_prices(ingredients: List[Dict]) -> List[Dict]:
    """Return reference prices for all ingredients. Always works."""
    results = []
    for ing in ingredients:
        name = ing["ingredient_name"]
        code = ing["ingredient_code"]
        if name in REFERENCE_PRICES:
            results.append({
                "ingredient_code": code,
                "ingredient_name": name,
                "price": REFERENCE_PRICES[name],
                "raw_price": REFERENCE_PRICES[name],
                "raw_unit": "USD/ton",
            })
        else:
            logger.warning(f"No reference price for: {name} ({code})")
    return results


# ============================================
# Main Update Logic
# ============================================

def run_price_update(dry_run: bool = False, force_source: Optional[str] = None) -> Dict:
    """
    Run the full price update pipeline.

    Args:
        dry_run: If True, don't write to database
        force_source: Force a specific source (yfinance, alpha_vantage, barchart, reference)

    Returns:
        Dict with update statistics
    """
    start_time = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info("FeedPilot AI - Daily Price Update Started")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 60)

    ingredients = get_ingredients_needing_prices()
    logger.info(f"Found {len(ingredients)} unique ingredients in formulas")

    # Determine data sources to try
    sources_to_try = []

    if force_source:
        sources_to_try = [force_source]
    else:
        # Priority order
        sources_to_try.append("yfinance")
        if os.getenv("ALPHA_VANTAGE_KEY"):
            sources_to_try.append("alpha_vantage")
        if os.getenv("BARCHART_API_KEY"):
            sources_to_try.append("barchart")
        sources_to_try.append("reference")

    fetched_prices = []
    used_source = None

    for source in sources_to_try:
        logger.info(f"Trying source: {source}")

        if source == "yfinance":
            fetched_prices = fetch_yfinance_prices()
        elif source == "alpha_vantage":
            key = os.getenv("ALPHA_VANTAGE_KEY")
            fetched_prices = fetch_alpha_vantage_prices(key) if key else []
        elif source == "barchart":
            key = os.getenv("BARCHART_API_KEY")
            fetched_prices = fetch_barchart_prices(key) if key else []
        elif source == "reference":
            fetched_prices = fetch_reference_prices(ingredients)
        else:
            logger.error(f"Unknown source: {source}")
            continue

        if fetched_prices:
            used_source = source
            logger.info(f"Source {source} returned {len(fetched_prices)} prices")
            break
        else:
            logger.warning(f"Source {source} returned no prices")

    if not fetched_prices:
        logger.error("All data sources failed. No prices updated.")
        return {"success": False, "error": "All sources failed", "updated": 0}

    # For reference source, we got prices for all ingredients
    # For API sources, we need to fill gaps with reference prices
    if used_source != "reference":
        fetched_codes = {p["ingredient_code"] for p in fetched_prices}
        missing = [ing for ing in ingredients if ing["ingredient_code"] not in fetched_codes]
        if missing:
            logger.info(f"Filling {len(missing)} missing ingredients with reference prices")
            fallback = fetch_reference_prices(missing)
            fetched_prices.extend(fallback)
            used_source = f"{used_source}+reference"

    # Save to database
    if not dry_run:
        updated = save_prices(fetched_prices, source_tag=used_source)
    else:
        updated = len(fetched_prices)
        logger.info(f"[DRY RUN] Would update {updated} price records")
        for p in fetched_prices[:10]:
            logger.info(f"  {p['ingredient_name']}: ${p['price']:.2f}/ton")

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"Price update completed: {updated} records from source '{used_source}'")
    logger.info(f"Elapsed: {elapsed:.1f}s")
    logger.info("=" * 60)

    return {
        "success": True,
        "updated": updated,
        "source": used_source,
        "elapsed_seconds": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description="FeedPilot AI Daily Price Updater")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    parser.add_argument("--source", choices=["yfinance", "alpha_vantage", "barchart", "reference"],
                        help="Force specific data source")
    args = parser.parse_args()

    result = run_price_update(dry_run=args.dry_run, force_source=args.source)

    if not result["success"]:
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
