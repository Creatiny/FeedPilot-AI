---
name: price-lookup
description: "原料价格查询 - 查询饲料原料的最新价格。使用当：用户询问原料价格、玉米价格、豆粕多少钱。支持私有价格和公共价格。"
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires": { "bins": ["python3"], "files": ["feed_sales.db"] },
      },
  }
---

# Price Lookup Skill (原料价格查询)

查询饲料原料的最新价格，支持私有价格和公共价格。

## When to Use

✅ **使用此 skill 当：**

- "玉米价格是多少"
- "豆粕多少钱一吨"
- "Fish meal price"
- "所有原料价格"

## Execution

使用统一启动器执行：

```bash
/usr/bin/python3 /root/.openclaw/workspace/feed-ai-assistant/openclaw_skills/launcher.py \
  --skill price-lookup \
  --user-id <user_id> \
  --message "玉米价格"
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