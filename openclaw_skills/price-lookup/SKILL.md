---
name: price-lookup
description: "Ingredient price lookup - Query latest feed ingredient prices. Use when: user asks about ingredient prices, corn price, soybean meal cost. Supports private prices and public prices."
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires": { "bins": ["python3"], "files": ["feed_sales.db"] },
      },
  }
---

# Price Lookup Skill

Queries the latest prices for feed ingredients, supporting private prices and public fallback.

## When to Use

✅ **Use this skill when:**

- "What is the corn price?"
- "Soybean meal price per ton"
- "Fish meal price"
- "All ingredient prices"

## Execution

Execute using the unified launcher:

```bash
/usr/bin/python3 /home/kenny/.openclaw/workspace-feedsales/openclaw_skills/launcher.py \
  --skill price-lookup \
  --user-id <user_id> \
  --message "corn price"
```

## Output Example

```json
{
  "success": true,
  "data": {
    "message": "All ingredient prices",
    "count": 26,
    "prices": [...]
  }
}
```

## Supported Ingredients

- Corn (玉米)
- Soybean meal (豆粕)
- Fish meal (鱼粉)
- Wheat (小麦)
- DDGS
- Limestone (石粉)
- Premix (预混料)
- Dicalcium phosphate (磷酸氢钙)
- L-Lysine (赖氨酸)
- Methionine (蛋氨酸)
