# FeedSales AI v1.7 独立代码审查报告

**审查时间**: 2026-03-29  
**审查人**: OpenClaw Reviewer  
**审查版本**: v1.7 (commit f5b18b3..2481bbb)  
**变更范围**: 34 文件，+5966/-1448 行

---

## 1. 执行摘要

### 审查结论
**⚠️ 有条件通过 (Conditional Pass)**

v1.7 实现了设计文档中的核心 Harness 架构，包括 Task Router、Session State Manager、Result Validator 和 Service Layer。多租户隔离机制基本正确，错误处理框架已建立。

**但存在以下关键问题需修复**：
1. **P0-01**: Schema 缺少 version 字段（乐观锁未实现）
2. **P0-02**: CustomerService/NutritionAnalysisSkill 仍使用 Repository 而非 Service
3. **P0-03**: Harness 层缺少日志审计实现
4. **P1-01**: 技能改造不彻底（FormulaCostSkill 保留 legacy 代码）

---

## 2. 架构一致性评估

### 2.1 Harness Runtime Layer ✓

| 组件 | 设计符合度 | 审查意见 |
|------|-----------|---------|
| **TaskRouter** | ✅ 95% | 正则模式完整，优先级设计正确，编译优化良好 |
| **SessionStateManager** | ✅ 90% | 内存存储 + TTL 机制正确，但缺少数据库持久化扩展点 |
| **ResultValidator** | ✅ 95% | 校验规则完整（成本、配方、客户、价格），误差容限合理 |
| **FeedSalesHarness** | ⚠️ 85% | 整合正确，但部分任务处理逻辑过于简化（quote_generate、nutrition_analysis） |

**亮点**：
- TaskRouter 预编译正则表达式（性能优化）
- SessionState 使用 dataclass（类型安全）
- ResultValidator 分离校验逻辑（单一职责）

**改进建议**：
- Harness.process() 缺少审计日志调用
- quote_generate 和 nutrition_analysis 仅返回占位消息

### 2.2 Service Layer ✓

| Service | 设计符合度 | 审查意见 |
|---------|-----------|---------|
| **FormulaService** | ✅ 95% | 私有优先查询正确，乐观锁实现完整，错误码规范 |
| **PriceService** | ✅ 90% | UPSERT 逻辑正确，但缺少 version 字段支持 |
| **CustomerService** | ⚠️ 80% | CRUD 完整，但 update 缺少乐观锁检查 |
| **CalculationService** | ✅ 95% | 成本计算逻辑正确，价格来源追踪完整 |

**亮点**：
- ServiceResult 统一返回结构（包含 error_code、source）
- 私有优先查询策略正确实现
- 参数化查询防止 SQL 注入

**改进建议**：
- CustomerService.update_customer() 应添加 version 检查
- PriceService 应支持乐观锁（设计文档要求）

### 2.3 Repository Layer ✓

| Repository | 设计符合度 | 审查意见 |
|-----------|-----------|---------|
| **FormulaRepository** | ✅ 95% | 输入验证完整，owner_open_id 强制隔离 |
| **PriceRepository** | ✅ 90% | 参数化查询正确 |
| **CustomerRepository** | ✅ 90% | CRUD 完整，隔离正确 |

**亮点**：
- validate_owner_open_id() 函数（输入验证）
- 所有 SQL 使用 `?` 占位符（无字符串拼接）

---

## 3. 设计合规性审查

### 3.1 错误处理（E001-E006）

| 错误码 | 定义位置 | 实现情况 | 审查意见 |
|-------|---------|---------|---------|
| E001 | FormulaService, PriceService, CustomerService | ✅ 已实现 | 参数错误处理完整 |
| E002 | 所有 Service | ✅ 已实现 | 数据不存在错误统一 |
| E003 | FormulaService, CustomerService | ✅ 已实现 | 权限错误检查正确 |
| E004 | FormulaService, CustomerService | ✅ 已实现 | 业务错误（重复数据） |
| E005 | FormulaService | ✅ 已实现 | 系统错误捕获 |
| E006 | FormulaService | ✅ 已实现 | 乐观锁冲突（仅 FormulaService） |

**问题**：
- ⚠️ CustomerService 和 PriceService 缺少 E006（乐观锁）支持
- ⚠️ CalculationService 未定义错误码（直接传递 FormulaService 的错误）

### 3.2 乐观锁（version 字段）

