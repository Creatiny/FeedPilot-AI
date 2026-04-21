# FeedPilot AI Reminder 用户隔离设计方案

## 文档信息

- **版本**: 1.0
- **日期**: 2026-04-05
- **作者**: OpenClaw Assistant
- **状态**: 待实现

---

## 1. 背景与问题

### 1.1 业务需求

FeedPilot AI 需要为每个 Telegram 用户提供个性化的价格提醒功能：

```
用户 A: "提醒我当豆粕价格超过 400 美元" → 创建任务，通知用户 A
用户 B: "查看我的提醒" → 只看到用户 B 的任务
用户 C: "删除豆粕提醒" → 只删除用户 C 的任务
```

### 1.2 现状分析

| 层面 | 现状 | 问题 |
|------|------|------|
| **工具权限** | FeedPilot AI 使用 `coding` profile | 无法调用 `cron` 工具（cron 在 `group:automation`） |
| **用户系统** | OpenClaw 有 `allowFrom` 授权机制 | 只控制谁能访问，不区分用户身份 |
| **cron 任务** | 全局任务，通过 `delivery.to` 指定目标 | 无用户 ID 字段，无法按用户过滤 |
| **FeedPilot DB** | 有 `authorized.json` 存储授权用户 | 无用户数据表，无用户状态管理 |

### 1.3 核心挑战

1. **工具权限不足** - FeedPilot AI 无法调用 cron 工具
2. **cron 任务无用户字段** - 无法直接实现用户隔离
3. **多用户数据管理** - 需要存储每个用户的提醒配置
4. **通知路由** - 需要确保通知发送给正确的用户

---

## 2. 设计目标

### 2.1 功能目标

- ✅ 用户可以创建价格提醒（原料价格、配方成本）
- ✅ 用户可以查看自己的提醒列表
- ✅ 用户可以删除自己的提醒
- ✅ 系统每日自动检查所有提醒条件
- ✅ 条件触发时通知对应用户

### 2.2 非功能目标

- **用户隔离**: 用户只能看到和操作自己的提醒
- **数据安全**: 用户数据不泄露给其他用户
- **可扩展性**: 支持未来添加更多提醒类型
- **可维护性**: 代码清晰，易于理解和修改

---

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Telegram 用户                          │
│                  (user_id: 123456, 789012, ...)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FeedPilot AI Agent (feedsales)                     │   │
│  │  - workspace: ~/.openclaw/workspace-feedsales       │   │
│  │  - tools: coding + group:automation                 │   │
│  │  - skills: reminder_skill, formula_cost_skill, ...  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  FeedPilot 数据层                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  feed_sales.db (SQLite)                             │   │
│  │  ├── ingredient_prices (现有)                       │   │
│  │  ├── formulas (现有)                                │   │
│  │  └── reminders (新增)                               │   │
│  │      ├── id (PRIMARY KEY)                           │   │
│  │      ├── user_id (用户 Telegram ID)                 │   │
│  │      ├── type (price | formula_cost)                │   │
│  │      ├── ingredient / formula                       │   │
│  │      ├── threshold (阈值)                           │   │
│  │      ├── condition (above | below)                  │   │
│  │      └── enabled (是否启用)                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   OpenClaw Cron 系统                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  统一检查任务 (每日执行)                             │   │
│  │  - 查询 reminders 表所有启用的提醒                  │   │
│  │  - 获取最新价格数据                                 │   │
│  │  - 检查每个提醒的条件                               │   │
│  │  - 触发时发送消息对应用户                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 数据流程

#### 创建提醒

```
用户: "提醒我当豆粕价格超过 400 美元"
     │
     ▼
┌─────────────────────────────────────────┐
│ FeedPilot AI 解析请求                    │
│ - ingredient: "Soybean meal, 48%"       │
│ - threshold: 400                        │
│ - condition: "above"                    │
│ - user_id: 从 inbound_meta 获取         │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 写入 reminders 表                        │
│ INSERT INTO reminders                   │
│ (id, user_id, type, ingredient, ...)    │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 检查是否需要创建 cron 任务               │
│ - 如果已有统一检查任务，跳过             │
│ - 如果没有，创建一个统一检查任务         │
└─────────────────────────────────────────┘
     │
     ▼
返回: "✅ 已创建价格提醒！"
```

