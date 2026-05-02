-- FeedSales AI Database Schema
-- Version: 1.7.0 (Subscription & Referral System)

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ============================================
-- Subscription Plans
-- ============================================
CREATE TABLE IF NOT EXISTS subscription_plans (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,          -- 'free', 'starter', 'pro'
    display_name TEXT NOT NULL,         -- 'Free', 'Starter', 'Pro'
    price_monthly REAL NOT NULL,        -- 0, 9.9, 39.99
    queries_per_day INTEGER NOT NULL,   -- 3, 50, -1 (unlimited)
    max_customers INTEGER NOT NULL,     -- 5, 50, 200
    features TEXT,                      -- JSON array of feature names
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Seed default plans
INSERT OR IGNORE INTO subscription_plans (id, name, display_name, price_monthly, queries_per_day, max_customers, features) VALUES
    (1, 'free', 'Free', 0.0, 10, 5, '["basic queries", "price lookup", "formula cost"]'),
    (2, 'starter', 'Starter', 9.99, 50, 50, '["basic queries", "price lookup", "formula cost", "customer records", "reminders"]'),
    (3, 'pro', 'Pro', 29.99, -1, 200, '["basic queries", "price lookup", "formula cost", "customer records", "reminders", "nutrition analysis", "priority support"]');

-- ============================================
-- User Subscriptions
-- ============================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    plan_id INTEGER NOT NULL DEFAULT 1,
    is_in_trial INTEGER DEFAULT 0,
    trial_started_at TEXT,
    trial_ends_at TEXT,
    referral_bonus_days INTEGER DEFAULT 0,
    pro_bonus_months INTEGER DEFAULT 0,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
);

-- ============================================
-- Daily Query Usage
-- ============================================
CREATE TABLE IF NOT EXISTS daily_usage (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    usage_date TEXT NOT NULL,
    query_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_usage_user_date ON daily_usage(user_id, usage_date);

-- ============================================
-- Referrals
-- ============================================
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY,
    referrer_id TEXT NOT NULL,
    referee_id TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'completed',
    bonus_days INTEGER DEFAULT 7,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES subscriptions(user_id),
    FOREIGN KEY (referee_id) REFERENCES subscriptions(user_id)
);

CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referee ON referrals(referee_id);

-- ============================================
-- Users (existing table, preserve existing schema)
-- ============================================
-- Note: users table already exists with different schema
-- Do not recreate, just ensure it exists
CREATE TABLE IF NOT EXISTS users (
    open_id TEXT NOT NULL UNIQUE,
    telegram_user_id TEXT,
    feishu_user_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Customers (existing table - preserve schema)
-- ============================================
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    animal_type TEXT,
    scale INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    version INTEGER
);

-- ============================================
-- Reminders (v2 schema)
-- ============================================
CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('price', 'formula_cost')),
    ingredient TEXT,
    ingredient_code TEXT,
    formula TEXT,
    formula_id TEXT,
    threshold REAL NOT NULL,
    condition TEXT NOT NULL CHECK(condition IN ('above', 'below')),
    enabled BOOLEAN DEFAULT 1,
    last_triggered_at TEXT,
    trigger_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_enabled ON reminders(enabled);
CREATE INDEX IF NOT EXISTS idx_reminders_type_ingredient ON reminders(type, ingredient_code);
CREATE INDEX IF NOT EXISTS idx_reminders_type_formula ON reminders(type, formula_id);

-- ============================================
-- Formulas (existing table - preserve schema)
-- ============================================
CREATE TABLE IF NOT EXISTS formulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT NOT NULL,
    name TEXT NOT NULL,
    animal_type TEXT,
    stage_type TEXT NOT NULL,
    weight_range TEXT,
    notes TEXT,
    version INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS formula_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula_id INTEGER NOT NULL,
    ingredient_name TEXT NOT NULL,
    ratio_percent REAL NOT NULL CHECK(ratio_percent >= 0 AND ratio_percent <= 100),
    ingredient_code TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
);

-- ============================================
-- Ingredient Prices (existing table - preserve schema)
-- ============================================
CREATE TABLE IF NOT EXISTS ingredient_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT,
    ingredient_code TEXT NOT NULL,
    ingredient_name TEXT NOT NULL,
    price REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    unit TEXT DEFAULT 'ton',
    source TEXT DEFAULT 'barchart',
    price_date DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Calculation History
-- ============================================
CREATE TABLE IF NOT EXISTS calculation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT NOT NULL,
    formula_name TEXT NOT NULL,
    total_cost REAL NOT NULL,
    cost_per_ton REAL NOT NULL,
    ingredients_json TEXT NOT NULL,
    data_source TEXT DEFAULT 'barchart',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_open_id) REFERENCES users(open_id)
);

-- ============================================
-- User Onboarding
-- ============================================
CREATE TABLE IF NOT EXISTS user_onboarding (
    user_id TEXT PRIMARY KEY,
    onboarding_step INTEGER DEFAULT 0,
    first_action_type TEXT,
    onboarding_started_at TEXT,
    onboarding_completed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Audit Log
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    result TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- Price History (existing table - preserve schema)
-- ============================================
-- Note: price_history table may not exist, create if needed
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY,
    ingredient_code TEXT NOT NULL,
    price REAL NOT NULL,
    source TEXT,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_price_history_code ON price_history(ingredient_code);
