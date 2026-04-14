# FeedSales AI — v1.7 设计文档修改审查报告

**Date**: 2026-04-14
**Reviewer**: AI Assistant
**Document**: V1_7_SYSTEM_DESIGN_HARNESS_BASED.md (commit 607da8e)
**Change Scope**: 补充 ingredient_code 到 v1.7 设计文档
**Baseline**: ARCHITECTURE_v1.6.md + schema.sql (实际实现)

---

## 执行摘要

**结论**: ⚠️ Needs Work (2 个 P2 问题)

本次修改的核心目标——将 `ingredient_code` 补充到 v1.7 设计文档——已正确完成。ingredient_code 的设计理由、正交性说明、查询策略更新均准确。但发现 2 个遗留不一致问题需要修复。

---

## 分维度评估

### 1. 契约一致性 ⚠️ PARTIAL

| 检查项 | v1.6 实现 | v1.7 设计 | 状态 |
|--------|----------|----------|------|
| ingredient_prices.ingredient_code | ✅ NOT NULL | ✅ NOT NULL | ✅ |
| formula_ingredients.ingredient_code | ✅ NOT NULL | ✅ 提及（注释） | ⚠️ |
| ingredient_prices.UNIQUE | (code, date, owner) | (code, date, owner) | ✅ |
| ingredient_prices.currency | USD | ❌ 未指定 | ⚠️ |
| ingredient_prices.version | ✅ 有（乐观锁） | ❌ 未包含 | ⚠️ |
| ingredient_prices.updated_at | ✅ 有 | ❌ 未包含 | ⚠️ |
| PriceService.get_price 参数 | ingredient_code | ingredient_code | ✅ |
| PriceService.batch_get_prices | ✅ 有 | ✅ 有 | ✅ |
| price_sources 键 | ingredient_code | ingredient_code | ✅ |

### 2. 文档质量 ✅ PASS

| 检查项 | 状态 | 说明 |
|--------|------|------|
| ingredient_code 必要性阐述 | ✅ | 多数据源命名差异 + 精确匹配理由清晰 |
| 正交性说明 | ✅ | owner_open_id vs ingredient_code 互补关系明确 |
| 查询策略更新 | ✅ | LIKE → IN(ingredient_code) 逻辑正确 |
| Service 签名更新 | ✅ | PriceService/CalculationService 参数已更新 |

### 3. 设计完整性 ⚠️ PARTIAL

| 检查项 | 状态 | 说明 |
|--------|------|------|
| ingredient_prices DDL | ⚠️ | 缺少 currency, version, updated_at 字段 |
| formula_ingredients DDL | ⚠️ | 仅有注释，无完整 DDL |
| 批量查询方法 | ✅ | batch_get_prices 已添加 |
| _generate_ingredient_code | ❌ | v1.6 有此方法，v1.7 未提及 |

### 4. 跨文档一致性 ⚠️ PARTIAL

| 对比项 | ARCHITECTURE_v1.6 | V1_7 设计 | 状态 |
|--------|-------------------|----------|------|
| ingredient_prices 字段 | 10 列（含 currency, version, updated_at） | 7 列 | ❌ |
| formula_ingredients DDL | 完整 CREATE TABLE | 仅注释 | ❌ |
| _generate_ingredient_code | ✅ 有完整实现 | ❌ 未提及 | ⚠️ |
| 默认货币 | USD | 未指定 | ❌ |

### 5. 需求不变性 ✅ PASS

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 未新增需求 | ✅ | 仅补充已有实现的设计说明 |
| 未删除需求 | ✅ | 所有 v1.7 原有功能保留 |
| 未改变业务逻辑 | ✅ | 查询策略从 name→code 是对齐实现，非新需求 |

---

## 问题清单

### P2-1: ingredient_prices DDL 与实际 schema.sql 不一致

**问题描述**:
v1.7 设计文档中 `ingredient_prices` DDL 缺少 3 个字段：

| 字段 | schema.sql | v1.7 DDL | 差异 |
|------|-----------|---------|------|
| currency | `TEXT DEFAULT 'USD'` | ❌ 缺失 | 北美市场统一 USD |
| version | `INTEGER DEFAULT 1` | ❌ 缺失 | 乐观锁所需 |
| updated_at | `DATETIME DEFAULT CURRENT_TIMESTAMP` | ❌ 缺失 | 审计追踪 |

**影响**: 开发者按 v1.7 DDL 建表会缺少乐观锁和审计字段。

**修复建议**: 补全 ingredient_prices DDL，与 schema.sql 对齐。

---

### P2-2: formula_ingredients 缺少完整 DDL

**问题描述**:
v1.7 设计文档中 `formula_ingredients` 仅有两行注释：
```sql
-- formula_ingredients 属于 formulas，ingredient_code 用于关联价格查询
-- ingredient_code 无 FK 约束，由应用层保证引用有效性
```

而 schema.sql 有完整 DDL：
```sql
CREATE TABLE IF NOT EXISTS formula_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    formula_id INTEGER NOT NULL,
    ingredient_name TEXT NOT NULL,
    ingredient_code TEXT NOT NULL,
    ratio_percent REAL NOT NULL CHECK(ratio_percent >= 0 AND ratio_percent <= 100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (formula_id) REFERENCES formulas(id) ON DELETE CASCADE
);
```

**影响**: 开发者无法从 v1.7 文档获得完整建表语句。

**修复建议**: 用完整 DDL 替换注释。

---

## 修改亮点 ✅

1. **正交性说明精准** — owner_open_id（用户间隔离）vs ingredient_code（同用户多数据源精确查找），逻辑清晰
2. **查询策略更新完整** — 从 LIKE 模糊匹配到 IN(ingredient_code) 精确匹配，Service 签名同步更新
3. **price_sources 键改用 ingredient_code** — 确保跨数据源一致性
4. **Phase 1 新增确认项** — 标注 ingredient_code 已在 v1.6 完成，避免重复工作
5. **需求零变更** — 纯补充，未改变任何业务需求

---

## 修复建议

| 问题 | 优先级 | 修复量 | 说明 |
|------|--------|--------|------|
| ingredient_prices DDL 补全 | P2 | 3 行 | 添加 currency, version, updated_at |
| formula_ingredients DDL 补全 | P2 | 8 行 | 用完整 CREATE TABLE 替换注释 |

---

**审查日期**: 2026-04-14
**审查者**: AI Assistant
**结论**: ⚠️ Needs Work — 2 个 P2 问题，修复量小，可快速完成
