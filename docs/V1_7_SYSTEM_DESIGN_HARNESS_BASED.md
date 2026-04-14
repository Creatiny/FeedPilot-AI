# FeedSales AI v1.7 系统设计方案（基于 Harness 理念）

## 0. 前言：为什么 v1.7 必须基于 Harness 理念

### 现有问题诊断
v1.6.3 的核心问题不是"功能不够"，而是**环境设计不足**：

| 问题 | Harness 视角的诊断 |
|------|-------------------|
| 技能直连数据库 | 没有统一接口层，模型直接操作数据 |
| 字段名不一致 | 没有统一数据契约，schema 和代码脱节 |
| 测试覆盖不足 | 没有结构化验证层 |
| 多用户隔离靠约定 | 没有在接口层强制隔离 |
| 无状态管理 | 没有会话上下文、任务状态 |

### Harness 的核心定义
> **Harness 是模型运行的完整环境**：包括可调用的工具、信息格式、历史管理、错误护栏、跨会话接力机制。

**模型负责理解与表达，Harness 负责业务真值和状态管理。**

---

## 1. v1.7 目标：从 Demo 升级为最小可用业务系统

### 核心目标
1. **多用户私有数据隔离**：配方库、原料价格、客户信息
2. **统一数据访问层**：Repository + Service，禁止直连
3. **最小 Harness 落地**：任务路由、状态管理、结果校验
4. **私有优先 / 公共回退**：查询策略明确化

### 本版本不做
- 复杂多 Agent 编排
- 团队权限体系
- 自动长期自治

---

## 2. 架构设计：FeedSales 业务最小 Harness

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Bot / API                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Harness Runtime Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Task Router │  │Session State│  │  Result Validator   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer (统一入口)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │FormulaService│  │ PriceService │  │CustomerService   │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │CalcService   │  │ ReportService│  │AnalyticsService  │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer (数据访问)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │FormulaRepo   │  │  PriceRepo   │  │  CustomerRepo    │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Database Layer                           │
│       SQLite (feed_sales.db) + Schema Migration              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Harness Runtime Layer（新增）

这是 v1.7 的核心增量，按照 ACI 和 Harness 理念设计。

#### Task Router（任务路由器）
把用户请求分类为固定任务类型：

| 任务类型 | 描述 | 触发示例 |
|---------|------|---------|
| `formula_cost_query` | 配方成本查询 | "保育料多少钱一吨" |
| `formula_manage` | 配方管理 | "创建/修改/查看我的配方" |
| `price_query` | 价格查询 | "玉米价格" |
| `price_manage` | 价格管理 | "设置我的玉米采购价" |
| `customer_manage` | 客户管理 | "添加客户张三" |
| `quote_generate` | 生成报价 | "给客户张三报保育料" |
| `nutrition_analysis` | 营养分析 | "分析保育料营养" |
| `formula_compare` | 配方对比 | "对比两个配方成本" |

**设计原则**：先确定任务类型，再进入执行流，避免模型在所有能力里乱猜。

#### Session State Manager（会话状态管理）
维护当前会话上下文：

```python
class SessionState:
    user_id: str
    current_customer: Optional[str]
    current_formula: Optional[str]
    price_mode: str  # "private" | "public" | "mixed"
    last_quote_result: Optional[Dict]
    conversation_turn: int
```

**作用**：
- 支持连续对话
- 避免每轮都重新理解上下文
- 让模型知道"我们在做什么"

#### Result Validator（结果校验器）
对关键输出进行结构化校验：

| 校验类型 | 规则 |
|---------|------|
| 配方校验 | 成分比例和 ≈ 100%，无重复原料 |
| 价格校验 | 价格为正数，单位为 USD/ton |
| 成本校验 | 明细和 = 总成本，来源说明完整 |
| 客户校验 | name 必填，phone/email 至少一个 |

**作用**：在返回用户前拦截错误，而不是让错误流出去。

### 2.3 Service Layer（统一业务逻辑）

每个 Service 封装一个业务域，提供清晰的接口：

