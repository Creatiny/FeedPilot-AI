# FeedSales AI v1.7 任务拆解清单（基于 Harness 理念）

## 目标
将 v1.7 设计方案拆解为可执行开发任务，按依赖顺序推进。

---

## Phase 1：数据层重构

### Task 1.1：Schema 升级
**文件**：`src/database/schema.sql`

**修改内容**：
- [ ] 为 `ingredient_prices` 添加 `owner_open_id`（已有）
- [ ] 为 `formulas` 添加 `owner_open_id`（已有）
- [ ] 新增 `quotes` 表
- [ ] 新增 `session_states` 表（可选）
- [ ] 统一货币为 USD

**验证**：
```bash
python3 -c "
from src.database.pool import DatabasePool
pool = DatabasePool('data/test_schema.db')
# 检查表结构
"
```

### Task 1.2：数据迁移脚本
**文件**：`scripts/migrate_v17_schema.py`

**功能**：
- [ ] 检查当前 schema 版本
- [ ] 为公共数据设置 `owner_open_id = 'system_public'`
- [ ] 保留用户已有数据

### Task 1.3：数据库初始化更新
**文件**：`scripts/init_database.py`

**修改**：
- [ ] 使用新 schema.sql
- [ ] 自动导入种子数据
- [ ] 创建 system_public 用户

---

## Phase 2：Service Layer

### Task 2.1：FormulaService
**文件**：`src/services/formula_service.py`

**接口**：
```python
class FormulaService:
    def get_formula(self, user_id: str, name: str) -> Optional[Formula]
    def list_formulas(self, user_id: str) -> List[Formula]
    def create_formula(self, user_id: str, data: FormulaCreate) -> Formula
    def update_formula(self, user_id: str, formula_id: int, data: FormulaUpdate) -> Formula
    def delete_formula(self, user_id: str, formula_id: int) -> bool
    def get_public_formula(self, name: str) -> Optional[Formula]
```

**测试**：`tests/test_formula_service.py`

### Task 2.2：PriceService
**文件**：`src/services/price_service.py`

**接口**：
```python
class PriceService:
    def get_price(self, user_id: str, ingredient: str) -> Optional[Price]  # 私有优先
    def get_public_price(self, ingredient: str) -> Optional[Price]
    def set_private_price(self, user_id: str, ingredient: str, price: float, source: str = "manual")
    def list_private_prices(self, user_id: str) -> List[Price]
    def list_public_prices(self) -> List[Price]
```

**测试**：`tests/test_price_service.py`

### Task 2.3：CustomerService
**文件**：`src/services/customer_service.py`

**接口**：
```python
class CustomerService:
    def get_customer(self, user_id: str, name: str) -> Optional[Customer]
    def list_customers(self, user_id: str) -> List[Customer]
    def create_customer(self, user_id: str, data: CustomerCreate) -> Customer
    def update_customer(self, user_id: str, customer_id: int, data: CustomerUpdate) -> Customer
    def delete_customer(self, user_id: str, customer_id: int) -> bool
    def add_interaction(self, user_id: str, customer_id: int, interaction: Interaction) -> Interaction
```

**测试**：`tests/test_customer_service.py`

### Task 2.4：CalculationService
**文件**：`src/services/calculation_service.py`

**接口**：
```python
class CalculationService:
    def calculate_cost(self, user_id: str, formula_name: str) -> CostResult
    def compare_formulas(self, user_id: str, names: List[str]) -> CompareResult
    def generate_quote(self, user_id: str, formula_name: str, 
                       customer_name: str, margin: float = 0.0) -> Quote
```

**关键逻辑**：
- [ ] 拉取配方（私有优先）
- [ ] 拉取价格（私有优先）
- [ ] 计算成本
- [ ] 标注来源
- [ ] 校验结果

**测试**：`tests/test_calculation_service.py`

### Task 2.5：Service 工厂
**文件**：`src/services/__init__.py`

**功能**：
- [ ] 统一创建所有 Service 实例
- [ ] 注入 Repository 依赖

---

## Phase 3：Harness Runtime

### Task 3.1：TaskRouter
**文件**：`src/harness/task_router.py`

**功能**：
- [ ] 定义任务类型枚举
- [ ] 定义匹配模式
- [ ] 实现 classify() 方法

**测试**：`tests/test_task_router.py`

### Task 3.2：SessionStateManager
**文件**：`src/harness/session_state.py`

**功能**：
- [ ] SessionState 数据类
- [ ] 内存存储实现
- [ ] get_state / update_state 方法

**测试**：`tests/test_session_state.py`

### Task 3.3：ResultValidator
**文件**：`src/harness/result_validator.py`

**功能**：
- [ ] validate_cost_result()
- [ ] validate_formula()
- [ ] validate_customer()

**测试**：`tests/test_result_validator.py`

### Task 3.4：Harness 入口
**文件**：`src/harness/__init__.py`

**功能**：
- [ ] 统一创建 Harness 组件
- [ ] 提供便捷访问方法

---

## Phase 4：技能改造

### Task 4.1：FormulaCostSkill 改造
**文件**：`skills/formula_cost_skill/skill.py`

**改造**：
- [ ] 移除直连 sqlite3
- [ ] 注入 CalculationService
- [ ] 调用统一接口
- [ ] 返回结构化结果

