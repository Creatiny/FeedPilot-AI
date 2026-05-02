# FeedPilot AI — 支付 Webhook 实施设计

## 一、目标

统一处理 Telegram Stars 和 Gumroad 两种支付方式，通过一个 webhook server 激活用户订阅。

## 二、现有架构

```
用户 → OpenClaw Telegram Bot → FeedPilot Skill (run_skill.py) → SQLite DB
```

**数据库关键表：**
- `subscription_plans` — 计划定义（free/starter/pro）
- `subscriptions` — 用户订阅状态（plan_id, is_in_trial, referral_bonus_days, pro_bonus_months）

**现有字段（未使用）：**
- `stripe_customer_id` — 可复用为 `payment_customer_id`
- `stripe_subscription_id` — 可复用为 `external_subscription_id`

## 三、新架构

```
┌─────────────────────────────────────────────────────────┐
│                    Webhook Server                        │
│                  (Python Flask/FastAPI)                   │
│                     端口: 8080                            │
├─────────────────────────────────────────────────────────┤
│  POST /webhook/telegram   ← Telegram Stars 支付回调      │
│  POST /webhook/gumroad    ← Gumroad 订阅回调             │
│  GET  /health             ← 健康检查                     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  SQLite DB     │
              │  (共享)        │
              └────────────────┘
                       ▲
                       │
┌──────────────────────┴──────────────────────────────────┐
│              OpenClaw Telegram Bot                       │
│         (webhook 模式，接收 Telegram 更新)                │
└─────────────────────────────────────────────────────────┘
```

## 四、数据库 Schema 变更

### 4.1 subscriptions 表新增字段

```sql
ALTER TABLE subscriptions ADD COLUMN payment_method TEXT DEFAULT 'free';
-- 'free', 'telegram_stars', 'gumroad'

ALTER TABLE subscriptions ADD COLUMN payment_id TEXT;
-- Telegram: payment_telegram_payment_id (Stars 交易唯一 ID)
-- Gumroad: Gumroad sale_id

ALTER TABLE subscriptions ADD COLUMN subscription_expires_at TEXT;
-- 订阅到期时间（用于月卡/年卡）

ALTER TABLE subscriptions ADD COLUMN gumroad_email TEXT;
-- Gumroad 买家 email（用于关联）
```

### 4.2 新增 payment_logs 表

```sql
CREATE TABLE payment_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    payment_method TEXT NOT NULL,        -- 'telegram_stars', 'gumroad'
    payment_id TEXT NOT NULL UNIQUE,     -- 去重用
    plan_id INTEGER NOT NULL,
    amount REAL,                         -- 金额（USD 或 Stars）
    currency TEXT DEFAULT 'USD',         -- 'USD', 'XTR'
    status TEXT DEFAULT 'pending',       -- 'pending', 'completed', 'refunded'
    raw_data TEXT,                       -- 原始 webhook 数据（JSON）
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
);
```

## 五、支付流程

### 5.1 Telegram Stars 支付流程

```
用户: /subscribe
    ↓
Bot: 显示计划选择（Stars 价格）
    ↓
用户: 选择 Starter 月卡
    ↓
Bot: 发送 Invoice（Telegram API: sendInvoice）
    ↓
用户: 点击 Pay → 输入密码 → 支付完成
    ↓
Telegram: 发送 pre_checkout_query 到 webhook
    ↓
Webhook Server: 验证 → 返回 ApprovePreCheckoutQuery
    ↓
Telegram: 发送 successful_payment 到 webhook
    ↓
Webhook Server:
    1. 验证 payment_id 去重
    2. 更新 subscriptions 表（plan_id, payment_method, expires_at）
    3. 记录 payment_logs
    4. 返回 200 OK
    ↓
Bot: 通知用户 "✅ 订阅已激活！"
```

### 5.2 Gumroad 支付流程

```
用户: 在 Gumroad 网页付款
    ↓
Gumroad: POST /webhook/gumroad
    ↓
Webhook Server:
    1. 验证 HMAC 签名
    2. 提取 email, plan_tier, sale_id
    3. 通过 gumroad_email 查找 user_id（或新建）
    4. 更新 subscriptions 表
    5. 记录 payment_logs
    6. 返回 200 OK
    ↓
Bot: 用户下次交互时自动获得新权限
```