```python
class FormulaService:
    def get_formula(self, user_id: str, name: str) -> Formula
    def list_formulas(self, user_id: str) -> List[Formula]
    def create_formula(self, user_id: str, data: FormulaData) -> Formula
    def update_formula(self, user_id: str, formula_id: int, data: FormulaData) -> Formula
    def delete_formula(self, user_id: str, formula_id: int) -> bool
    
class PriceService:
    def get_price(self, user_id: str, ingredient_code: str) -> Price  # 私有优先，按 ingredient_code 查询
    def get_public_price(self, ingredient_code: str) -> Price  # 仅公共，按 ingredient_code 查询
    def set_private_price(self, user_id: str, ingredient_code: str, price: float)
    def list_private_prices(self, user_id: str) -> List[Price]
    def batch_get_prices(self, user_id: str, ingredient_codes: List[str]) -> Dict[str, Price]  # 批量查询

class CustomerService:
    def get_customer(self, user_id: str, name: str) -> Customer
    def list_customers(self, user_id: str) -> List[Customer]
    def create_customer(self, user_id: str, data: CustomerData) -> Customer
    def update_customer(self, user_id: str, customer_id: int, data: CustomerData) -> Customer
    def delete_customer(self, user_id: str, customer_id: int) -> bool

class CalculationService:
    def calculate_cost(self, user_id: str, formula_name: str) -> CostResult  # 内部通过 ingredient_code 批量查价格
    def compare_formulas(self, user_id: str, names: List[str]) -> CompareResult
    def generate_quote(self, user_id: str, formula_name: str, customer_name: str) -> Quote
```

### 2.4 Repository Layer（数据访问）

已有的 Repository 继续使用，增强为：
- 强制 owner_id 隔离
- 统一错误处理
- 日志记录

---

## 3. 数据模型设计

### 3.1 用户隔离模型

所有核心业务表引入 `owner_open_id`：

| 表 | owner 字段 | 说明 |
|---|-----------|------|
| `formulas` | owner_open_id | 私有配方 |
| `formula_ingredients` | (继承 formula) | 配方成分（含 ingredient_code） |
| `ingredient_prices` | owner_open_id | 私有价格（含 ingredient_code） |
| `customers` | owner_open_id | 客户信息 |
| `customer_interactions` | owner_open_id | 客户跟进 |
| `quotes` | owner_open_id | 报价记录 |

**公共数据**：`owner_open_id = 'system_public'`

**ingredient_code（原料代码）**：所有涉及原料的表（`ingredient_prices`、`formula_ingredients`）必须包含 `ingredient_code` 字段，作为精确查找键。

| 方面 | ingredient_name | ingredient_code |
|------|----------------|----------------|
| 用途 | 人类可读的显示名称 | 系统内部精确匹配键 |
| 唯一性 | 不同数据源可能使用不同名称 | 同一原料唯一代码 |
| 查询方式 | LIKE 模糊匹配（有歧义风险） | IN 精确匹配（无歧义） |
| 索引 | LIKE 无法利用索引 | exact match 可用索引 |

**为什么 ingredient_code 与 owner_open_id 正交且互补**：
- `owner_open_id` 解决**用户间隔离**：不同用户的私有数据互不可见
- `ingredient_code` 解决**同用户下多数据源共存**：同一原料来自 CBOT（"Corn, #2 Yellow CBOT"）、USDA AMS（"Corn, No.2 Yellow"）、配方用名（"Corn, grain"）等不同命名，但共享同一 `ingredient_code = ING_CORN`
- 两者缺一不可：没有 `ingredient_code`，多数据源插入时无法精确去重和查找

**注意**：`formulas` 表包含 `animal_type` 字段（Swine, Beef Cattle, Broiler 等），已在 v1.6.4 修复中添加。`formula_ingredients` 表包含 `ingredient_code` 字段，已在 v1.6 迁移中添加。

### 3.2 新增表

#### ingredient_prices（原料价格表，含 ingredient_code）
```sql
CREATE TABLE ingredient_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT NOT NULL,
    ingredient_code TEXT NOT NULL,         -- 原料代码（精确查找键）
    ingredient_name TEXT NOT NULL,         -- 原料名称（显示用）
    price REAL NOT NULL,
    price_date DATE NOT NULL,
    source TEXT,                           -- 数据来源（CBOT, USDA AMS 等）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ingredient_code, price_date, owner_open_id)
);
CREATE INDEX idx_prices_code ON ingredient_prices(ingredient_code);
```

#### formula_ingredients（配方成分表，含 ingredient_code）
```sql
-- formula_ingredients 属于 formulas，ingredient_code 用于关联价格查询
-- ingredient_code 无 FK 约束，由应用层保证引用有效性
```

