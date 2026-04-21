---
name: nutrition-analysis
description: "Nutrition analysis - Analyze formula nutrition and compare with NRC standards. Use when: user asks about formula nutrition, nutritional composition, NRC standard comparison. Supports swine, chicken, cattle, etc."
metadata:
  {
    "openclaw":
      {
        "emoji": "🧬",
        "requires": { "bins": ["python3"], "files": ["feed_sales.db"] },
      },
  }
---

# Nutrition Analysis Skill

Analyzes feed formula nutrition composition and compares with NRC standards.

## When to Use

✅ **Use this skill when:**

- "Analyze Nursery Diet 1 nutrition"
- "What are the nutrition facts for this formula"
- "Compare with NRC standards"
- "Does this formula have enough protein"

## Execution

Execute using the unified launcher:

```bash
/usr/bin/python3 /home/kenny/.openclaw/workspace-feedsales/openclaw_skills/launcher.py \
  --skill nutrition-analysis \
  --user-id <user_id> \
  --message "analyze Nursery Diet 1 nutrition"
```

## NRC Standards

| Animal | Stages |
|--------|--------|
| Swine | Nursery, Growing, Finishing, Gestating, Lactating |
| Broiler | Starter, Grower, Finisher |
| Layer | Starter, Grower, Laying |
| Beef Cattle | Starter, Growing, Finishing |

## Output Example

```json
{
  "success": true,
  "data": {
    "formula": "Nursery Diet 1",
    "nutrition": {
      "protein": 19.1,
      "calcium": 1.89,
      "phosphorus": 1.23,
      "lysine": 1.15
    },
    "nrc_comparison": {
      "protein": {"actual": 19.1, "standard": 18.0, "status": "✓ Meets"}
    }
  }
}
```
