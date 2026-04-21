# FeedSales AI MVP — 代码审查与测试报告

**审查日期：** 2026-04-14  
**审查人：** Hermes Agent  
**版本：** v1.7 (Harness-Based Design)  
**仓库：** https://gitee.com/kenny-chenym/feed-sales-ai-mvp

---

## 1. 执行摘要

| 项目 | 状态 |
|------|------|
| 架构设计 | ✅ 优秀 |
| 代码质量 | ⚠️ 良好（有 P0 bug） |
| E2E 测试通过率 | 76.1%（需修复） |
| 多租户隔离 | ✅ 已实现 |
| 测试覆盖 | ⚠️ 需完善 |

**关键发现：** 架构遵循 Harness 理念，分层清晰，但存在价格查询使用 `ingredient_name` 而非 `ingredient_code` 的 P0 bug，导致价格查询大面积失败。

---

## 2. 测试结果汇总

### 2.1 E2E 综合测试 (test_e2e_comprehensive.py)

```
Total:   113
Passed:  86 ✅
Failed:  27 ❌
Rate:    76.1%
Status:  NEEDS_FIX ⚠️
```

**失败分布：**
- 价格查询失败：20 项 — `ingredient_name` vs `ingredient_code` 映射问题
- 私有配方查询失败：1 项
- 消息提取失败：1 项
- E2E 工作流价格步骤失败：3 项

### 2.2 E2E Full 测试 (test_e2e_full.py)

```
Total:   18
Passed:  18 ✅
Failed:  0 ❌
Rate:    100.0%
```

### 2.3 CalculationService 测试 (test_calculation_service.py)

```
Total:   5
Passed:  5 ✅
Failed:  0 ❌
Rate:    100.0%
```

### 2.4 Telegram E2E 测试

需要真实 Telegram Bot Token，跳过。

---

## 3. 代码审查详情

### 3.1 ✅ 架构亮点

**1. 清晰的分层架构**
```
Harness Runtime (Task Router, Session State, Result Validator)
    ↓
Service Layer (Formula, Price, Customer, Calculation)
    ↓
Repository Layer (多租户隔离)
    ↓
Database (SQLite WAL)
```

**2. 多租户隔离设计**
- 所有核心表都有 `owner_open_id` 字段
- Repository 层强制 `WHERE owner_open_id = ?` 过滤
- 私有数据优先 + 公共数据回退策略

**3. ingredient_code 标准化**
- 用 `ING_CORN`、`ING_SBM` 等代码替代模糊名称匹配
- 解决不同数据源命名不一致问题
- 支持精确 `IN` 批量查询

**4. Harness 组件完整**
- TaskRouter: 8 种任务类型，分类清晰
- SessionStateManager: 支持连续对话上下文
- ResultValidator: 返回前结构化校验
- AuditLogger: 关键操作审计

### 3.2 ⚠️ 发现的问题

#### P0 — 价格查询使用 ingredient_name 而非 ingredient_code

**位置：** `src/harness/harness.py` 第 223-241 行

**问题代码：**
```python
# ingredient_map 将中文映射到英文名称
ingredient_map = {
    '玉米': 'Corn, grain',
    '豆粕': 'Soybean meal, 48%',
    ...
}

# 但 PriceRepository.get_latest_price() 用的是 ingredient_code:
# WHERE owner_open_id = ? AND ingredient_code = ?
```

**影响：** 20 项价格查询全部失败，包括核心原料（玉米、豆粕、鱼粉等）

**根因：** `PriceService.get_price()` 和 `PriceRepository.get_latest_price()` 使用 `ingredient_code` 字段查询，但 `harness.py` 传入的是 `ingredient_name` 字符串。

**修复建议：**
```python
# 方案 1: 在 harness.py 中将 ingredient_map 改为 ingredient_code
ingredient_map = {
    '玉米': 'ING_CORN',
    '豆粕': 'ING_SBM',
    ...
}

# 方案 2: 在 PriceService 中增加按 name 查询的 fallback
def get_price(self, user_id: str, identifier: str) -> ServiceResult:
    # 尝试 ingredient_code
    result = self.price_repo.get_latest_price(user_id, identifier)
    if result:
        return ServiceResult(success=True, data=result, source='...')
    
    # fallback: 按 name 查找
    result = self._get_by_name(user_id, identifier)
```

---

#### P1 — 硬编码的中文 ingredient_map

**位置：** `src/harness/harness.py` 第 223-228 行

**问题代码：**
```python
ingredient_map = {
    '玉米': 'Corn, grain',
    '豆粕': 'Soybean meal, 48%',
    'corn': 'Corn, grain',
    'soybean': 'Soybean meal, 48%',
}
```

**建议：** 使用 `src/utils/ingredient_codes.py` 中的标准化映射表。

---

#### P1 — AuditLogger 写数据库失败无重试

**位置：** `src/harness/harness.py` 第 64 行

**问题代码：**
```python
except Exception as e:
    logger.warning(f"Failed to write audit log to DB: {e}")
```

**问题：** 审计日志写入失败时只记录 warning，日志永久丢失。

**建议：** 添加重试队列或降级方案，确保审计日志不丢失。

---

#### P2 — ServiceResult.source 属性需验证

**位置：** `src/harness/harness.py` 第 251 行

**问题代码：**
```python
result = self.price_service.get_price(user_id, ingredient)
return {
    ...
    'source': result.source  # ServiceResult 是否有 source 属性？
}
```

**建议：** 确认 `ServiceResult` 类定义中 `source` 属性的来源（private/public/default）。

---

### 3.3 📊 代码质量指标

| 指标 | 数值 |
|------|------|
| src/ 代码行数 | 3,327 行 |
| 测试文件数 | 28 个 |
| Harness 组件 | 4 个 (TaskRouter, SessionState, ResultValidator, AuditLogger) |
| Service 类 | 5 个 (Formula, Price, Customer, Calculation, Reminder) |
| Repository 类 | 3 个 |

---

## 4. 修复优先级

| 优先级 | 问题 | 预计工时 |
|--------|------|----------|
| P0 | 价格查询用 name 而非 code | 1-2h |
| P1 | 硬编码中文映射 | 0.5h |
| P1 | AuditLogger 无重试 | 1h |
| P2 | ServiceResult.source 验证 | 0.5h |

---

## 5. 结论

**架构：优秀** — v1.7 Harness 理念清晰，分层合理，多租户隔离考虑周全，代码组织良好。

**代码质量：良好** — 结构清晰，注释完善，但存在一个关键的 P0 bug（价格查询失败率 100%），需要优先修复。

**建议行动：**
1. 立即修复 `ingredient_name` vs `ingredient_code` 问题
2. 重新运行 E2E 测试验证
3. 补充 price lookup 的单元测试覆盖

---

*报告生成：Hermes Agent @ 2026-04-14*
