#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from skills.price_lookup_skill.skill import PriceLookupSkill

skill = PriceLookupSkill()

# Check which keywords are substrings of other common words
print("=== Substring collision check ===")
test_strings = [
    "price of Corn", "price of Soybean meal", "price of Fish meal",
    "price of Wheat", "price of Limestone", "price of Premix",
    "price of DDGS", "Corn price", "Soybean meal price",
    "L-Lysine price", "DL-Methionine price", "Dicalcium phosphate price",
    "Salt price", "Alfalfa price", "show all prices",
    "what is the price of Fish meal", "how much for DDGS",
    "current price of Limestone", "Premix pricing",
]

for msg in test_strings:
    ingredient = skill._find_ingredient(msg)
    # Check what it SHOULD be
    msg_lower = msg.lower()
    expected = None
    for kw in skill.INGREDIENT_KEYWORDS:
        if kw.lower() in msg_lower and kw != "Rice":  # Skip Rice false positive
            if expected is None:  # Take first non-Rice match
                expected = kw
    # Also check if Rice is a real match (not substring of "price")
    if "rice" in msg_lower and "price" not in msg_lower:
        expected = "Rice"
    
    if ingredient != expected and ingredient is not None:
        print(f"  WRONG: '{msg}' => got '{ingredient}', expected '{expected}'")
    elif ingredient == expected:
        print(f"  OK:    '{msg}' => '{ingredient}'")
    else:
        print(f"  MISS:  '{msg}' => None (expected '{expected}')")
