---
name: formula_cost_skill
description: Feed formula cost calculation. Triggers when user asks about formula cost, price calculation. Examples: "calculate Nursery Diet 1 cost", "how much is Beef Cattle Starter per ton"
---

# Formula Cost Calculation Skill

## ⚠️ Important Rules

- ❌ **NEVER** give users commands to run themselves
- ✅ **ALWAYS reply in English**
- ✅ **Call the unified skill runner via exec tool**

## When to Use

- "calculate Nursery Diet 1 cost"
- "how much is Beef Cattle Starter per ton"
- "formula cost query"
- "价格计算" (Chinese input → English output)

## How to Execute

Use exec tool to call the unified skill runner:

```bash
python3 {baseDir}/../../scripts/run_skill.py cost "<user message>"
```

Example for "Beef Cattle Starter cost":
```bash
python3 {baseDir}/../../scripts/run_skill.py cost "Beef Cattle Starter cost"
```

## Workflow

1. Extract formula name from user message
2. Call: `python3 {baseDir}/../../scripts/run_skill.py cost "<formula_name> cost"`
3. Parse JSON output and format in English

## Output Format (English)

```markdown
| Formula | Cost | Animal | Stage |
|---------|------|--------|-------|
| Beef Cattle Starter | $125.40/ton ($0.125/kg) | Beef Cattle | Starter |

**Ingredient Breakdown:**

| Ingredient | Inclusion % | Cost Contribution |
|------------|-------------|-------------------|
| Soybean meal | 20% | $70.00 |
| Alfalfa hay | 20% | $44.00 |
| Dicalcium phosphate | 1.5% | $9.75 |
| Limestone | 1% | $1.20 |
| Salt | 0.3% | $0.45 |
```

## Available Formulas

- **Swine**: Nursery Diet 1, Growing Diet, Finishing Diet
- **Beef Cattle**: Starter, Grower, Finisher
- **Broiler**: Starter, Grower, Finisher
- **Layer**: Starter, Grower, Laying
- **Others**: Turkey, Lamb, Goat, Duck, Trout, Catfish

## Error Handling

- Formula not found: List available formulas
- Price missing: Show partial calculation with warning
- Script error: Apologize and suggest retry