**设计要求**：formulas、customers、ingredient_prices 表均需添加 version 字段

**实现状态**：
| 表 | Schema | FormulaService | CustomerService | PriceService |
|---|--------|----------------|-----------------|--------------|
| formulas | ❌ 缺失 | ✅ 已实现 | N/A | N/A |
| customers | ❌ 缺失 | N/A | ❌ 未实现 | N/A |
| ingredient_prices | ❌ 缺失 | N/A | N/A | ❌ 未实现 |

**P0 问题**：
1. `schema.sql` 未添加 version 字段到任何表
2. FormulaService 的 update_formula() 使用 version 检查，但数据库不支持
3. CustomerService 和 PriceService 完全未实现乐观锁

**修复建议**：
```sql
-- 必须添加到 schema.sql
ALTER TABLE formulas ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE customers ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE ingredient_prices ADD COLUMN version INTEGER DEFAULT 1;
```

### 3.3 日志审计

**设计要求**：
- JSON 格式日志
- 包含 user_id, session_id, action, duration_ms
- 敏感操作审计（log_sensitive_access）

**实现状态**：
- ✅ 所有文件导入 logging 模块
- ✅ 关键操作有 logger.info/error 调用
- ❌ 缺少结构化 JSON 日志格式
- ❌ 缺少审计日志专用接口
- ❌ Harness.process() 未记录操作日志

**问题**：
- 日志格式不统一（部分使用 f-string，部分使用 format）
- 未实现 AuditLogger 类（设计文档 6.4 节要求）

---

## 4. 代码质量评估

### 4.1 命名规范

| 文件 | 评分 | 问题 |
|------|------|------|
| harness.py | ✅ 9/10 | 方法命名清晰，但 `_execute_task` 过长 |
| task_router.py | ✅ 10/10 | 常量大写，私有方法下划线前缀 |
| session_state.py | ✅ 10/10 | dataclass 字段命名规范 |
| result_validator.py | ✅ 10/10 | 方法命名一致 |
| formula_service.py | ✅ 9/10 | ServiceResult 重复定义（应集中） |
| price_service.py | ⚠️ 8/10 | `_get_price_by_owner` 私有方法正确，但 ServiceResult 重复 |
| customer_service.py | ⚠️ 8/10 | 同上 |
| calculation_service.py | ⚠️ 8/10 | 同上 |
| constants.py | ✅ 10/10 | 常量集中管理，工具函数命名清晰 |

**问题**：
- ServiceResult 在 4 个 Service 文件中重复定义（应提取到 `src/services/__init__.py`）
- FormulaCostSkill 中 `_execute_legacy` 方法保留 legacy 代码（应移除）

### 4.2 函数职责

| 文件 | 评分 | 问题 |
|------|------|------|
| harness.py | ⚠️ 7/10 | `_handle_*` 方法包含正则提取逻辑（应分离） |
| formula_service.py | ✅ 9/10 | 单一职责，但 update_formula 过长（60 行） |
| price_service.py | ✅ 9/10 | 职责清晰 |
| customer_service.py | ✅ 9/10 | 职责清晰 |
| calculation_service.py | ✅ 10/10 | 职责单一 |

**改进建议**：
- Harness 层的配方名/原料名提取逻辑应提取到独立工具类
- FormulaService.update_formula() 应拆分（版本检查、更新逻辑、成分更新）

### 4.3 DRY 原则

**重复代码**：
1. **ServiceResult 定义**：在 4 个 Service 文件中重复（约 40 行代码）
2. **ingredient_map**：在 harness.py、price_lookup_skill.py、constants.py 中重复
3. **默认价格字典**：在 calculation_service.py、constants.py、formula_cost_skill.py 中重复

**修复建议**：
```python
# src/services/__init__.py
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class ServiceResult:
    success: bool
    data: Optional[Dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    source: Optional[str] = None
```

---

## 5. 多租户隔离审查

### 5.1 owner_open_id 隔离

| 层级 | 隔离实现 | 审查意见 |
|------|---------|---------|
| **Harness** | ✅ 正确 | process() 接收 user_id，传递给 Service |
| **Service** | ✅ 正确 | 所有查询强制传入 user_id |
| **Repository** | ✅ 正确 | WHERE 条件包含 owner_open_id |
| **Schema** | ✅ 正确 | 所有核心表包含 owner_open_id |

