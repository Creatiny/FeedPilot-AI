---
name: price_lookup_skill
description: Ingredient price lookup. Triggers when user asks about ingredient prices, current prices. Examples: "corn price", "soybean meal price", "Barley price"
---

# Ingredient Price Lookup Skill

## ⚠️ Important Rules

- ❌ **NEVER** give users commands to run themselves
- ✅ **ALWAYS reply in English**
- ✅ **Call the unified skill runner via exec tool**

## When to Use

- "corn price", "Barley price", "soybean meal price"
- "what's the price of X"
- "ingredient price query"
- "玉米价格" (Chinese input → English output)

## How to Execute

Use exec tool to call the unified skill runner:

```bash
python3 {baseDir}/../../scripts/run_skill.py price "<user message>"
```

Example for "Barley price":
```bash
python3 {baseDir}/../../scripts/run_skill.py price "Barley price"
```

## Workflow

1. Extract ingredient name from user message
2. Call: `python3 {baseDir}/../../scripts/run_skill.py price "<ingredient_name> price"`
3. Parse JSON output and format in English

## Output Format (English)

**Price Found:**
```
Ingredient: Barley
Price: $158/ton
Source: USDA NASS
Date: 2026-03-31
```

**Auto-added:**
```
Ingredient: Oats
Price: $150/ton
Source: Reference (auto-added)
```

**Not Found:**
```
Ingredient 'X' not found in database.
Supported ingredients: Corn, Wheat, Barley, Soybean meal, Fish meal...
```

## Supported Ingredients

| Category | Ingredients |
|----------|-------------|
| Grains | Corn, Wheat, Barley, Sorghum, Oats, Rice |
| Proteins | Soybean meal, Fish meal, Canola meal, Cottonseed meal |
| Minerals | Limestone, Dicalcium phosphate, Salt |
| Additives | L-Lysine, DL-Methionine, Premix |
| Forage | Alfalfa, Corn silage, Grass hay |

## Error Handling

- Price not found: Skill will attempt auto-add
- Auto-add fails: Return friendly message with supported ingredients
- Script error: Apologize and suggest retry