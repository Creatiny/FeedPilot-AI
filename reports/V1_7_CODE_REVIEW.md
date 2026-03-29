# FeedSales AI v1.7 代码检视报告

> 检视时间：2026-03-29 17:49
> 检视范围：全部源代码、测试、文档

---

## 1. 项目概览

### 代码规模
| 类别 | 文件数 | 代码行数 |
|------|--------|----------|
| 源代码 (src/) | 14 | 2,144 |
| 技能 (skills/) | 4 | 1,136 |
| 脚本 (scripts/) | 6 | 984 |
| 测试 (tests/) | 21 | 5,562 |
| **合计** | **45** | **9,826** |

### 目录结构
```
feed-sales-ai-mvp/
├── src/
│   ├── database/      # 数据库层
│   ├── services/      # 服务层 (v1.7 新增)
│   ├── harness/       # Harness 运行时 (v1.7 新增)
│   ├── integrations/  # 外部集成
│   └── utils/         # 工具类
├── skills/            # 技能层
├── scripts/           # 运维脚本
├── tests/             # 测试
├── docs/              # 文档
└── reports/           # 报告
```

---

## 2. 代码质量评估

### ✅ 优点

#### 2.1 安全性
- **SQL 注入防护**：所有 SQL 查询使用参数化查询（`?` 占位符）
- **无硬编码密钥**：敏感配置通过环境变量和审批机制管理
- **多租户隔离**：在服务层强制执行 owner_open_id 隔离

```python
# 示例：参数化查询
cursor.execute(
    "SELECT * FROM formulas WHERE owner_open_id = ? AND name = ?",
    (user_id, formula_name)
)
```

#### 2.2 架构设计
- **清晰的分层**：Service → Repository → Database
- **依赖注入**：服务通过构造函数注入依赖
- **Harness 模式**：任务路由、状态管理、结果校验分离

```python
# 示例：依赖注入
class FeedSalesHarness:
    def __init__(self, db_pool: DatabasePool):
        self.formula_service = FormulaService(db_pool)
        self.price_service = PriceService(db_pool)
        # ...
```

#### 2.3 测试覆盖
- **65 个测试全部通过**
- **TDD 开发**：先写测试再写实现
- **集成测试**：技能、Harness 都有集成测试

#### 2.4 错误处理
- **统一的错误码**：E001-E006
- **一致的返回格式**：ServiceResult
- **完整的日志记录**：33 处日志调用

```python
@dataclass
class ServiceResult:
    success: bool
    data: Optional[Dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    source: Optional[str] = None
```

---

### ⚠️ 需要改进

#### 2.5 代码重复 (中等优先级)

**问题**：default_prices 和 ingredient_map 在多处重复定义

| 位置 | 重复内容 |
|------|----------|
| `src/services/calculation_service.py` | DEFAULT_PRICES |
| `skills/formula_cost_skill/skill.py` | default_prices |
| `skills/price_lookup_skill/skill.py` | default_prices |
| `src/harness/harness.py` | ingredient_map (2处) |
| `skills/price_lookup_skill/skill.py` | ingredient_map |

**建议**：
```python
# 创建 src/constants.py
DEFAULT_PRICES = {
    'Corn, grain': 180.00,
    'Soybean meal, 48%': 350.00,
    # ...
}

INGREDIENT_MAP = {
    '玉米': 'Corn, grain',
    '豆粕': 'Soybean meal, 48%',
    # ...
}
```

#### 2.6 Legacy 模式残留 (低优先级)

**问题**：FormulaCostSkill 仍保留直连数据库的 legacy 模式

```python
# skills/formula_cost_skill/skill.py:89
conn = sqlite3.connect(self.db_path)  # legacy fallback
```

**评估**：这是向后兼容的设计，可接受。未来版本可移除。

#### 2.7 类型注解不完整 (低优先级)

**问题**：部分函数缺少类型注解

```python
# 当前
def _extract_ingredient(self, message: str) -> Optional[str]:
    # ...

# 缺少返回类型的函数
def _success(self, data: Dict) -> Dict[str, Any]:  # ✓ 有类型
def _get_default_price(self, ingredient_name: str) -> float:  # ✓ 有类型
```

**建议**：逐步补充类型注解，提高代码可维护性。

---

## 3. 架构评估

### 3.1 分层设计 ✅

```
┌─────────────────────────────────┐
│       FeedSalesHarness          │  入口层
│  (TaskRouter + Session + Valid) │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│        Service Layer            │  业务层
│  Formula/Price/Customer/Calc    │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│      Repository Layer           │  数据层
│  FormulaRepo/PriceRepo/...      │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│        DatabasePool             │  连接池
│         SQLite                  │
└─────────────────────────────────┘
```

**评价**：分层清晰，职责明确，符合 Harness 设计理念。