**验证**：
- FormulaService.get_formula(): 先查私有，再查公共
- PriceService.get_price(): 先查私有，再查公共
- CustomerService.list_customers(): WHERE owner_open_id = ?

**亮点**：
- 公共数据使用 `'system_public'` 标识（设计一致）
- 不允许删除公共配方（FormulaService.delete_formula 检查）

### 5.2 私有优先查询策略

| Service | 实现 | 测试覆盖 |
|---------|------|---------|
| FormulaService | ✅ 正确 | 未提供测试 |
| PriceService | ✅ 正确 | 未提供测试 |
| CalculationService | ✅ 正确 | 未提供测试 |

**代码示例**（FormulaService.get_formula）：
```python
# 1. 先查私有配方
formula = self.repo.get_formula(user_id, name)
if formula:
    return ServiceResult(success=True, data=formula, source='private')

# 2. 再查公共配方
formula = self.repo.get_formula('system_public', name)
if formula:
    return ServiceResult(success=True, data=formula, source='public')
```

**审查意见**：实现正确，但缺少单元测试验证回退逻辑。

---

## 6. 安全审查

### 6.1 SQL 注入防护

**审查结果**：✅ 通过

所有 SQL 语句使用参数化查询：
```python
# ✅ 正确
cursor.execute(
    "SELECT * FROM formulas WHERE owner_open_id = ? AND name = ?",
    (user_id, formula_name)
)

# ❌ 未发现字符串拼接
```

