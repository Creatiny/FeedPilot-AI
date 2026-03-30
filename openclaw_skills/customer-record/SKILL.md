---
name: customer-record
description: "客户记录管理 - 管理饲料销售客户信息。使用当：用户要求添加/查询/更新/删除客户、显示所有客户、客户列表。支持多租户隔离。"
metadata:
  {
    "openclaw":
      {
        "emoji": "👥",
        "requires": { "bins": ["python3"], "files": ["feed_sales.db"] },
      },
  }
---

# Customer Record Skill (客户记录管理)

管理饲料销售客户信息，支持多租户隔离。

## When to Use

✅ **使用此 skill 当：**

- "添加客户 John"
- "显示所有客户"
- "查找客户 Smith"
- "我有多少客户"

## Execution

使用统一启动器执行：

```bash
/usr/bin/python3 /root/.openclaw/workspace/feed-ai-assistant/openclaw_skills/launcher.py \
  --skill customer-record \
  --user-id <user_id> \
  --message "show all customers"
```

## Supported Actions

| Action | Example |
|--------|---------|
| add | "add customer John, pig farmer" |
| list | "show all customers" |
| find | "find customer Smith" |
| update | "update customer John phone 999" |
| delete | "delete customer John" |
| count | "how many customers" |

## Output Example

```json
{
  "success": true,
  "data": {
    "message": "Found 5 customers",
    "count": 5,
    "customers": [...]
  }
}
```