---
name: onboarding
description: "New user onboarding - Guide new users through first valuable action. Use when: user sends /start, first message, or needs help getting started."
metadata:
  {
    "openclaw":
      {
        "emoji": "👋",
        "requires": { "bins": ["python3"], "files": ["feed_sales.db"] },
      },
  }
---

# Onboarding Skill

Guides new users through their first valuable action within 3 steps.

## When to Use

✅ **Use this skill when:**

- User sends /start
- User's first message
- User asks "how to use" or "help me start"

## Onboarding Flow

### Step 1: Welcome + Quick Choice

When user sends /start:

```
👋 Welcome to FeedSales AI!

I'm your pocket feed assistant. What do you want to do first?

1️⃣ Check ingredient prices
2️⃣ Calculate feed formula cost  
3️⃣ Set a customer reminder

Just type 1, 2, or 3 to start!
```

### Step 2: Guided First Action

**If user chooses 1 (Price Check):**
```
📊 Great choice! Let's check some prices.

Which ingredient? Type the name or choose:
• corn
• soybean meal
• fish meal
• wheat
• all (see all prices)
```

**If user chooses 2 (Formula Cost):**
```
🧮 Let's calculate a formula cost!

Tell me your formula ingredients, like:
"corn 60%, soybean meal 25%, premix 5%..."

Or type 'example' to see a sample calculation.
```

**If user chooses 3 (Reminder):**
```
⏰ Never miss a follow-up!

What should I remind you about?
Example: "Follow up with John next Monday"
```

### Step 3: Success + Next Steps

After user completes first action:

```
✅ Nice! You just checked your first price!

Here's what else you can do:
• /formula - Calculate feed cost
• /remind - Set customer reminders  
• /customer - Manage your customers
• /help - See all features

💡 Tip: Try asking "What's the corn price trend?" for insights!
```

## Tracking

Store in database:
- onboarding_started_at
- onboarding_step (1, 2, 3, completed)
- first_action_type (price, formula, reminder)
- onboarding_completed_at

## Implementation

```bash
/usr/bin/python3 /home/kenny/.openclaw/workspace-feedsales/openclaw_skills/launcher.py \
  --skill onboarding \
  --user-id <user_id> \
  --message "/start"
```

## Output Example

```json
{
  "success": true,
  "data": {
    "step": 1,
    "message": "👋 Welcome to FeedSales AI!...",
    "options": ["1️⃣ Check ingredient prices", "2️⃣ Calculate feed formula cost", "3️⃣ Set a customer reminder"]
  }
}
```
