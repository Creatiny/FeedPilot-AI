-- FeedSales AI v1.6 数据库 Schema
-- 启用 WAL 模式
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA foreign_keys = ON;

-- ============================================
-- 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    open_id TEXT PRIMARY KEY,              -- OpenClaw 用户 ID
    telegram_user_id TEXT UNIQUE,          -- Telegram 用户 ID
    feishu_user_id TEXT UNIQUE,            -- 飞书用户 ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 原料价格表（支持多租户隔离 + 乐观锁）
-- ============================================
CREATE TABLE IF NOT EXISTS ingredient_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT NOT NULL,           -- 所有者 ID（NULL = 公共数据）
    ingredient_code TEXT NOT NULL,         -- 原料代码
    ingredient_name TEXT NOT NULL,         -- 原料名称
    price REAL NOT NULL,                   -- 价格
    currency TEXT DEFAULT 'USD',           -- 货币（北美市场统一 USD）
    unit TEXT DEFAULT 'ton',               -- 单位
    source TEXT DEFAULT 'barchart',        -- 数据来源
    price_date DATE NOT NULL,              -- 价格日期
    version INTEGER DEFAULT 1,             -- 乐观锁版本号
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_open_id) REFERENCES users(open_id),
    UNIQUE(ingredient_code, price_date, owner_open_id)
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_prices_owner_date ON ingredient_prices(owner_open_id, price_date);
CREATE INDEX IF NOT EXISTS idx_prices_code ON ingredient_prices(ingredient_code);

-- ============================================
-- 配方表（支持多租户隔离 + 乐观锁）
-- ============================================
CREATE TABLE IF NOT EXISTS formulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT NOT NULL,           -- 所有者 ID
    name TEXT NOT NULL,                    -- 配方名称
    animal_type TEXT,                      -- 动物类型（Swine, Beef Cattle, Broiler 等）
    stage_type TEXT NOT NULL,              -- 饲养阶段
    weight_range TEXT,                     -- 体重范围
    notes TEXT,                            -- 备注
    version INTEGER DEFAULT 1,             -- 乐观锁版本号
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_open_id) REFERENCES users(open_id),
    UNIQUE(owner_open_id, name)
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_formulas_owner ON formulas(owner_open_id);
CREATE INDEX IF NOT EXISTS idx_formulas_stage ON formulas(stage_type);

-- ============================================
-- 配方成分表
-- ============================================
CREATE TABLE IF NOT EXISTS formula_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula_id INTEGER NOT NULL,
    ingredient_name TEXT NOT NULL,         -- 原料名称
    ratio_percent REAL NOT NULL CHECK(ratio_percent >= 0 AND ratio_percent <= 100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_formula_ingredients_formula ON formula_ingredients(formula_id);

-- ============================================
-- 客户数据表（支持多租户隔离 + 乐观锁）
-- ============================================
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT NOT NULL,           -- 所有者 ID
    name TEXT NOT NULL,                    -- 客户姓名
    phone TEXT,                            -- 电话
    address TEXT,                          -- 地址
    animal_type TEXT,                      -- 养殖类型
    scale INTEGER,                         -- 养殖规模
    notes TEXT,
    version INTEGER DEFAULT 1,             -- 乐观锁版本号
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_open_id) REFERENCES users(open_id)
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_customers_owner ON customers(owner_open_id);

-- ============================================
-- 计算历史表（支持多租户隔离）
-- ============================================
CREATE TABLE IF NOT EXISTS calculation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT NOT NULL,           -- 所有者 ID
    formula_name TEXT NOT NULL,            -- 配方名称
    total_cost REAL NOT NULL,              -- 总成本
    cost_per_ton REAL NOT NULL,            -- 每吨成本
    ingredients_json TEXT NOT NULL,        -- JSON 格式成分
    data_source TEXT DEFAULT 'barchart',   -- 数据来源
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_open_id) REFERENCES users(open_id)
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_history_owner ON calculation_history(owner_open_id);
CREATE INDEX IF NOT EXISTS idx_history_date ON calculation_history(created_at);

-- ============================================
-- 审计日志表
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

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id, timestamp);

