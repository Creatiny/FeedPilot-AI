#!/usr/bin/env python3
"""Quick formula cost calculation for cron jobs"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "feed_sales.db"

def get_ingredient_price(name_pattern, code_pattern=None):
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    if code_pattern:
        row = conn.execute(
            "SELECT ingredient_name, price FROM ingredient_prices WHERE ingredient_code = ? ORDER BY price_date DESC LIMIT 1",
            (code_pattern,)
        ).fetchone()
        if not row:
            row = conn.execute(
                "SELECT ingredient_name, price FROM ingredient_prices WHERE ingredient_name LIKE ? ORDER BY price_date DESC LIMIT 1",
                (f'%{name_pattern}%',)
            ).fetchone()
    else:
        row = conn.execute(
            "SELECT ingredient_name, price FROM ingredient_prices WHERE ingredient_name LIKE ? ORDER BY price_date DESC LIMIT 1",
            (f'%{name_pattern}%',)
        ).fetchone()
    
    conn.close()
    return dict(row) if row else None

def calculate_cost(ingredients):
    """ingredients: list of (display_name, name_pattern, code_pattern, inclusion_pct)"""
    total = 0.0
    details = []
    for display_name, name_pattern, code_pattern, pct in ingredients:
        ing = get_ingredient_price(name_pattern, code_pattern)
        if ing:
            cost = ing['price'] * (pct / 100)
            total += cost
            details.append(f"{ing['ingredient_name']}: ${ing['price']}/ton x {pct}% = ${cost:.2f}/ton")
        else:
            details.append(f"{display_name}: NOT FOUND")
    return total, details

if __name__ == "__main__":
    formula = sys.argv[1] if len(sys.argv) > 1 else "beef_finisher"
    
    # Beef Finisher: Corn 70%, Soybean meal 48% at 10%, Alfalfa hay early bloom 10%, Premix beef 5%, Dicalcium phosphate 1.5%, Limestone 1%, Salt 0.3%
    if formula == "beef_finisher":
        ingredients = [
            ("Corn, #2 Yellow", "Corn, #2 Yellow", "CORN", 70),
            ("Soybean meal, 48%", "Soybean meal, 48%", "SBM", 10),
            ("Alfalfa hay, early bloom", "Alfalfa hay, early bloom", "ING_ALFALFA", 10),
            ("Premix, beef", "Premix", "ING_PREMIX", 5),
            ("Dicalcium phosphate", "Dicalcium phosphate", "DCP", 1.5),
            ("Limestone, ag", "Limestone, ag", "LIME", 1),
            ("Iodized salt", "Iodized salt", "ING_IODIZED", 0.3),
        ]
    elif formula == "broiler_starter":
        # Corn 52%, Soybean meal 48% at 32%, Fish meal 65% at 5%, Premix broiler 5%, Dicalcium phosphate 1.5%, Limestone 1%, Salt 0.3%, L-Lysine HCl 0.2%
        ingredients = [
            ("Corn, #2 Yellow", "Corn, #2 Yellow", "CORN", 52),
            ("Soybean meal, 48%", "Soybean meal, 48%", "SBM", 32),
            ("Fish meal, 65%", "Fish meal, 65%", "FISHM", 5),
            ("Premix, broiler", "Premix", "ING_PREMIX", 5),
            ("Dicalcium phosphate", "Dicalcium phosphate", "DCP", 1.5),
            ("Limestone, ag", "Limestone, ag", "LIME", 1),
            ("Salt, white", "Salt, white", "SALT", 0.3),
            ("L-Lysine HCl", "L-Lysine HCl", "LYS", 0.2),
        ]
    elif formula == "nursery_diet_1":
        # Corn 60%, Soybean meal 48% at 25%, Fish meal 65% at 3%, Premix swine 5%, Dicalcium phosphate 1.5%, Limestone 1%, Salt 0.3%, L-Lysine HCl 0.2%
        ingredients = [
            ("Corn, #2 Yellow", "Corn, #2 Yellow", "CORN", 60),
            ("Soybean meal, 48%", "Soybean meal, 48%", "SBM", 25),
            ("Fish meal, 65%", "Fish meal, 65%", "FISHM", 3),
            ("Premix, swine", "Premix, swine", "ING_PREMIX", 5),
            ("Dicalcium phosphate", "Dicalcium phosphate", "DCP", 1.5),
            ("Limestone, ag", "Limestone, ag", "LIME", 1),
            ("Salt, white", "Salt, white", "SALT", 0.3),
            ("L-Lysine HCl", "L-Lysine HCl", "LYS", 0.2),
        ]
    else:
        print("UNKNOWN_FORMULA")
        sys.exit(1)
    
    total, details = calculate_cost(ingredients)
    print(f"TOTAL_COST|{total:.2f}")
    for d in details:
        print(f"  {d}")