#### quotes（报价记录）
```sql
CREATE TABLE quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_open_id TEXT NOT NULL,
    customer_id INTEGER,
    formula_name TEXT NOT NULL,
    cost_per_ton REAL NOT NULL,
    price_per_ton REAL,  -- 报价（可加利润）
    valid_until DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### session_states（会话状态，可选）
```sql
CREATE TABLE session_states (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    state_json TEXT NOT NULL,  -- JSON 序列化
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. 查询策略：私有优先 / 公共回退

### 4.1 配方查询
```python
def get_formula(user_id, name):
    # 1. 先查私有
    formula = repo.get_private_formula(user_id, name)
    if formula:
        return formula, source="private"
    
    # 2. 再查公共
    formula = repo.get_public_formula(name)
    if formula:
        return formula, source="public"
    
    return None, source="not_found"
```

### 4.2 价格查询（基于 ingredient_code 精确匹配）
```python
def get_price(user_id, ingredient_code):
    # 1. 私有价格（按 ingredient_code 精确查找）
    price = repo.get_private_price(user_id, ingredient_code)
    if price:
        return price, source="private"
    
    # 2. 公共价格（按 ingredient_code 精确查找）
    price = repo.get_public_price(ingredient_code)
    if price:
        return price, source="public"
    
    return None, source="not_found"
```

**关键设计**：价格查询使用 `ingredient_code` 而非 `ingredient_name`，原因：
- 不同数据源对同一原料使用不同命名（如 CBOT 的 "Corn, #2 Yellow CBOT" vs USDA AMS 的 "Corn, No.2 Yellow"）
- `ingredient_code`（如 `ING_CORN`）是跨数据源的统一标识，确保精确匹配
- 批量查询使用 `IN(ingredient_code)` 而非 `LIKE '%name%'`，避免歧义和性能问题

### 4.3 成本计算时的来源追踪
结果必须包含：
```json
{
  "total_cost": 285.50,
  "price_sources": {
    "ING_CORN": "private",
    "ING_SBM": "public",
    "ING_PREMIX": "default"
  },
  "missing_prices": []
}
```

**注意**：`price_sources` 的键使用 `ingredient_code` 而非 `ingredient_name`，确保跨数据源一致性。

---

## 5. Harness 最小实现：关键组件

### 5.1 Task Router 实现

```python
class TaskRouter:
    TASK_PATTERNS = {
        "formula_cost_query": [
            r"(计算|查).*(成本|价格|多少钱)",
            r".*配方.*成本",
        ],
        "formula_manage": [
            r"(创建|添加|新建|修改|删除).*(配方)",
            r"(查看|列出).*配方",
        ],
        "price_query": [
            r"(查|问).*(价格|行情)",
            r".*(价格|多少钱)",
        ],
        "price_manage": [
            r"(设置|修改|更新).*价格",
            r"我的.*价格",
        ],
        "customer_manage": [
            r"(添加|创建|修改|删除).*客户",
            r"(查看|列出).*客户",
        ],
        "quote_generate": [
            r"(生成|做|开).*报价",
            r"给.*报价",
        ],
    }
    
    def classify(self, message: str) -> str:
        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    return task_type
        return "unknown"
```

### 5.2 Session State 实现

```python
class SessionStateManager:
    def __init__(self):
        self.sessions = {}  # session_id -> SessionState
    
    def get_state(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState()
        return self.sessions[session_id]
    
    def update_state(self, session_id: str, **kwargs):
        state = self.get_state(session_id)
        for key, value in kwargs.items():
            setattr(state, key, value)
```

### 5.3 Result Validator 实现

```python
class ResultValidator:
    def validate_cost_result(self, result: Dict) -> ValidationResult:
        errors = []
        
        # 总成本必须为正数
        if result.get("total_cost", 0) <= 0:
            errors.append("总成本必须大于0")
        
        # 明细和 = 总成本
        detail_sum = sum(d["cost"] for d in result.get("details", []))
        if abs(detail_sum - result["total_cost"]) > 0.01:
            errors.append(f"明细和({detail_sum})不等于总成本({result['total_cost']})")
        
        # 所有来源必须标注
        for detail in result.get("details", []):
            if not detail.get("price_source"):
                errors.append(f"{detail['name']} 缺少价格来源")
        
        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

---

## 6. 技能改造：走 Harness 接口

### 6.1 FormulaCostSkill 改造

**改造前**：直连 sqlite3
**改造后**：依赖注入 Service

```python
class FormulaCostSkill:
    def __init__(self, formula_service: FormulaService, 
                 price_service: PriceService,
                 calc_service: CalculationService):
        self.formula_service = formula_service
        self.price_service = price_service
        self.calc_service = calc_service
    
    async def execute(self, user_id: str, message: str) -> Dict:
        # 1. 提取配方名
        formula_name = self._extract_formula_name(message)
        
        # 2. 调用计算服务（走统一接口）
        result = self.calc_service.calculate_cost(user_id, formula_name)
        
        # 3. 校验结果
        validation = ResultValidator().validate_cost_result(result)
        if not validation.valid:
            return {"success": False, "errors": validation.errors}
        
        return {"success": True, "data": result}
```

---

## 6. 非功能性需求（补充）

### 6.1 错误处理流程

#### 错误码定义
| 错误码 | 类型 | 说明 |
|-------|------|------|
| E001 | 参数错误 | 缺少必填参数或参数格式错误 |
| E002 | 数据不存在 | 配方/价格/客户不存在 |
| E003 | 权限错误 | 用户无权访问该数据 |
| E004 | 业务错误 | 成分比例不等于100%等 |
| E005 | 系统错误 | 数据库连接失败等 |
| E006 | 并发冲突 | 数据已被其他用户修改，请刷新后重试 |

#### 错误传递机制
```python
class ServiceResult:
    success: bool
    data: Optional[Dict]
    error_code: Optional[str]
    error_message: Optional[str]

# Service 层
def get_formula(user_id: str, name: str) -> ServiceResult:
    formula = self.repo.get_formula(user_id, name)
    if not formula:
        return ServiceResult(
            success=False,
            error_code="E002",
            error_message=f"配方 '{name}' 不存在"
        )
    return ServiceResult(success=True, data=formula)

# Harness 层
def handle_result(result: ServiceResult) -> Dict:
    if not result.success:
        # 根据错误码生成用户友好消息
        user_message = ERROR_MESSAGES.get(result.error_code, "操作失败")
        return {"success": False, "error": user_message}
    return {"success": True, "data": result.data}
```

### 6.2 并发控制设计

#### 乐观锁机制

**应用范围**：所有可更新的业务表

| 表名 | 是否需要 version | 说明 |
|------|-----------------|------|
| `formulas` | ✓ | 配方可被修改 |
| `formula_ingredients` | ✗ | 随配方一起更新 |
| `ingredient_prices` | ✓ | 私有价格可被修改 |
| `customers` | ✓ | 客户信息可被修改 |
| `quotes` | ✗ | 报价单生成后不可修改 |

```sql
-- 为需要的表添加版本字段
ALTER TABLE formulas ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE ingredient_prices ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE customers ADD COLUMN version INTEGER DEFAULT 1;

-- 更新时检查版本
UPDATE formulas 
SET name = ?, stage_type = ?, version = version + 1
WHERE id = ? AND owner_open_id = ? AND version = ?;
```

#### 更新流程
```python
def update_formula(user_id: str, formula_id: int, data: Dict, expected_version: int) -> ServiceResult:
    result = self.repo.update_formula_with_version(
        user_id, formula_id, data, expected_version
    )
    if result.rowcount == 0:
        return ServiceResult(
            success=False,
            error_code="E006",
            error_message="数据已被其他用户修改，请刷新后重试"
        )
    return ServiceResult(success=True, data=result.data)
```

### 6.3 Session State 持久化策略

**策略**：内存 + 可选数据库持久化

```python
class SessionStateManager:
    def __init__(self, db_pool: Optional[DatabasePool] = None):
        self.memory_store = {}  # 内存缓存
        self.db_pool = db_pool  # 可选数据库持久化
        self.ttl = 3600  # 1小时过期
    
    def get_state(self, session_id: str) -> SessionState:
        # 1. 先查内存
        if session_id in self.memory_store:
            return self.memory_store[session_id]
        
        # 2. 再查数据库（如果启用）
        if self.db_pool:
            state = self._load_from_db(session_id)
            if state:
                self.memory_store[session_id] = state
                return state
        
        # 3. 创建新状态
        state = SessionState()
        self.memory_store[session_id] = state
        return state
    
    def save_state(self, session_id: str, state: SessionState):
        self.memory_store[session_id] = state
        if self.db_pool:
            self._save_to_db(session_id, state)
    
    def cleanup_expired(self):
        """定期清理过期会话"""
        now = time.time()
        expired = [sid for sid, s in self.memory_store.items() 
                   if now - s.last_access > self.ttl]
        for sid in expired:
            del self.memory_store[sid]
```

### 6.4 日志审计设计

#### 日志格式
```json
{
  "timestamp": "2026-03-29T13:00:00Z",
  "level": "INFO",
  "user_id": "user_123",
  "session_id": "sess_456",
  "action": "formula_cost_query",
  "formula_name": "Nursery Diet 1",
  "result": "success",
  "duration_ms": 45,
  "price_sources": {"Corn": "private", "Soybean meal": "public"}
}
```

#### 日志类型
| 类型 | 级别 | 说明 |
|------|------|------|
| 操作日志 | INFO | 用户操作记录（查询、创建、更新、删除） |
| 错误日志 | ERROR | 业务错误、系统错误 |
| 审计日志 | INFO | 敏感操作（私有数据访问、报价生成） |

#### 日志保留策略
| 日志类型 | 存储位置 | 保留期限 | 清理方式 |
|----------|----------|----------|----------|
| 操作日志 | `logs/operation.log` | 30 天 | 每日自动清理超过 30 天的日志 |
| 错误日志 | `logs/error.log` | 90 天 | 每日自动清理超过 90 天的日志 |
| 审计日志 | `logs/audit.log` | 365 天 | 每日自动清理超过 365 天的日志 |

#### 清理脚本
```bash
# 每日清理脚本（可加入 cron）
#!/bin/bash
LOG_DIR="/var/log/feedsales"
find $LOG_DIR -name "operation.log.*" -mtime +30 -delete
find $LOG_DIR -name "error.log.*" -mtime +90 -delete
find $LOG_DIR -name "audit.log.*" -mtime +365 -delete
```

#### 日志实现
```python
class AuditLogger:
    def log_operation(self, user_id: str, action: str, details: Dict, result: str):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "user_id": user_id,
            "action": action,
            "details": details,
            "result": result
        }
        logger.info(json.dumps(log_entry))
    
    def log_sensitive_access(self, user_id: str, resource_type: str, resource_id: str):
        self.log_operation(user_id, "sensitive_access", {
            "resource_type": resource_type,
            "resource_id": resource_id
        }, "success")
