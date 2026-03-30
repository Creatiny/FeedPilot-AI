# FeedSales AI v1.7 - Comprehensive Test Plan

> Generated: 2026-03-29  
> Coverage: All formulas, ingredients, prices, costs, nutrition, customer management, smart reminders

---

## Test Categories

| Category | Test Cases | Priority |
|----------|-----------|----------|
| Formula Cost Calculation | 38 | P0 |
| Ingredient Price Query | 21 | P0 |
| Nutrition Analysis | 10 | P1 |
| Customer Management | 8 | P1 |
| Smart Reminders | 6 | P2 |
| Language Modes | 12 | P1 |
| Error Handling | 10 | P1 |
| **Total** | **105** | |

---

## 1. Formula Cost Calculation (38 Tests)

### Swine Formulas (8 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-01 | "How much does nursery pig feed cost per ton?" | Return Nursery Diet 1-3 costs |
| FC-02 | "What's the cost for starter feed for baby pigs?" | Nursery Diet 1 cost |
| FC-03 | "Calculate growing pig diet price" | Grower Diet 1-2 costs |
| FC-04 | "Finishing pig feed, how much?" | Finisher Diet cost |
| FC-05 | "Sow feed during pregnancy cost" | Gestating Sow Diet cost |
| FC-06 | "Lactating sow diet price per ton" | Lactating Sow Diet cost |
| FC-07 | "Show me all pig feed options with prices" | List all 8 swine formulas |
| FC-08 | "Compare nursery vs finisher pig feed costs" | Comparison table |

### Beef Cattle Formulas (3 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-09 | "Beef cattle starter feed cost" | Beef Cattle Starter cost |
| FC-10 | "Price for finishing beef cattle diet" | Beef Cattle Finisher cost |
| FC-11 | "Growing beef cattle feed, what's the cost?" | Beef Cattle Grower cost |

### Dairy Cattle Formulas (3 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-12 | "Dairy calf starter diet price" | Dairy Calf Starter cost |
| FC-13 | "Heifer grower feed cost per ton" | Dairy Heifer Grower cost |
| FC-14 | "Lactating cow feed, how much?" | Lactating Cow Diet cost |

### Broiler Formulas (3 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-15 | "Broiler starter feed cost" | Broiler Starter cost |
| FC-16 | "Broiler grower diet price" | Broiler Grower cost |
| FC-17 | "Finishing broiler feed per ton" | Broiler Finisher cost |

### Layer Formulas (3 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-18 | "Layer starter feed price" | Layer Starter cost |
| FC-19 | "Growing layer diet cost" | Layer Grower cost |
| FC-20 | "Laying hen feed, how much per ton?" | Layer Diet cost |

### Turkey Formulas (3 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-21 | "Turkey starter diet cost" | Turkey Starter cost |
| FC-22 | "Turkey grower feed price" | Turkey Grower cost |
| FC-23 | "Finishing turkey feed per ton" | Turkey Finisher cost |

### Sheep Formulas (4 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-24 | "Lamb starter feed cost" | Lamb Starter cost |
| FC-25 | "Finishing lamb diet price" | Lamb Finisher cost |
| FC-26 | "Pregnant ewe feed, how much?" | Ewe Gestating cost |
| FC-27 | "Lactating ewe diet per ton" | Ewe Lactating cost |

### Goat Formulas (3 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-28 | "Goat kid starter feed price" | Goat Kid Starter cost |
| FC-29 | "Pregnant goat diet cost" | Goat Doe Gestating cost |
| FC-30 | "Lactating goat feed per ton" | Goat Doe Lactating cost |

### Duck Formulas (3 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-31 | "Duck starter feed cost" | Duck Starter cost |
| FC-32 | "Duck grower diet price" | Duck Grower cost |
| FC-33 | "Duck breeder feed per ton" | Duck Breeder cost |

### Pet & Aquatic Formulas (5 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| FC-34 | "Adult cat food price" | Cat Food Adult cost |
| FC-35 | "Adult dog food cost per ton" | Dog Food Adult cost |
| FC-36 | "Trout starter feed, fry stage" | Trout Starter cost |
| FC-37 | "Trout grower diet for fingerlings" | Trout Grower cost |
| FC-38 | "Catfish grower feed price" | Catfish Grower cost |

---

## 2. Ingredient Price Query (21 Tests)

### Grains (4 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| IP-01 | "What's corn price today?" | Corn, grain price USD/ton |
| IP-02 | "Current wheat price per ton" | Wheat price |
| IP-03 | "How much is rice for feed?" | Rice price |
| IP-04 | "Barley feed grain price" | Barley price |

### Protein Sources (5 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| IP-05 | "Soybean meal price today" | Soybean meal, 48% price |
| IP-06 | "Fish meal cost per ton" | Fish meal, 65% price |
| IP-07 | "DDGS price for feed" | DDGS price |
| IP-08 | "Canola meal price" | Canola meal price |
| IP-09 | "Cottonseed meal cost" | Cottonseed meal price |

### Additives & Minerals (6 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| IP-10 | "Dicalcium phosphate price" | Dicalcium phosphate price |
| IP-11 | "Limestone for feed, how much?" | Limestone, ag price |
| IP-12 | "Salt price per ton" | Salt, white price |
| IP-13 | "L-Lysine price today" | L-Lysine HCl price |
| IP-14 | "DL-Methionine cost" | DL-Methionine price |
| IP-15 | "Premix for swine price" | Premix, swine price |

### Forage (4 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| IP-16 | "Alfalfa hay price" | Alfalfa hay, early bloom price |
| IP-17 | "Grass hay cost per ton" | Grass hay price |
| IP-18 | "Corn silage price" | Corn silage price |
| IP-19 | "Straw bedding price" | Straw price |