**验证文件**：
- src/database/repository.py: 100% 参数化
- src/services/*.py: 100% 参数化

### 6.2 输入验证

| 验证点 | 实现位置 | 审查意见 |
|-------|---------|---------|
| owner_open_id | repository.validate_owner_open_id() | ✅ 长度检查（<100） |
| formula_name | repository.validate_formula_name() | ✅ 长度检查（<200） |
| price > 0 | PriceService.set_private_price() | ✅ 业务验证 |
| customer name | CustomerService.create_customer() | ✅ 必填检查 |

**改进建议**：
- 缺少对特殊字符的过滤（如 SQL 通配符 `%`、`_`）
- 缺少对 ingredient_name 的白名单验证

### 6.3 权限检查

| 操作 | 权限检查 | 审查意见 |
|------|---------|---------|
| 更新配方 | ✅ WHERE id = ? AND owner_open_id = ? | 正确 |
| 删除配方 | ✅ 显式检查 owner_open_id | 正确 |
| 删除客户 | ✅ 显式检查 owner_open_id | 正确 |
| 删除公共配方 | ✅ 显式拒绝 | 正确 |

---

## 7. 性能风险

### 7.1 N+1 查询

**发现问题**：

1. **CalculationService.calculate_cost()**：
   ```python
   for ingredient in formula.get('ingredients', []):
       price_result = self.price_service.get_price(user_id, name)
   ```
   - 每个成分查询一次价格（N+1 问题）
   - 10 个成分 = 11 次查询（1 次配方 + 10 次价格）

**修复建议**：
```python
# 批量查询价格
def calculate_cost(self, user_id: str, formula_name: str):
    formula = self.formula_service.get_formula(user_id, formula_name)
    ingredient_names = [ing['name'] for ing in formula['ingredients']]
    prices = self.price_service.get_prices_batch(user_id, ingredient_names)
    # ...
```

2. **FormulaService.list_formulas()**：
   - 分别查询私有和公共配方（2 次查询）
   - 然后在 Python 中合并和去重
   - 应改为单 SQL 查询

### 7.2 内存泄漏风险

**SessionStateManager**：
```python
self.sessions: Dict[str, SessionState] = {}
```

**风险**：
- 内存字典无限增长
- cleanup_expired() 需要定期调用（但未集成到 Harness）

**修复建议**：
- 在 Harness 中集成定时清理（如每 10 分钟）
- 或使用 LRU 缓存限制最大会话数

### 7.3 并发问题

**发现问题**：
- Harness 是单例，SessionStateManager 是内存存储
- 多用户并发访问时，sessions 字典可能竞争

**修复建议**：
- 添加线程锁（threading.Lock）
- 或使用线程安全的 collections.OrderedDict

---

## 8. 回归风险

### 8.1 v1.6 技能改造

| 技能 | 改造状态 | 回归风险 |
|------|---------|---------|
| **FormulaCostSkill** | ⚠️ 部分改造 | 保留 legacy 代码（_execute_legacy），可能误用 |
| **PriceLookupSkill** | ✅ 改造完成 | 支持 Service 注入，向后兼容 |
| **CustomerRecordSkill** | ⚠️ 未改造 | 仍使用 customer_repo，未注入 CustomerService |
| **NutritionAnalysisSkill** | ⚠️ 未改造 | 仍使用 formula_repo，未注入 FormulaService |

**P0 问题**：
- CustomerRecordSkill 和 NutritionAnalysisSkill 未使用 Service 层
- 违反设计文档"技能改造走 Harness 接口"原则

### 8.2 向后兼容性

**FormulaCostSkill**：
```python
def __init__(self, db_path: str = "data/feed_sales.db", calc_service=None):
    self.calc_service = calc_service  # 可选注入

def execute(self, user_id: str, message: str):
    if self.calc_service:
        return self._execute_with_service(user_id, formula_name)
    return self._execute_legacy(user_id, formula_name)  # 向后兼容
```

**审查意见**：
- ✅ 支持渐进式迁移（可先部署 Service，再切换技能）
- ⚠️ legacy 代码应标记为 `@deprecated` 并在 v1.8 移除

---

## 9. 测试质量

### 9.1 测试覆盖

**问题**：本次审查范围内**未发现测试文件**

根据设计文档，以下测试必须提供：
- [ ] tests/test_formula_service.py
- [ ] tests/test_price_service.py
- [ ] tests/test_customer_service.py
- [ ] tests/test_calculation_service.py
- [ ] tests/test_task_router.py
- [ ] tests/test_session_state.py
- [ ] tests/test_result_validator.py
- [ ] tests/test_multi_tenant_v17.py

**风险**：
- 无单元测试验证 Service 逻辑
- 无集成测试验证 Harness 流程
- 无多租户隔离测试

### 9.2 测试建议

**优先级 P0**：
```python
# test_formula_service.py
def test_get_formula_private_first():
    """验证私有优先查询"""
    service = FormulaService(db_pool)
    # 创建私有配方
    # 创建公共配方（同名）
    # 查询应返回私有配方
    
def test_update_formula_optimistic_lock():
    """验证乐观锁"""
    # 更新配方时传入错误 version
    # 应返回 E006 错误
```

---

## 10. 问题清单

### P0 级别（必须修复）

| 编号 | 问题 | 影响 | 修复建议 | 预计工时 |
|------|------|------|---------|---------|
| **P0-01** | Schema 缺少 version 字段 | 高 | 乐观锁无法工作 | 30 分钟 |
| **P0-02** | CustomerService 缺少乐观锁 | 中 | 并发修改无保护 | 1 小时 |
| **P0-03** | PriceService 缺少乐观锁 | 中 | 并发修改无保护 | 1 小时 |
| **P0-04** | CustomerRecordSkill 未注入 Service | 中 | 违反架构规范 | 2 小时 |
| **P0-05** | NutritionAnalysisSkill 未注入 Service | 中 | 违反架构规范 | 2 小时 |
| **P0-06** | Harness 缺少审计日志 | 中 | 无法追踪操作 | 2 小时 |
| **P0-07** | CalculationService N+1 查询 | 中 | 性能问题 | 2 小时 |

### P1 级别（建议修复）

| 编号 | 问题 | 影响 | 修复建议 |
|------|------|------|---------|
| **P1-01** | ServiceResult 重复定义 | 低 | 提取到 services/__init__.py |
| **P1-02** | ingredient_map 重复 | 低 | 使用 constants.py 统一映射 |
| **P1-03** | Harness._handle_* 方法过长 | 低 | 提取正则逻辑到工具类 |
| **P1-04** | SessionStateManager 无线程安全 | 中 | 添加 threading.Lock |
| **P1-05** | 缺少输入特殊字符过滤 | 中 | 添加白名单验证 |
| **P1-06** | FormulaCostSkill legacy 代码 | 低 | 标记 @deprecated |

---

## 11. 评分

### 11.1 维度评分

| 维度 | 评分 | 说明 |
|------|------|------|
| **架构一致性** | 8.5/10 | Harness 架构基本实现，部分组件简化 |
| **设计合规性** | 7.0/10 | 错误处理完整，但乐观锁未完全实现 |
| **代码质量** | 8.0/10 | 命名规范，但有重复代码 |
| **多租户隔离** | 9.0/10 | owner_open_id 隔离正确 |
| **安全性** | 9.0/10 | SQL 注入防护完整，输入验证基本 |
| **性能** | 7.0/10 | 存在 N+1 查询和内存泄漏风险 |
| **可维护性** | 7.5/10 | 职责清晰，但有重复代码 |

### 11.2 总体评分

**7.9/10 (B+)**

**对标 v1.6.4 审查**：
- v1.6.4: 7.5/10 (B)
- v1.7: 7.9/10 (B+)

**提升点**：
- ✅ 统一 Service 层（vs v1.6.4 直连数据库）
- ✅  Harness 架构落地（Task Router、Session State、Validator）
- ✅ 错误处理框架（ServiceResult、错误码）

**待改进**：
- ⚠️ 乐观锁未完全实现（Schema 缺失）
- ⚠️ 技能改造不彻底
- ⚠️ 缺少测试覆盖

---

## 12. 结论

### 12.1 审查结论

**⚠️ 有条件通过 (Conditional Pass)**

v1.7 实现了 Harness 架构的核心组件，多租户隔离机制正确，错误处理框架完整。但存在以下关键问题需在 QA 前修复：

**必改项（P0）**：
1. 添加 version 字段到 schema.sql（formulas、customers、ingredient_prices）
2. CustomerService 和 PriceService 实现乐观锁
3. CustomerRecordSkill 和 NutritionAnalysisSkill 注入 Service
4. Harness 添加审计日志
5. CalculationService 优化 N+1 查询

**建议项（P1）**：
1. 提取 ServiceResult 到公共模块
2. 统一 ingredient_map 到 constants.py
3. 添加线程安全保护
4. 补充单元测试

### 12.2 与开发者自审对比

| 维度 | 开发者自审 | 独立审查 | 差异说明 |
|------|-----------|---------|---------|
| 架构一致性 | A- | B+ (8.5/10) | 开发者高估了乐观锁实现完整度 |
| 代码质量 | A- | B+ (8.0/10) | 重复代码未计入 |
| 测试覆盖 | 未评分 | 缺失 | 开发者未提供测试文件 |

### 12.3 下一步建议

1. **修复 P0 问题**（预计 8-10 小时）
2. **补充单元测试**（预计 6-8 小时）
3. **性能优化**（N+1 查询、线程安全）
4. **回归测试**（验证 v1.6 技能功能未退化）

---

**审查人签名**: OpenClaw Reviewer  
**审查完成时间**: 2026-03-29 18:30 GMT+8

---

## 附录 A：代码行统计

| 文件 | 行数 | 新增/修改 | 审查状态 |
|------|------|----------|---------|
| src/harness/harness.py | 308 | 新增 | ✅ 通过 |
| src/harness/task_router.py | 109 | 新增 | ✅ 通过 |
| src/harness/session_state.py | 116 | 新增 | ✅ 通过 |
| src/harness/result_validator.py | 148 | 新增 | ✅ 通过 |
| src/services/formula_service.py | 305 | 新增 | ✅ 通过（需修复乐观锁） |
| src/services/price_service.py | 223 | 新增 | ✅ 通过（需修复乐观锁） |
| src/services/calculation_service.py | 169 | 新增 | ⚠️ N+1 查询 |
| src/services/customer_service.py | 241 | 新增 | ✅ 通过（需修复乐观锁） |
| src/constants.py | 128 | 新增 | ✅ 通过 |
| src/database/repository.py | ~400 | 修改 | ✅ 通过 |
| skills/formula_cost_skill/skill.py | ~250 | 修改 | ⚠️ legacy 代码 |
| skills/price_lookup_skill/skill.py | ~200 | 修改 | ✅ 通过 |
| skills/customer_record_skill/skill.py | ~230 | 修改 | ⚠️ 未注入 Service |
| skills/nutrition_analysis_skill/skill.py | ~240 | 修改 | ⚠️ 未注入 Service |

---

## 附录 B：错误码实现状态

| 错误码 | FormulaService | PriceService | CustomerService | CalculationService |
|-------|---------------|--------------|-----------------|-------------------|
| E001 | ✅ | ✅ | ✅ | N/A |
| E002 | ✅ | ✅ | ✅ | ✅（传递） |
| E003 | ✅ | N/A | ✅ | N/A |
| E004 | ✅ | N/A | ✅ | N/A |
| E005 | ✅ | N/A | N/A | N/A |
| E006 | ✅ | ❌ | ❌ | N/A |
