---
name: nutrition-analysis
description: "营养分析 - 分析配方营养成分并与 NRC 标准对比。使用当：用户询问配方营养、营养成分、NRC 标准对比。支持猪、鸡、牛等动物。"
metadata:
  {
    "openclaw":
      {
        "emoji": "🧬",
        "requires": { "bins": ["python3"], "files": ["feed_sales.db"] },
      },
  }
---

# Nutrition Analysis Skill (营养分析)

分析饲料配方营养成分并与 NRC 标准对比。

## When to Use

✅ **使用此 skill 当：**

- "分析 Nursery Diet 1 营养"
- "配方营养成分"
- "NRC 标准对比"
- "这个配方蛋白质够吗"

## Execution

使用统一启动器执行：

```bash
/usr/bin/python3 /root/.openclaw/workspace/feed-ai-assistant/openclaw_skills/launcher.py \
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