#### 查看提醒

```
用户: "查看我的提醒"
     │
     ▼
┌─────────────────────────────────────────┐
│ 查询 reminders 表                        │
│ SELECT * FROM reminders                 │
│ WHERE user_id = ? AND enabled = 1       │
└─────────────────────────────────────────┘
     │
     ▼
返回: "📋 你的提醒列表：..."
```

#### 删除提醒

```
用户: "删除豆粕价格提醒"
     │
     ▼
┌─────────────────────────────────────────┐
│ 查询匹配的提醒                           │
│ SELECT * FROM reminders                 │
│ WHERE user_id = ?                       │
│   AND ingredient LIKE '%豆粕%'          │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 确认删除                                 │
│ "要删除这个提醒吗？豆粕价格提醒 ($400)"  │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 执行删除                                 │
│ DELETE FROM reminders                   │
│ WHERE id = ? AND user_id = ?            │
└─────────────────────────────────────────┘
     │
     ▼
返回: "✅ 已删除"
```

#### 每日检查任务

```
cron 任务执行 (每日 08:00)
     │
     ▼
┌─────────────────────────────────────────┐
│ 查询所有启用的提醒                       │
│ SELECT * FROM reminders WHERE enabled=1 │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 获取最新价格数据                         │
│ SELECT * FROM ingredient_prices          │
│ WHERE price_date = CURRENT_DATE         │
└─────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ 检查每个提醒的条件                       │
│ - 用户 A: SBM $350, 阈值 $400 → 不触发  │
│ - 用户 B: SBM $350, 阈值 $380 → 不触发  │
│ - 用户 A: Fish meal $2100, 阈值 $2000   │
│   → 触发！发送通知给用户 A               │
└─────────────────────────────────────────┘
```

---

## 4. 数据库设计

### 4.1 reminders 表

```sql
CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('price', 'formula_cost')),
    
    -- 价格提醒字段
    ingredient TEXT,  -- 原料名称 (如 "Soybean meal, 48%")
    ingredient_code TEXT,  -- 原料代码 (如 "ING_SBM_48")
    
    -- 配方成本提醒字段
    formula TEXT,  -- 配方名称 (如 "Nursery Diet 1")
    formula_id TEXT,  -- 配方 ID
    
    -- 通用字段
    threshold REAL NOT NULL,  -- 阈值 (美元/吨)
    condition TEXT NOT NULL CHECK(condition IN ('above', 'below')),  -- 条件
    
    -- 状态
    enabled BOOLEAN DEFAULT 1,
    last_triggered_at TEXT,  -- 上次触发时间
    trigger_count INTEGER DEFAULT 0,  -- 触发次数
    
    -- 元数据
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_enabled ON reminders(enabled);
CREATE INDEX IF NOT EXISTS idx_reminders_type_ingredient ON reminders(type, ingredient_code);
CREATE INDEX IF NOT EXISTS idx_reminders_type_formula ON reminders(type, formula_id);
```

### 4.2 示例数据

```sql
-- 用户 123456 创建的提醒
INSERT INTO reminders (id, user_id, type, ingredient, ingredient_code, threshold, condition)
VALUES 
    ('rmd-001', '123456', 'price', 'Soybean meal, 48%', 'ING_SBM_48', 400, 'above'),
    ('rmd-002', '123456', 'price', 'Fish meal, 65%', 'ING_FISH_65', 2000, 'above'),
    ('rmd-003', '123456', 'formula_cost', 'Nursery Diet 1', 'FORMULA_NURSERY_1', 300, 'above');

-- 用户 789012 创建的提醒
INSERT INTO reminders (id, user_id, type, ingredient, ingredient_code, threshold, condition)
VALUES 
    ('rmd-004', '789012', 'price', 'Soybean meal, 48%', 'ING_SBM_48', 380, 'above'),
    ('rmd-005', '789012', 'price', 'DDGS, 28%', 'ING_DDGS_28', 200, 'below');
```

---