### Task 4.2：PriceLookupSkill 改造
**文件**：`skills/price_lookup_skill/skill.py`

**改造**：
- [ ] 注入 PriceService
- [ ] 支持私有价格查询
- [ ] 标注来源

### Task 4.3：CustomerRecordSkill 改造
**文件**：`skills/customer_record_skill/skill.py`

**改造**：
- [ ] 注入 CustomerService
- [ ] 已实现基本功能，检查是否走统一接口

### Task 4.4：NutritionAnalysisSkill 改造
**文件**：`skills/nutrition_analysis_skill/skill.py`

**改造**：
- [ ] 注入 FormulaService
- [ ] 已实现基本功能，检查是否走统一接口

### Task 4.5：技能工厂更新
**文件**：`skills/__init__.py`

**功能**：
- [ ] 统一创建技能实例
- [ ] 注入 Service 依赖

---

## Phase 5：私有数据功能

### Task 5.1：私有配方管理
**功能**：
- [ ] 创建私有配方
- [ ] 修改私有配方
- [ ] 删除私有配方
- [ ] 列出私有配方

**对话示例**：
- "创建我的保育料配方"
- "修改我的保育料，把豆粕改成 20%"
- "列出我的所有配方"

### Task 5.2：私有价格管理
**功能**：
- [ ] 设置私有价格
- [ ] 查看私有价格
- [ ] 用私有价格重新计算

**对话示例**：
- "我的玉米采购价是 180 美元/吨"
- "查看我的所有私有价格"

### Task 5.3：客户管理
**功能**：
- [ ] 添加客户
- [ ] 查看客户
- [ ] 更新客户
- [ ] 删除客户

**对话示例**：
- "添加客户张三，电话 123456"
- "查看我的客户列表"

### Task 5.4：报价生成
**功能**：
- [ ] 选择客户
- [ ] 选择配方
- [ ] 生成报价
- [ ] 可选：加利润率

**对话示例**：
- "给客户张三报保育料配方"
- "给客户李四报育肥料，加 10% 利润"

---

## Phase 6：测试与验证

### Task 6.1：多用户隔离测试
**文件**：`tests/test_multi_tenant_v17.py`

**测试场景**：
- [ ] 用户 A 创建配方，用户 B 看不到
- [ ] 用户 A 设置私有价格，用户 B 用公共价格
- [ ] 用户 A 的客户，用户 B 看不到

### Task 6.2：私有/公共回退测试
**文件**：`tests/test_private_public_fallback.py`

**测试场景**：
- [ ] 私有配方存在，返回私有
- [ ] 私有配方不存在，返回公共
- [ ] 都不存在，返回错误

### Task 6.3：成本计算测试
**文件**：`tests/test_cost_calculation_v17.py`

**测试场景**：
- [ ] 全私有价格
- [ ] 全公共价格
- [ ] 混合价格
- [ ] 缺失价格

### Task 6.4：端到端测试
**文件**：`tests/test_e2e_v17.py`

**测试场景**：
- [ ] 完整报价流程
- [ ] 连续对话流程

---

## Phase 7：文档

### Task 7.1：架构文档
**文件**：`docs/V1_7_ARCHITECTURE.md`

**内容**：
- [ ] 整体架构图
- [ ] 各层职责
- [ ] 数据流图

### Task 7.2：Harness 设计文档
**文件**：`docs/HARNESS_DESIGN.md`

**内容**：
- [ ] TaskRouter 设计
- [ ] SessionState 设计
- [ ] ResultValidator 设计

### Task 7.3：API 参考
**文件**：`docs/API_REFERENCE.md`

**内容**：
- [ ] Service 接口定义
- [ ] 数据模型定义
- [ ] 错误码定义

### Task 7.4：多租户数据模型
**文件**：`docs/MULTI_TENANT_MODEL.md`

**内容**：
- [ ] owner_open_id 机制
- [ ] 公共/私有数据区分
- [ ] 查询策略

---

## 里程碑

### Milestone 1：数据层 + Service 层
- Phase 1 完成
- Phase 2 完成
- 所有 Service 测试通过

### Milestone 2：Harness Runtime
- Phase 3 完成
- TaskRouter、SessionState、Validator 可用

### Milestone 3：技能改造
- Phase 4 完成
- 所有技能走统一接口

### Milestone 4：私有数据功能
- Phase 5 完成
- 完整的私有配方、价格、客户管理

### Milestone 5：测试与发布
- Phase 6 完成
- Phase 7 完成
- v1.7 发布

---

## 最高优先级任务

1. **Task 1.1**：Schema 升级
2. **Task 2.1**：FormulaService
3. **Task 2.2**：PriceService
4. **Task 2.4**：CalculationService
5. **Task 3.1**：TaskRouter
6. **Task 4.1**：FormulaCostSkill 改造

---

## 预计工时

| Phase | 预计工时 |
|-------|---------|
| Phase 1 | 4 小时 |
| Phase 2 | 8 小时 |
| Phase 3 | 4 小时 |
| Phase 4 | 4 小时 |
| Phase 5 | 4 小时 |
| Phase 6 | 4 小时 |
| Phase 7 | 2 小时 |
| **合计** | **30 小时** |

---

## 结论

v1.7 不是简单的功能迭代，而是**架构升级**。核心是从"技能直连数据"变成"Harness 驱动的业务系统"。

按照本任务清单执行，确保每一步都有可验证的产出。