```

### 6.5 SQL 注入防护

**策略**：Repository 层强制使用参数化查询

```python
# ✅ 正确：参数化查询
cursor.execute(
    "SELECT * FROM formulas WHERE owner_open_id = ? AND name = ?",
    (user_id, formula_name)
)

# ❌ 错误：字符串拼接（禁止）
cursor.execute(
    f"SELECT * FROM formulas WHERE owner_open_id = '{user_id}'"
)
```

**代码审查规则**：
- 所有 SQL 语句必须使用 `?` 占位符
- 禁止任何形式的字符串拼接 SQL

---

## 7. 实施阶段

### Phase 1：数据层重构
- [ ] Schema 升级：添加 owner_open_id 到所有核心表
- [ ] Schema 确认：ingredient_prices 和 formula_ingredients 包含 ingredient_code（v1.6 已完成）
- [ ] 数据迁移：公共数据标记为 system_public
- [ ] 新增表：quotes, session_states

### Phase 2：Service Layer
- [ ] FormulaService
- [ ] PriceService
- [ ] CustomerService
- [ ] CalculationService

### Phase 3：Harness Runtime
- [ ] TaskRouter
- [ ] SessionStateManager
- [ ] ResultValidator

### Phase 4：技能改造
- [ ] FormulaCostSkill → 走 CalculationService
- [ ] PriceLookupSkill → 走 PriceService
- [ ] CustomerRecordSkill → 走 CustomerService
- [ ] NutritionAnalysisSkill → 走 FormulaService

### Phase 5：私有数据功能
- [ ] 私有配方 CRUD
- [ ] 私有价格设置
- [ ] 私有客户管理

### Phase 6：测试与验证
- [ ] 多用户隔离测试
- [ ] 私有/公共回退测试
- [ ] 端到端测试

---

## 8. 文档规划

- [ ] `docs/V1_7_ARCHITECTURE.md` — 架构文档
- [ ] `docs/HARNESS_DESIGN.md` — Harness 设计
- [ ] `docs/API_REFERENCE.md` — Service API 参考
- [ ] `docs/MULTI_TENANT_MODEL.md` — 多租户数据模型

---

## 9. 结论

v1.7 的本质是**从"技能直连数据"升级为"Harness 驱动的业务系统"**：

| 层面 | v1.6.x | v1.7 |
|------|--------|------|
| 数据访问 | 直连 sqlite | Repository + Service |
| 业务逻辑 | 在技能里散落 | Service 层统一 |
| 用户隔离 | 靠约定 | 强制在接口层 |
| 状态管理 | 无 | SessionState |
| 结果校验 | 无 | ResultValidator |
| 任务路由 | 无 | TaskRouter |

**一句话**：v1.7 让 FeedSales 从"能回答问题"变成"能可靠执行业务流程"。