## 5. 技能设计

### 5.1 reminder_skill 结构

```
~/.openclaw/workspace-feedsales/skills/reminder_skill/
├── SKILL.md           # 技能说明
├── scripts/
│   ├── create_reminder.py    # 创建提醒
│   ├── list_reminders.py     # 查看提醒
│   ├── delete_reminder.py    # 删除提醒
│   └── check_reminders.py    # 检查提醒（cron 任务调用）
└── reference/
    └── ingredient_codes.json # 原料名称到代码的映射
```

### 5.2 SKILL.md 更新

```markdown
# Reminder Skill

让用户通过对话创建价格提醒和配方成本监控。

## 触发场景

- "提醒我当豆粕价格超过 400 美元"
- "设置价格提醒"
- "当保育料成本超过 300 美元时通知我"
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
3. 写入 reminders 表
4. 返回确认信息

### 2. 查看提醒

1. 从 inbound_meta 获取 user_id
2. 查询 reminders 表
3. 格式化返回

### 3. 删除提醒

1. 从 inbound_meta 获取 user_id
2. 查询匹配的提醒
3. 确认后删除

## 用户隔离

所有操作必须带 user_id 过滤：
- SELECT ... WHERE user_id = ?
- DELETE ... WHERE user_id = ?

## 原料名称映射

| 用户输入 | 标准名称 | 代码 |
|----------|----------|------|
| 豆粕 | Soybean meal, 48% | ING_SBM_48 |
| 玉米 | Corn, grain | ING_CORN |
| 鱼粉 | Fish meal, 65% | ING_FISH_65 |
| DDGS | DDGS, 28% | ING_DDGS_28 |
```

---

## 6. 配置修改

### 6.1 OpenClaw 配置

```json
// ~/.openclaw/openclaw.json
{
  "tools": {
    "profile": "coding",
    "alsoAllow": ["group:automation"]
  },
  "agents": {
    "list": [
      {
        "id": "feedsales",
        "name": "feedsales",
        "workspace": "/home/kenny/.openclaw/workspace-feedsales",
        "model": "astroncodingplan/astron-code-latest",
        "tools": {
          "profile": "coding",
          "allow": ["group:automation"]
        }
      }
    ]
  }
}
```

### 6.2 统一检查任务

