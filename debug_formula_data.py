#!/usr/bin/env python3
import sqlite3, json

# Check what's in the seed data for ingredient_code
with open('data/nrc_formulas_full.json') as f:
    data = json.load(f)

# Check first formula's ingredients
f1 = data[0]
print(f"Formula: {f1['name']}")
for ing in f1.get('ingredients', [])[:5]:
    print(f"  name={ing.get('name')}, code={ing.get('code')}, ratio={ing.get('ratio')}")

# Count how many have empty codes
total = 0
empty = 0
for fd in data:
    for ing in fd.get('ingredients', []):
        total += 1
        if not ing.get('code'):
            empty += 1

print(f"\nTotal ingredients: {total}, empty codes: {empty}")
