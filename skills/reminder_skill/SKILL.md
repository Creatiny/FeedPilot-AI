---
name: reminder_skill
description: Create and manage price alerts and formula cost reminders. Users can set alerts for when ingredient prices or formula costs exceed or fall below a threshold.
triggers:
  - "alert when corn exceeds $100"
  - "remind me when soybean meal falls below $350"
  - "show my reminders"
  - "delete reminder"
---

# Reminder Skill

让用户通过对话创建价格提醒和配方成本监控。

## 触发场景

- "提醒我当豆粕价格超过 400 美元"
- "设置价格提醒"
- "当保育料成本超过 300 美元时通知我"
- "玉米价格低于 80 美元时提醒我"
- "查看我的提醒"
- "删除豆粕价格提醒"

## 工作流程

### 1. 创建提醒

1. 解析用户请求，提取：
   - 提醒类型（价格/配方成本）
   - 目标（原料/配方）
   - 阈值
   - 条件（above/below）
2. 从 inbound_meta 获取 user_id
3. 调用 ReminderService.create_reminder()
4. 返回确认信息

**代码示例**：
```python
from src.services import ReminderService
from src.database.pool import DatabasePool

db_pool = DatabasePool("data/feed_sales.db")
reminder_service = ReminderService(db_pool)

result = reminder_service.create_reminder(
    user_id="123456",
    reminder_type="price",
    threshold=400,
    condition="above",
    ingredient="Soybean meal, 48%",
    ingredient_code="ING_SBM_48"
)

if result.success:
    print(f"✅ 已创建提醒: {result.data['id']}")
```

### 2. 查看提醒

1. 从 inbound_meta 获取 user_id
2. 调用 ReminderService.list_reminders()
3. 格式化返回

**代码示例**：
```python
result = reminder_service.list_reminders(user_id="123456")

if result.success:
    for reminder in result.data["reminders"]:
        print(f"- {reminder['ingredient']} {reminder['condition']} ${reminder['threshold']}")
```

### 3. 删除提醒

1. 从 inbound_meta 获取 user_id
2. 查询匹配的提醒
3. 确认后调用 ReminderService.delete_reminder()

**代码示例**：
```python
result = reminder_service.delete_reminder(
    reminder_id="xxx",
    user_id="123456"
)

if result.success:
    print("✅ 已删除")
```

## 用户隔离

所有操作必须带 user_id 过滤：
- 创建时使用 user_id
- 查看时只返回该用户的提醒
- 删除时验证 user_id 匹配

## 支持的原料

| 用户输入 | 标准名称 | 代码 |
|----------|----------|------|
| 豆粕 | Soybean meal, 48% | ING_SBM_48 |
| 玉米 | Corn, grain | ING_CORN |
| 鱼粉 | Fish meal, 65% | ING_FISH_65 |
| DDGS | DDGS, 28% | ING_DDGS_28 |
| 小麦 | Wheat, grain | ING_WHEAT |
| 麸皮 | Wheat bran | ING_WHEAT_BRAN |
| 豆油 | Soybean oil | ING_SBM_OIL |
| 磷酸氢钙 | Dicalcium phosphate | ING_DCP |
| 石粉 | Limestone | ING_LIMESTONE |
| 盐 | Salt | ING_SALT |
| 赖氨酸 | L-Lysine HCl | ING_LYSINE |
| 蛋氨酸 | DL-Methionine | ING_METHIONINE |
| 苜蓿草粉 | Alfalfa hay early bloom | ING_ALFALFA |

## 支持的配方

| 用户输入 | 标准名称 | ID |
|----------|----------|------|
| 保育料 | Nursery Diet 1 | FORMULA_NURSERY_1 |
| 育肥料 | Finishing Diet | FORMULA_FINISHING |
| 生长料 | Grower Diet 1 | FORMULA_GROWER_1 |
| 肉鸡料 | Broiler Starter | FORMULA_BROILER_STARTER |
| 蛋鸡料 | Layer Diet | FORMULA_LAYER |
| 肉牛育肥料 | Beef Cattle Finisher | FORMULA_BEEF_FINISHING |

## 文件结构

```
~/.openclaw/workspace-feedsales/
├── src/
│   ├── database/
│   │   └── pool.py          # DatabasePool (WAL 模式)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── price_service.py
│   │   ├── formula_service.py
│   │   ├── customer_service.py
│   │   ├── calculation_service.py
│   │   └── reminder_service.py  # ReminderService
│   └── types.py             # ServiceResult
└── skills/reminder_skill/
    ├── SKILL.md             # 本文件
    ├── scripts/
    │   └── reminder_cli.py  # CLI 工具
    ├── tests/
    │   └── test_reminders.py
    └── reference/
        └── ingredient_codes.json
```

## 统一检查任务

创建一个 cron 任务，每日检查所有用户的提醒：

```json
{
  "name": "Check All User Reminders",
  "agentId": "feedsales",
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *",
    "tz": "America/Chicago"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "Check all enabled reminders from the reminders table. For each reminder: 1) Get current price/formula cost from database, 2) Check if condition is met (above/below threshold), 3) If triggered, send notification to the user via sessions_send tool with sessionKey 'agent:feedsales:telegram:direct:{user_id}'. Use the user_id field to route notifications.",
    "thinking": "Query reminders table for all enabled reminders. For each reminder, query ingredient_prices or calculate formula cost. Compare to threshold. If condition met, use sessions_send to notify the user."
  }
}
```

## 示例对话

**用户**: 提醒我当豆粕价格超过 400 美元

**Agent**: 
```markdown
✅ 价格提醒已创建！

| 字段 | 值 |
|------|-----|
| 原料 | 豆粕 (Soybean meal, 48%) |
| 条件 | 超过 $400/吨 |
| 提醒 ID | abc12345 |

我会每天检查价格，当超过阈值时立即通知你。
```

---

**用户**: 查看我的提醒

**Agent**:
```markdown
📋 你的提醒列表 (3 个)：

| ID | 类型 | 目标 | 条件 |
|----|------|------|------|
| abc12345 | 价格 | 豆粕 | 超过 $400/吨 |
| def67890 | 价格 | 鱼粉 | 超过 $2000/吨 |
| ghi24680 | 配方成本 | 保育料 | 超过 $300/吨 |
```

---

**用户**: 删除豆粕价格提醒

**Agent**: 
```markdown
✅ 已删除提醒

| ID | 目标 | 条件 |
|----|------|------|
| abc12345 | 豆粕 | 超过 $400/吨 |
```
