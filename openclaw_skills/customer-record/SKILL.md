---
name: customer-record
description: "Customer record management - Manage feed sales customer information. Use when: user asks to add/find/update/delete customer, show all customers, customer list. Supports multi-tenant isolation."
metadata:
  {
    "openclaw":
      {
        "emoji": "👥",
        "requires": { "bins": ["python3"], "files": ["feed_sales.db"] },
      },
  }
---

# Customer Record Skill

Manages feed sales customer information with multi-tenant isolation.

## When to Use

✅ **Use this skill when:**

- "Add customer John"
- "Show all my customers"
- "Find customer Smith"
- "How many customers do I have"

## Execution

Execute using the unified launcher:

```bash
/usr/bin/python3 /home/kenny/.openclaw/workspace-feedsales/openclaw_skills/launcher.py \
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
