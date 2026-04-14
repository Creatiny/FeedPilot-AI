# FeedSales AI — Design Review Report
**Date**: 2026-04-14
**Reviewer**: AI Assistant
**Document**: ARCHITECTURE_v1.6.md
**Status**: Needs Work

---

## 执行摘要

**结论**: ⚠️ Needs Work

经过 5 维度审查，发现 2 个 P1 问题、1 个 P2 问题。主要问题是多租户隔离失败（private price/formula 读写异常）和架构文档与实际 Schema 不同步。核心的 `ingredient_code` 迁移已完成，设计文档已更新。

---

## 分维度评估

### 1. 契约一致性 ✅ PASS

| 检查项 | 状态 | 说明 |
|--------|------|------|
| ingredient_code 列定义 | ✅ | formula_ingredients 表已添加 ingredient_code (NOT NULL) |
| PriceService 精确匹配 | ✅ | batch_get_* 使用 IN(ingredient_code) 替代 LIKE |
| CalculationService | ✅ | 使用 ingredient_code 做批量价格查询 |
| Repository 返回 ingredient_code | ✅ | get_formula/get_formula_by_id 返回 ingredient_code |
| FK 约束 | ✅ | ingredient_code 无 FK（应用层保证引用有效性，正确决策） |

### 2. 文档质量 ⚠️ PARTIAL

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 链接定位 | ✅ | 文档内链接和文件路径正确 |
| 术语一致性 | ✅ | 术语使用统一 |
| 代码示例同步 | ❌ | FormulaRepository.get_formula() SQL 示例未更新（仍无 ingredient_code） |

### 3. 设计完整性 ✅ PASS

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 价格获取流程 | ✅ | PriceService → CalculationService 链路正确 |
| 配方成本计算 | ✅ | 批量查询 + 默认价格 fallback |
| 多租户隔离 | ❌ | 4 个测试失败（private price/formula） |
| 错误处理 | ✅ | ServiceResult 统一返回格式 |

### 4. 跨文档一致性 ❌ FAIL

| 检查项 | 文档定义 | 实际 Schema | 状态 |
|--------|----------|-------------|------|
| formulas 表列 | owner_open_id, name, stage_type, notes | + animal_type, weight_range, version | ❌ |
| formula_ingredients SQL 示例 | 无 ingredient_code | 有 ingredient_code | ❌ |

### 5. 实现就绪度 ⚠️ PARTIAL

| 检查项 | 状态 | 说明 |
|--------|------|------|
| ingredient_code 迁移 | ✅ | 988 行数据已迁移 |
| 计算服务 | ✅ | 精确匹配，消除 LIKE 误匹配 |
| 多租户隔离 | ❌ | private 数据读写失败 |
| 测试覆盖 | ⚠️ | 70/74 通过，4 个多租户隔离失败 |

---

## 问题清单

### P1 — 上线前必须修复

#### P1-1: 多租户隔离失败（4 个测试）

**问题描述**: 
- `Private price priority` — 私有价格查询返回公共价格
- `List private prices` — 私有价格列表为空
- `Get private formula` — 私有配方创建后无法获取
- `Extract formula from message` — NLP 提取失败

**根因分析**:
`owner_open_id` 过滤逻辑在 Service 层可能未正确实现，导致私有数据被公共数据覆盖或查询时使用了错误的 owner。

**影响**: 用户私有价格/配方数据无法正常使用，核心功能失效。

**修复建议**:
1. 检查 `PriceService.get_private_price()` 是否正确传递 `owner_open_id`
2. 检查 `FormulaService.get_formula()` 的私有优先查询逻辑
3. 验证 `owner_open_id` 在数据库层是否正确存储

**验证方法**: 
```bash
cd /home/kenny/.openclaw/workspace-feedsales && \
PYTHONPATH=. uv run pytest tests/test_e2e_comprehensive.py -v -k "private"
```

---

#### P1-2: 架构文档 formulas 表定义不完整

**问题描述**:
ARCHITECTURE_v1.6.md 中 `formulas` 表定义为:
```sql
CREATE TABLE formulas (
    id, owner_open_id, name, stage_type, notes, ...
)
```

但实际 Schema.sql 包含额外列:
```sql
CREATE TABLE formulas (
    id, owner_open_id, name, 
    animal_type,        -- 缺失
    stage_type, notes, 
    weight_range,       -- 缺失
    version, ...        -- 缺失
)
```

**影响**: 开发者参考文档会创建错误的表结构。

**修复建议**: 更新 ARCHITECTURE_v1.6.md 中 formulas 表定义为完整版本。

---

### P2 — 重要但非阻断

#### P2-1: FormulaRepository.get_formula() SQL 示例未更新

**问题描述**:
架构文档中 `FormulaRepository.get_formula()` 的 SQL 查询:
```sql
SELECT f.id, f.name, f.stage_type, f.notes,
       fi.ingredient_name, fi.ratio_percent
```

实际代码已更新为:
```sql
SELECT f.id, f.name, f.stage_type, f.notes,
       fi.ingredient_name, fi.ingredient_code, fi.ratio_percent
```

**修复建议**: 更新文档中的 SQL 示例以匹配实际实现。

---

## 修复进度

### ✅ 已完成

| 问题 | 状态 | 提交 |
|------|------|------|
| ingredient_code 缺失 | ✅ 已修复 | 323d23c |
| FK 约束设计错误 | ✅ 已移除 FK | f5cd734 |
| LIKE 误匹配 | ✅ 改为精确 IN 查询 | 323d23c |
| Repository 迁移 | ✅ 988 行数据完成 | 323d23c |

### ⚠️ 待修复

| 问题 | 优先级 | 预计工时 |
|------|--------|----------|
| 多租户隔离失败 | P1 | 2-3h |
| 文档 formulas 定义 | P1 | 15min |
| SQL 示例更新 | P2 | 10min |

---

## 设计亮点 ✅

1. **ingredient_code 迁移方案正确** — 应用层保证引用有效性，不依赖 DB 层 FK（SQLite FK 限制）
2. **批量查询优化** — `batch_get_prices` 避免 N+1 查询问题
3. **默认价格 fallback** — 价格缺失时不会导致计算失败
4. **ServiceResult 统一返回** — 错误处理一致

---

## 结论

**工程就绪状态**: ⚠️ Needs Work — 核心迁移完成，但多租户隔离缺陷阻断生产部署。

**下一步**:
1. 修复多租户隔离问题（P1）
2. 同步架构文档与实际 Schema（P1）
3. 重新运行完整测试套件验证

---

**审查日期**: 2026-04-14  
**审查者**: AI Assistant  
**下次审查**: P1 问题修复后
