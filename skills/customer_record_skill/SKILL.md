---
name: customer_record_skill
description: Customer record management. Triggers when user needs to add, view, or manage customer records. Examples: "add new customer John", "show all customers", "find customer John"
---

# Customer Record Management Skill

## ⚠️ Important Rules

- ❌ **NEVER** give users commands to run themselves
- ✅ **ALWAYS reply in English**
- ✅ **Call the unified skill runner via exec tool**

## When to Use

- "add new customer John Smith"
- "show all my customers"
- "find customer John"
- "update John's phone number"
- "delete customer John"
- "how many customers do I have"

## How to Execute

Use exec tool to call the unified skill runner:

```bash
python3 {baseDir}/../../scripts/run_skill.py customer "<user message>"
```

Examples:
```bash
# Add customer
python3 {baseDir}/../../scripts/run_skill.py customer "add customer John Smith phone 555-1234"

# List customers
python3 {baseDir}/../../scripts/run_skill.py customer "show all customers"

# Find customer
python3 {baseDir}/../../scripts/run_skill.py customer "find customer John"
```

## Workflow

1. Parse action from user message (add/list/find/update/delete)
2. Call unified skill runner with appropriate message
3. Parse JSON output and format in English

## Output Format (English)

**Add Customer:**
```markdown
✓ Customer added successfully

| Field | Value |
|-------|-------|
| Name | John Smith |
| ID | 123 |
| Phone | 555-1234 |
```

**List Customers:**
```markdown
Found 3 customers:

| ID | Name | Farm Type | Scale | Phone |
|----|------|-----------|-------|-------|
| 1 | John Smith | Swine | 500 head | 555-1234 |
| 2 | Jane Doe | Beef Cattle | 200 head | 555-5678 |
| 3 | Bob Wilson | Broiler | 10,000 head | 555-9012 |
```

**Find Customer:**
```markdown
| Field | Value |
|-------|-------|
| Name | John Smith |
| Farm Type | Swine |
| Scale | 500 head |
| Phone | 555-1234 |
| Notes | Prefers text contact |
```

## Error Handling

- Customer not found: Suggest similar names or offer to add
- Missing required info: Ask for customer name
- Duplicate name: Warn and offer to update instead
- Script error: Apologize and suggest retry