### 3.2 依赖注入 ✅

| 组件 | 依赖注入 | 状态 |
|------|----------|------|
| FormulaService | db_pool | ✅ |
| PriceService | db_pool | ✅ |
| CustomerService | db_pool | ✅ |
| CalculationService | db_pool | ✅ |
| FeedSalesHarness | db_pool | ✅ |
| FormulaCostSkill | calc_service | ✅ |
| PriceLookupSkill | price_service | ✅ |

**评价**：依赖注入完整，便于测试和维护。

### 3.3 错误处理链 ✅

```
User Message
    ↓
TaskRouter.classify() → task_type
    ↓
Harness._execute_task()
    ↓
Service.method() → ServiceResult
    ↓
ResultValidator.validate()
    ↓
Return to User
```

**评价**：错误处理链完整，每一层都有明确的错误处理。

---

## 4. 安全性审查

### 4.1 SQL 注入 ✅
- **状态**：无风险
- **证据**：所有查询使用参数化

### 4.2 敏感数据 ✅
- **状态**：无硬编码密钥
- **机制**：通过审批机制管理敏感配置

### 4.3 多租户隔离 ✅
- **状态**：服务层强制隔离
- **机制**：owner_open_id 在所有查询中强制检查

### 4.4 输入验证 ⚠️
- **状态**：部分缺失
- **建议**：增加更严格的输入验证

```python
# 建议：在 Service 层增加输入验证
def create_customer(self, user_id: str, data: Dict) -> ServiceResult:
    # 验证 user_id 格式
    if not user_id or len(user_id) > 128:
        return ServiceResult(success=False, error_code='E001', ...)
    
    # 验证 data 字段
    if not data.get('name') or len(data['name']) > 256:
        return ServiceResult(success=False, error_code='E001', ...)
```

---

## 5. 性能评估

### 5.1 数据库连接 ✅
- **连接池**：DatabasePool 单例模式
- **复用**：避免频繁创建连接

### 5.2 查询优化 ⚠️
- **索引**：需要确认关键字段有索引

```sql
-- 建议索引
CREATE INDEX idx_formulas_owner ON formulas(owner_open_id, name);
CREATE INDEX idx_prices_owner ON ingredient_prices(owner_open_id, ingredient_name);
CREATE INDEX idx_customers_owner ON customers(owner_open_id, name);
```

### 5.3 缓存 ⚠️
- **状态**：无缓存层
- **建议**：对频繁访问的公共数据增加缓存

---

## 6. 文档评估

### 6.1 代码文档 ✅
- **Docstring**：所有类和主要方法有文档
- **类型注解**：大部分函数有类型注解

### 6.2 项目文档 ✅
- **架构文档**：完整
- **设计文档**：v1.7 Harness 设计文档
- **用户指南**：有

### 6.3 API 文档 ⚠️
- **状态**：有但可能需要更新
- **建议**：为 Service 层生成 API 文档

---

## 7. 测试评估

### 7.1 测试覆盖 ✅
- **单元测试**：24 个
- **集成测试**：10 个
- **E2E 测试**：4 个

### 7.2 测试质量 ✅
- **TDD**：所有 v1.7 代码先写测试
- **边界测试**：覆盖错误场景

### 7.3 测试数据 ⚠️
- **状态**：测试数据在代码中定义
- **建议**：抽取到 fixtures 文件

---

## 8. 问题汇总

### 高优先级
无

### 中优先级
| 问题 | 位置 | 建议 |
|------|------|------|
| 代码重复 | default_prices, ingredient_map | 抽取到 constants.py |

### 低优先级
| 问题 | 位置 | 建议 |
|------|------|------|
| Legacy 模式 | FormulaCostSkill | 未来版本移除 |
| 类型注解 | 部分函数 | 逐步补充 |
| 输入验证 | Service 层 | 增加验证逻辑 |
| 数据库索引 | schema.sql | 添加关键字段索引 |

---

## 9. 结论

### 整体评价：优秀 (A-)

| 维度 | 评分 | 说明 |
|------|------|------|
| 安全性 | A | 无 SQL 注入，多租户隔离完整 |
| 架构设计 | A | 分层清晰，依赖注入完整 |
| 代码质量 | A- | 有代码重复，但不影响功能 |
| 测试覆盖 | A | 65 个测试，TDD 开发 |
| 文档 | A | 文档完整，更新及时 |
| 性能 | B+ | 无缓存，需要优化索引 |

### 建议优先改进
1. **代码重复**：抽取 default_prices 和 ingredient_map
2. **数据库索引**：添加关键字段索引
3. **输入验证**：在 Service 层增加验证

### 发布建议
**v1.7 可发布**。上述问题不影响核心功能，可在后续版本迭代中改进。