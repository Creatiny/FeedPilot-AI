---
name: formula-cost
description: "Feed formula cost calculation - Calculate total feed formula cost. Use when: user asks about formula cost, how much per ton, formula price. Supports private price priority lookup."
metadata:
  {
    "openclaw":
      {
        "emoji": "💰",
        "requires": { "bins": ["python3"], "files": ["feed_sales.db"] },
      },
  }
---

# Formula Cost Skill

Calculates the total cost of a feed formula based on formula ingredients and raw material prices.

## When to Use

✅ **Use this skill when:**

- "How much does Nursery Diet 1 cost?"
- "What is the cost per ton of Grower Diet?"
- "Calculate formula cost for Beef Finishing 1"
- "Compare Nursery vs Grower formula cost"

## Execution

Execute using the unified launcher:

```bash
/usr/bin/python3 /home/kenny/.openclaw/workspace-feedsales/openclaw_skills/launcher.py \
  --skill formula-cost \
  --user-id <user_id> \
  --message "<formula_name> cost"
```

## Output Example

```json
{
  "success": true,
  "data": {
    "formula_name": "Nursery Diet 1",
    "animal_type": "Swine",
    "stage": "Nursery",
    "cost_per_ton": 224.30,
    "cost_per_kg": 0.2243,
    "currency": "USD",
    "details": [...],
    "price_sources": {"Corn, grain": "public", "Soybean meal, 48%": "public"}
  }
}
```

## Dependencies

- Database: `/home/kenny/.openclaw/workspace-feedsales/data/feed_sales.db`
- Services: CalculationService (wraps FormulaService + PriceService)