### Specialty (2 tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| IP-20 | "Molasses for feed price" | Molasses price |
| IP-21 | "Show me all ingredient prices today" | Full price list |

---

## 3. Nutrition Analysis (10 Tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| NA-01 | "What's the protein content in Nursery Diet 1?" | Crude protein % |
| NA-02 | "Calcium level in broiler starter feed" | Calcium % |
| NA-03 | "Phosphorus content for grower pigs" | Phosphorus % |
| NA-04 | "Compare protein between nursery and finisher diets" | Comparison |
| NA-05 | "Does Layer Diet meet NRC standards?" | NRC compliance check |
| NA-06 | "Lysine content in sow lactation feed" | Lysine % |
| NA-07 | "Energy level in beef cattle finisher" | ME/DE kcal/kg |
| NA-08 | "Nutrient profile for trout grower" | Full nutrition table |
| NA-09 | "Which formula has highest protein?" | Ranking list |
| NA-10 | "Analyze nutrition for all swine formulas" | Swine nutrition summary |

---

## 4. Customer Management (8 Tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| CM-01 | "Add new customer: John Smith, phone 555-1234, pig farmer" | Customer created |
| CM-02 | "Register client Mary Jones, raises beef cattle, Texas" | Customer created |
| CM-03 | "Find customer John" | Customer details |
| CM-04 | "Show all my customers" | Customer list |
| CM-05 | "Update John Smith's phone to 555-9999" | Updated |
| CM-06 | "Which customers raise pigs?" | Filtered list |
| CM-07 | "Delete customer Mary Jones" | Deleted |
| CM-08 | "How many customers do I have?" | Count |

---

## 5. Smart Reminders (6 Tests)

| ID | Test Case (Natural Language) | Expected |
|----|------------------------------|----------|
| SR-01 | "Remind me to check corn price tomorrow morning" | Reminder set |
| SR-02 | "Alert me when soybean meal drops below $300" | Price alert created |
| SR-03 | "Weekly feed cost report, every Monday 8am" | Recurring report |
| SR-04 | "Notify when nursery feed cost exceeds $280" | Cost threshold alert |
| SR-05 | "Remind customer John's delivery date next week" | Delivery reminder |
| SR-06 | "Show all my active reminders" | Reminder list |

---

## 6. Language Modes (12 Tests)

### Chinese (4 tests)

| ID | Test Case | Expected |
|----|-----------|----------|
| LM-01 | "保育料1号多少钱一吨" | Nursery Diet 1 cost |
| LM-02 | "玉米今天价格" | Corn price |
| LM-03 | "添加客户张三，养猪的" | Customer created |
| LM-04 | "所有配方成本对比" | Cost comparison |

### Mixed Chinese-English (4 tests)

| ID | Test Case | Expected |
|----|-----------|----------|
| LM-05 | "Nursery Diet 1 成本是多少" | Cost returned |
| LM-06 | "Soybean meal 今天价格" | Price returned |
| LM-07 | "Beef Cattle Finisher 配方成本" | Cost returned |
| LM-08 | "查询 Corn 价格" | Price returned |

### English (4 tests)

| ID | Test Case | Expected |
|----|-----------|----------|
| LM-09 | "cost of Nursery Diet 1" | Cost returned |
| LM-10 | "today's corn price" | Price returned |
| LM-11 | "add new customer John Smith" | Customer created |
| LM-12 | "show formula cost comparison" | Comparison table |

---

## 7. Error Handling (10 Tests)

| ID | Test Case (Natural Language) | Expected Error |
|----|------------------------------|----------------|
| EH-01 | "Cost of Unknown Formula XYZ" | Formula not found |
| EH-02 | "Price of imaginary ingredient" | Ingredient not found |
| EH-03 | "Calculate cost" (no formula specified) | Missing parameter |
| EH-04 | "Add customer" (no details) | Missing info |
| EH-05 | "Remind me" (no time/task) | Missing reminder details |
| EH-06 | "Show customer Nonexistent Person" | Customer not found |
| EH-07 | "Delete formula Nursery Diet 1" | Permission denied |
| EH-08 | "Update price corn to $0" | Invalid price |
| EH-09 | "Feed cost for dinosaur" | Animal type invalid |
| EH-10 | "What's the price?" (no ingredient) | Missing ingredient |

---

## Test Execution Script

```python
# Generate test prompts for automated testing
TEST_PROMPTS = [
    # Formula Costs
    "How much does nursery pig feed cost per ton?",
    "Beef cattle finisher feed price",
    "Broiler starter diet cost",
    # ... (full list in execution)
    
    # Ingredient Prices
    "What's corn price today?",
    "Soybean meal cost per ton",
    # ...
    
    # Nutrition
    "Protein content in Nursery Diet 1",
    # ...
    
    # Customer
    "Add customer John Smith, pig farmer, 555-1234",
    # ...
]

# Run tests via skill execute()
async def run_comprehensive_tests():
    results = []
    for prompt in TEST_PROMPTS:
        result = await skill.execute(user_id, prompt)
        results.append({
            'prompt': prompt,
            'success': result['success'],
            'response': result
        })
    return results
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Formula Cost Success Rate | ≥95% (36/38) |
| Price Query Success Rate | ≥90% (19/21) |
| Nutrition Analysis | ≥80% (8/10) |
| Customer Management | ≥75% (6/8) |
| Language Mode Support | ≥80% (10/12) |
| Error Handling Accuracy | ≥90% (9/10) |

---

## Next Steps

1. **Generate full test prompts list** (105 natural language queries)
2. **Run automated test suite** via skill.execute()
3. **Capture results** and identify failures
4. **Fix issues** in skill implementations
5. **Regression test** after fixes