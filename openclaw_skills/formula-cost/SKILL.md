---
name: formula-cost
description: "配方成本计算 - 计算饲料配方的总成本。使用当：用户询问配方成本、配方多少钱、配方价格。支持私有价格优先查询。"
metadata:
  {
    "openclaw":
      {
        "emoji": "💰",
        "requires": { "bins": ["python3"], "files": ["feed_sales.db"] },
      },
  }
---

# Formula Cost Skill (配方成本计算)

计算饲料配方的总成本，基于配方成分和原料价格。

## When to Use

✅ **使用此 skill 当：**

- "Nursery Diet 1 成本是多少"
- "配方多少钱一吨"
- "计算 Grower Diet 成本"
- "Compare Nursery vs Grower formula cost"

## Execution

使用统一启动器执行：

```bash
/usr/bin/python3 /root/.openclaw/workspace/feed-ai-assistant/openclaw_skills/launcher.py \
  --skill formula-cost \
  --user-id <user_id> \
  --message "<formula_name>成本"
```

## Output Example

```json
{
  "success": true,
  "data": {
    "formula_name": "Nursery Diet 1",
    "animal_type": "Swine",
    "stage": "Nursery",
    "cost_per_ton": 284.30,
    "cost_per_kg": 0.2843,
    "currency": "USD",
    "details": [...],
    "price_sources": {"Corn": "default", "Soybean meal": "public"}
  }
}
```

## Dependencies

- Database: `/root/.openclaw/workspace/feed-ai-assistant/data/feed_sales.db`
- Services: CalculationService (FormulaService + PriceService)