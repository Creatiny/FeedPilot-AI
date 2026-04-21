#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from src.utils.ingredient_codes import generate_ingredient_code

# Test what codes are generated for each keyword
keywords = ['Corn', 'Soybean meal', 'Fish meal', 'Wheat', 'Limestone', 'Premix', 
            'DDGS', 'L-Lysine', 'DL-Methionine', 'Dicalcium phosphate', 'Salt', 'Alfalfa']
for kw in keywords:
    code = generate_ingredient_code(kw)
    print(f'{kw:25s} => {code}')

# Now test what _find_ingredient returns for each query
print("\n--- Testing _find_ingredient ---")
from skills.price_lookup_skill.skill import PriceLookupSkill
skill = PriceLookupSkill()

queries = [
    "price of Corn", "price of Soybean meal", "price of Fish meal",
    "price of Wheat", "price of Limestone", "price of Premix",
    "price of DDGS", "Corn price", "Soybean meal price",
    "L-Lysine price", "DL-Methionine price", "Dicalcium phosphate price",
    "Salt price", "Alfalfa price",
]
for q in queries:
    ingredient = skill._find_ingredient(q)
    code = generate_ingredient_code(ingredient) if ingredient else None
    print(f'  query="{q:35s}" => ingredient="{ingredient}" => code={code}')