创建一个 cron 任务，检查所有用户的提醒：

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
    "message": "Check all enabled reminders from the reminders table. For each reminder: 1) Get current price/formula cost from database, 2) Check if condition is met (above/below threshold), 3) If triggered, send notification to the user via Telegram. Use the user_id field to route notifications.",
    "thinking": "Query reminders table for all enabled reminders. For each reminder, query ingredient_prices or calculate formula cost. Compare to threshold. If condition met, send message to user_id via Telegram."
  },
  "delivery": {
    "mode": "none"
  }
}
```

---

## 7. 实现步骤

### Phase 1: 基础设施 (Day 1)

1. **修改 OpenClaw 配置**
   - 添加 `group:automation` 到 tools.allow
   - 重启 Gateway

2. **创建数据库表**
   - 执行 reminders 表创建 SQL
   - 创建索引

3. **创建原料名称映射**
   - 编写 `ingredient_codes.json`
   - 支持中英文映射

### Phase 2: 核心功能 (Day 2)

4. **创建提醒脚本**
   - `create_reminder.py`
   - `list_reminders.py`
   - `delete_reminder.py`

5. **更新 SKILL.md**
   - 完善工作流程
   - 添加用户隔离说明

### Phase 3: 自动化 (Day 3)

6. **创建检查脚本**
   - `check_reminders.py`
   - 支持批量检查和通知

7. **创建统一 cron 任务**
   - 每日执行检查
   - 发送通知给对应用户

### Phase 4: 测试与优化 (Day 4)

8. **功能测试**
   - 创建提醒
   - 查看提醒
   - 删除提醒
   - 自动检查

9. **用户隔离测试**
   - 多用户场景
   - 权限验证

---

## 8. 测试用例

### 8.1 创建提醒

| 测试 | 输入 | 预期输出 |
|------|------|----------|
| 价格提醒 | "提醒我当豆粕价格超过 400 美元" | ✅ 已创建价格提醒！ |
| 配方成本提醒 | "当保育料成本超过 300 美元时通知我" | ✅ 已创建成本提醒！ |
| 价格下跌提醒 | "玉米价格低于 80 美元时提醒我" | ✅ 已创建价格提醒！ |
| 无效输入 | "提醒我" | ❌ 请说明要监控什么 |

### 8.2 查看提醒

| 测试 | 用户 | 预期输出 |
|------|------|----------|
| 有提醒 | 用户 A (有 3 个提醒) | 📋 你的提醒列表：1. ... 2. ... 3. ... |
| 无提醒 | 用户 B (无提醒) | 📋 你还没有设置任何提醒 |

### 8.3 删除提醒

| 测试 | 输入 | 预期输出 |
|------|------|----------|
| 精确删除 | "删除豆粕价格提醒" | ✅ 已删除 "豆粕价格提醒 ($400)" |
| 模糊删除 | "删除所有提醒" | ⚠️ 确认删除 3 个提醒？ |
| 无匹配 | "删除玉米提醒" (用户无此提醒) | ❌ 未找到匹配的提醒 |

### 8.4 用户隔离

| 测试 | 操作 | 预期结果 |
|------|------|----------|
| 隔离查看 | 用户 A 查看提醒 | 只看到用户 A 的提醒 |
| 隔离删除 | 用户 A 删除用户 B 的提醒 ID | ❌ 无权限删除此提醒 |
| 隔离通知 | 用户 B 的提醒触发 | 只通知用户 B |

---

## 9. 风险与缓解

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 工具权限不足 | 🔴 高 | 修改配置添加 `group:automation` |
| 用户数据泄露 | 🔴 高 | 所有查询带 user_id 过滤；参数化查询防止 SQL 注入 |
| 任务过多 | 🟡 中 | 使用统一检查任务，避免每用户一个任务 |
| 数据库锁竞争 | 🟢 低 | SQLite 写入频率低；考虑未来迁移到 PostgreSQL |
| 原料名称歧义 | 🟡 中 | 使用映射表标准化；支持模糊匹配 |
| 通知失败 | 🟡 中 | 记录失败日志；支持重试机制 |

---

## 10. 未来扩展

### 10.1 短期 (1-2 周)

- [ ] 支持更多提醒类型（库存、汇率等）
- [ ] 支持自定义检查频率
- [ ] 支持提醒暂停/恢复

### 10.2 中期 (1-2 月)

- [ ] Web 界面管理提醒
- [ ] 提醒历史记录
- [ ] 多渠道通知（Email、飞书等）

### 10.3 长期 (3-6 月)

- [ ] AI 智能推荐提醒阈值
- [ ] 市场趋势预测
- [ ] 多用户协作提醒

---

## 11. 附录

### 11.1 原料名称映射表

```json
{
  "豆粕": {"name": "Soybean meal, 48%", "code": "ING_SBM_48"},
  "豆粕48": {"name": "Soybean meal, 48%", "code": "ING_SBM_48"},
  "soybean meal": {"name": "Soybean meal, 48%", "code": "ING_SBM_48"},
  "玉米": {"name": "Corn, grain", "code": "ING_CORN"},
  "corn": {"name": "Corn, grain", "code": "ING_CORN"},
  "鱼粉": {"name": "Fish meal, 65%", "code": "ING_FISH_65"},
  "fish meal": {"name": "Fish meal, 65%", "code": "ING_FISH_65"},
  "DDGS": {"name": "DDGS, 28%", "code": "ING_DDGS_28"},
  "ddgs": {"name": "DDGS, 28%", "code": "ING_DDGS_28"}
}
```

### 11.2 配方名称映射表

```json
{
  "保育料": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
  "保育料1": {"name": "Nursery Diet 1", "id": "FORMULA_NURSERY_1"},
  "育肥料": {"name": "Finishing Diet", "id": "FORMULA_FINISHING"},
  "肉鸡料": {"name": "Broiler Starter", "id": "FORMULA_BROILER_STARTER"}
}
```

---

**文档结束**
