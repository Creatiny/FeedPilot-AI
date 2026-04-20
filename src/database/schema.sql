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
    (1, 'free', 'Free', 0.0, 3, 5, '["basic queries", "price lookup", "formula cost"]'),
    (2, 'starter', 'Starter', 9.9, 50, 50, '["basic queries", "price lookup", "formula cost", "customer records", "reminders"]'),
    (3, 'pro', 'Pro', 39.99, -1, 200, '["basic queries", "price lookup", "formula cost", "customer records", "reminders", "nutrition analysis", "priority support"]');

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
-- Note: customers table already exists with owner_open_id instead of user_id
-- Do not recreate

-- ============================================
-- Reminders (existing table - preserve schema)
-- ============================================
-- Note: reminders table already exists
-- Do not recreate

-- ============================================
-- Formulas (existing table - preserve schema)
-- ============================================
-- Note: formulas table already exists with owner_open_id instead of user_id
-- Do not recreate

-- ============================================
-- Ingredient Prices (existing table - preserve schema)
-- ============================================
-- Note: ingredient_prices table already exists
-- Do not recreate

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