## 六、Telegram Stars 定价

| Plan | USD | Stars (建议) | 说明 |
|------|-----|-------------|------|
| Starter 月卡 | $9.99 | 700 ⭐ | |
| Starter 年卡 | $99.99 | 7,000 ⭐ | |
| Pro 月卡 | $29.99 | 2,100 ⭐ | |
| Pro 年卡 | $299.99 | 21,000 ⭐ | |

> Stars 价格需参考 Telegram 官方 Star 购买价格表调整。

## 七、Webhook Server 设计

### 7.1 技术栈

- **框架:** FastAPI (Python)
- **数据库:** SQLite (共享 FeedPilot DB)
- **端口:** 8080
- **部署:** systemd service

### 7.2 端点设计

```
POST /webhook/telegram
  - 处理 Telegram Stars pre_checkout_query
  - 处理 Telegram Stars successful_payment
  - 处理 Telegram subscription 特殊回调

POST /webhook/gumroad
  - 处理 Gumroad sale 事件
  - 处理 Gumroad refund 事件
  - 处理 Gumroad subscription 事件

GET /health
  - 健康检查
```

### 7.3 安全设计

| 来源 | 验证方式 |
|------|---------|
| Telegram | Bot Token 验证（webhook secret） |
| Gumroad | HMAC-SHA256 签名验证 |

### 7.4 错误处理

- 支付回调必须返回 200 OK，否则 Telegram/Gumroad 会重试
- 所有操作先记录日志，再更新数据库
- payment_id 唯一约束防止重复处理

## 八、Bot 命令变更

### 8.1 /subscribe 命令

```
用户: /subscribe

Bot: 🐔 选择你的订阅计划：

      ┌─────────────────────────────────────┐
      │  Starter        │  Pro              │
│  700 ⭐/月      │  2,100 ⭐/月      │
│  7,000 ⭐/年    │  21,000 ⭐/年     │
      └─────────────────────────────────────┘

      1️⃣ Starter 月卡 (700 ⭐)
      2️⃣ Starter 年卡 (7,000 ⭐)
      3️⃣ Pro 月卡 (2,100 ⭐)
      4️⃣ Pro 年卡 (21,000 ⭐)
      5️⃣ Gumroad（信用卡/PayPal）

用户: 1

Bot: [发送 Invoice → 用户支付 → 激活]
Bot: ✅ Starter 月卡已激活！有效期 30 天。
```

### 8.2 /subscription 命令

```
用户: /subscription

Bot: 📋 你的订阅状态：

      Plan: Starter
      支付方式: Telegram Stars
      有效期至: 2026-05-30
      今日查询: 12/50

      升级: /subscribe
```

## 九、文件结构

```
/tmp/feedpilot-ai/
├── webhook_server/
│   ├── main.py              # FastAPI 入口
│   ├── telegram_handler.py  # Telegram Stars 处理
│   ├── gumroad_handler.py   # Gumroad 处理
│   ├── database.py          # 数据库操作
│   └── config.py            # 配置（bot token, webhook secret 等）
├── scripts/
│   ├── run_skill.py         # 现有（更新 /subscribe 命令）
│   └── ...
└── data/
    └── feed_sales.db        # 共享数据库
```

## 十、实施步骤

| 步骤 | 内容 | 优先级 |
|------|------|--------|
| 1 | 数据库 schema 变更（新增字段 + payment_logs 表） | 🔴 |
| 2 | 搭建 webhook server 框架 | 🔴 |
| 3 | 实现 Telegram Stars 处理（pre_checkout + successful_payment） | 🔴 |
| 4 | 实现 Gumroad webhook 处理 | 🟡 |
| 5 | 更新 run_skill.py 的 /subscribe 命令 | 🔴 |
| 6 | 配置 OpenClaw Telegram bot 为 webhook 模式 | 🔴 |
| 7 | 配置 systemd service | 🟡 |
| 8 | 测试验证 | 🔴 |

## 十一、待确认项

| 项目 | 状态 |
|------|------|
| Telegram bot webhook URL（需公网 HTTPS） | 待确认 |
| Gumroad webhook URL 配置 | 待确认 |
| Stars 定价是否合理 | 待确认 |
| 到期提醒 cron job | 后续实现 |
