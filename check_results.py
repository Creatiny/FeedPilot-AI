#!/usr/bin/env python3
"""Analyze E2E test results for data correctness (not just success=True)"""
import json, sys

with open('tests/e2e_results.json') as f:
    data = json.load(f)

print("=== PRICE LOOKUP: Checking actual ingredient returned ===")
for r in data['results']:
    if r['category'] == 'price_lookup' and r['test_id'] != 'PL-15':
        actual = r['actual']
        if actual.get('success'):
            d = actual['data']
            ingredient = d.get('ingredient', '?')
            price = d.get('price', '?')
            code = d.get('ingredient_code', '?')
            print(f"  {r['test_id']}: query='{r['query']}' => ingredient={ingredient}, code={code}, price={price}")
        else:
            print(f"  {r['test_id']}: FAILED - {actual.get('error')}")

print()
print("=== FORMULA COST: Checking for empty/null fields ===")
for r in data['results']:
    if r['category'] == 'formula_cost':
        actual = r['actual']
        if actual.get('success'):
            d = actual['data']
            source = d.get('source')
            ps = d.get('price_sources')
            details = d.get('details', [])
            # Check for empty ingredient_code in details
            empty_codes = sum(1 for item in details if isinstance(item, dict) and not item.get('ingredient_code'))
            print(f"  {r['test_id']}: source={source}, price_sources={ps}, details_count={len(details)}, empty_codes={empty_codes}")

print()
print("=== NUTRITION: Checking NRC comparison ===")
for r in data['results']:
    if r['category'] == 'nutrition_analysis' and r['test_id'] != 'NA-12':
        actual = r['actual']
        if actual.get('success'):
            d = actual['data']
            nrc = d.get('nrc_comparison', {})
            animal = d.get('animal_type')
            stage = d.get('stage')
            print(f"  {r['test_id']}: animal={animal}, stage={stage}, nrc_keys={list(nrc.keys()) if nrc else 'EMPTY'}")

print()
print("=== CUSTOMER RECORD: Checking name parsing ===")
for r in data['results']:
    if r['category'] == 'customer_record' and r['test_id'] in ('CR-05', 'CR-06'):
        actual = r['actual']
        if actual.get('success'):
            d = actual['data']
            cust = d.get('customer', {})
            print(f"  {r['test_id']}: query='{r['query']}' => name={cust.get('name')}, phone={cust.get('phone')}, notes={str(cust.get('notes',''))[:60]}")

print()
print("=== ERROR MESSAGES: Checking language ===")
for r in data['results']:
    actual = r['actual']
    if not actual.get('success'):
        err = actual.get('error', '')
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in err)
        if has_chinese:
            print(f"  {r['test_id']}: CHINESE ERROR: {err}")
