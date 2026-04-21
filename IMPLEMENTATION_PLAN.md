# FeedSales Subscription & Referral Implementation Plan

## Goal
Implement subscription system, query limits, trial period, and referral mechanism for FeedSales AI MVP.

## Success Criteria
1. Users can check subscription status via `/subscription` command
2. Query limits enforced based on plan (Free: 3/day, Starter: 50/day, Pro: unlimited)
3. New users get 7-day trial automatically
4. Referral system: invite friend = 7 bonus days for both parties
5. All code has test coverage (TDD: RED-GREEN-REFACTOR)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      launcher.py                            │
│  run_subscription()  run_referral()  check_query_limit()   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              SubscriptionService                            │
│  - get_subscription_status()                                │
│  - start_trial()                                            │
│  - get_referral_link()                                      │
│  - add_referral_bonus()                                     │
│  - record_usage()                                           │
│  - check_query_limit()                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database (SQLite)                         │
│  Tables: subscription_plans, subscriptions,                 │
│          daily_usage, referrals                             │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### subscription_plans
```sql
CREATE TABLE IF NOT EXISTS subscription_plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,          -- 'free', 'starter', 'pro'
    price_monthly REAL NOT NULL,        -- 0, 9.9, 39.99
    queries_per_day INTEGER NOT NULL,   -- 3, 50, -1 (unlimited)
    max_customers INTEGER NOT NULL,     -- 5, 50, 200
    features TEXT                       -- JSON array of feature names
);
```

### subscriptions
```sql
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_id INTEGER NOT NULL DEFAULT 1,
    is_in_trial INTEGER DEFAULT 0,
    trial_started_at TEXT,
    trial_ends_at TEXT,
    referral_bonus_days INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id),
    UNIQUE(user_id)
);
```

### daily_usage
```sql
CREATE TABLE IF NOT EXISTS daily_usage (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    query_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, usage_date)
);
```

### referrals
```sql
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY,
    referrer_id TEXT NOT NULL,
    referee_id TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'completed',
    bonus_days INTEGER DEFAULT 7,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Implementation Tasks (TDD)

### Task 1: Database Schema (30 min)
**Files:** `src/database/schema.sql`

**Test First:**
```python
# tests/test_subscription_db.py
def test_subscription_plans_exist():
    """Verify default plans are seeded"""
    
def test_create_subscription():
    """Test creating a new user subscription"""
    
def test_daily_usage_tracking():
    """Test query count tracking per day"""
```

**Implementation:**
- Add subscription tables to schema.sql
- Seed default plans (free, starter, pro)
- Update DatabasePool to run schema on init

### Task 2: SubscriptionService (45 min)
**Files:** `src/services/subscription_service.py`

**Test First:**
```python
# tests/test_subscription_service.py
def test_get_subscription_status_new_user():
    """New user should have free plan"""
    
def test_start_trial():
    """Start 7-day trial for user"""
    
def test_check_query_limit_free_user():
    """Free user limited to 3 queries/day"""
    
def test_check_query_limit_pro_user():
    """Pro user has unlimited queries"""
    
def test_record_usage():
    """Usage should be recorded and counted"""
```

**Implementation:**
- SubscriptionService class with all methods
- Query limit logic with plan-based limits
- Trial period management

### Task 3: QueryLimitMiddleware (30 min)
**Files:** `src/middleware/query_limit.py`

**Test First:**
```python
# tests/test_query_limit_middleware.py
def test_check_limit_allowed():
    """User under limit should be allowed"""
    
def test_check_limit_exceeded():
    """User over limit should be blocked"""
    
def test_check_limit_unlimited():
    """Pro user should always be allowed"""
```

**Implementation:**
- Middleware that wraps SubscriptionService
- Returns clear error messages when limit exceeded

### Task 4: Referral System (30 min)
**Files:** `src/services/subscription_service.py` (extend)

**Test First:**
```python
# tests/test_referral.py
def test_get_referral_link():
    """Generate unique referral link for user"""
    
def test_apply_referral_bonus():
    """Both referrer and referee get bonus days"""
    
def test_cannot_refer_self():
    """User cannot use own referral link"""
    
def test_cannot_refer_twice():
    """Referee can only be referred once"""
```

**Implementation:**
- Generate referral codes from user_id
- Track referrals in database
- Apply bonus days to both parties

### Task 5: Launcher Integration (30 min)
**Files:** `openclaw_skills/launcher.py`

**Test First:**
```python
# tests/test_launcher_subscription.py
def test_run_subscription_status():
    """Test /subscription status command"""
    
def test_run_subscription_trial():
    """Test /subscription trial command"""
    
def test_run_referral_link():
    """Test /referral link command"""
    
def test_query_limit_blocks_request():
    """Test that limit exceeded returns error"""
```

**Implementation:**
- Wire up run_subscription() to SubscriptionService
- Wire up run_referral() to referral methods
- Ensure check_query_limit() works correctly

### Task 6: Onboarding Integration (20 min)
**Files:** `openclaw_skills/onboarding/skill.py`

**Test First:**
```python
# tests/test_onboarding_subscription.py
def test_new_user_gets_trial_prompt():
    """New user should see trial offer in onboarding"""
    
def test_onboarding_exempt_from_limits():
    """Onboarding skill should not count against query limit"""
```

**Implementation:**
- Add trial prompt to onboarding flow