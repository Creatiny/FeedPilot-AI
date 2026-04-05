# FeedSales AI v1.6.3 修复清单

> 基于 QA 测试报告 + 代码审查报告综合整理  
> 生成时间：2026-03-28  
> 目标版本：v1.6.4

---

## 修复统计

| 优先级 | 数量 | 预计工时 | 状态 |
|--------|------|---------|------|
| P0 阻塞 | 8 项 | 6 小时 | ⬜ 待修复 |
| P1 重要 | 7 项 | 10 小时 | ⬜ 待修复 |
| P2 建议 | 5 项 | 5 小时 | ⬜ 待修复 |
| P3 优化 | 3 项 | 3 小时 | ⬜ 待修复 |
| **合计** | **23 项** | **24 小时** | |

---

## P0 — 阻塞发布（必须全部修复）

### P0-01: SQL 字段名错误 `date` → `price_date`

**影响**：update_prices.py / cleanup_duplicates.py / FormulaCostSkill 全部报错  
**根因**：Schema 定义的是 `price_date`，代码中用的是 `date`

| 文件 | 行号 | 错误 | 修正 |
|------|------|------|------|
| `scripts/update_prices.py` | 多处 | `date` | `price_date` |
| `scripts/cleanup_duplicates.py` | 多处 | `date` | `price_date` |
| `skills/formula_cost_skill/skill.py` | SQL 查询 | `date` | `price_date` |

**验证**：
```bash
python scripts/update_prices.py   # 应不再报 OperationalError
python scripts/cleanup_duplicates.py  # 同上
```

---

### P0-02: INSERT 缺少 `owner_open_id`

**影响**：多租户数据无法写入（`owner_open_id NOT NULL` 约束）  
**文件**：`scripts/update_prices.py`

**修复方案**：
- INSERT 语句添加 `owner_open_id` 字段
- 使用系统级 owner（如 `"system_public"`）作为公共数据的 owner
- 同步修改 `ON CONFLICT` 子句匹配实际 UNIQUE 约束 `(ingredient_code, price_date, owner_open_id)`

```sql
-- 修复前
INSERT INTO ingredient_prices (ingredient_name, ingredient_code, price, date)
VALUES (?, ?, ?, ?)
ON CONFLICT (ingredient_name, date) DO UPDATE SET price = ?

-- 修复后
INSERT INTO ingredient_prices (owner_open_id, ingredient_name, ingredient_code, price, price_date, source, currency, unit)
VALUES (?, ?, ?, ?, ?, ?, 'CNY', 'ton')
ON CONFLICT (ingredient_code, price_date, owner_open_id) DO UPDATE SET price = excluded.price
```

---

### P0-03: scrape_formulas.py 方法名不匹配

**影响**：脚本直接 `AttributeError` 崩溃  
**文件**：`scripts/scrape_formulas.py` → `main()` 函数

| 调用（错误） | 实际方法名 |
|-------------|-----------|
| `scrape_standard_formulas()` | `scrape_nrc_formulas()` |
| `scrape_ingredient_nutrition()` | `scrape_usda_nutrition()` |
| `scrape_ingredient_prices()` | `scrape_us_prices()` |

**修复**：将 main() 中的调用改为实际方法名。

**验证**：
```bash
python scripts/scrape_formulas.py  # 应不再报 AttributeError
```

---

### P0-04: 种子数据文件缺失

**影响**：`migrate_data_to_db.py` 报 FileNotFoundError，数据库永远是空的  
**根因**：`data/nrc_formulas_full.json` 从未提交到 git

**修复方案（二选一）**：

**方案 A（推荐）**：创建种子数据生成脚本
- 新建 `scripts/seed_data.py`
- 内嵌基础配方/原料/价格数据（不依赖外部 JSON）
- `init_database.py` 完成后自动调用 `seed_data.py`

**方案 B**：提交现有 JSON 文件
- 将 `data/nrc_formulas_full.json` 加入版本控制
- 修改 `.gitignore` 确保不被忽略

**验证**：
```bash
python scripts/init_database.py
sqlite3 data/feed_sales.db "SELECT COUNT(*) FROM formulas"  # 应 > 0
sqlite3 data/feed_sales.db "SELECT COUNT(*) FROM ingredient_prices"  # 应 > 0
```

---

### P0-05: BarchartAPI print 语句残留

**影响**：生产日志无法收集/分级  
**文件**：`src/integrations/barchart_api.py`

| 行号 | 当前代码 | 修正 |
|------|---------|------|
| 56 | `print("⚠️ BARCHART_API_KEY 未配置")` | `logger.warning("BARCHART_API_KEY 未配置")` |
| 73 | `print(f"❌ API 错误：{...}")` | `logger.error(f"API 错误：{...}")` |
| 80 | `print(f"❌ 请求失败：{e}")` | `logger.error(f"请求失败：{e}")` |
| 85 | `print(f"❌ 数据解析失败：{e}")` | `logger.error(f"数据解析失败：{e}")` |

注意：`__main__` 演示块（161-168 行）中的 print 可保留。

**验证**：
```bash
grep -n "print(" src/integrations/barchart_api.py | grep -v "__main__"  # 应无结果
```

---

### P0-06: 测试 fixture `pool` 未定义

**影响**：test_database.py 和 test_p0_complete.py 共 3 个测试 ERROR  
**文件**：`tests/test_database.py`, `tests/test_p0_complete.py`

**修复**：在 conftest.py 或文件顶部添加 fixture：
```python
import pytest
from src.database.pool import DatabasePool

@pytest.fixture
def pool(tmp_path):
    db_path = str(tmp_path / "test.db")
    p = DatabasePool(db_path)
    yield p
```

---

### P0-07: `skills.base_skill` 模块不存在

**影响**：test_multi_tenant.py import 失败  
**根因**：测试引用了从未创建的 base_skill 模块

**修复方案（二选一）**：
- **A**：创建 `skills/base_skill.py`（如果架构需要基类）
- **B**：修改测试，移除对 base_skill 的依赖（如果不需要基类）

---

### P0-08: async 测试缺少 pytest-asyncio

**影响**：4 个 async 测试无法运行  
**修复**：
```bash
pip install pytest-asyncio
```
并在 `pyproject.toml` 或 `pytest.ini` 中配置：
```ini
[tool.pytest.ini_options]
asyncio_mode = auto
```

同时在 `requirements.txt`（如存在）中添加 `pytest-asyncio`。

---

## P1 — 重要问题（建议本轮修复）

### P1-01: FormulaCostSkill 直接 sqlite3，未用 Repository

**文件**：`skills/formula_cost_skill/skill.py`  
**问题**：绕过 DatabasePool 和 Repository 层，硬编码 `db_path = "data/feed_sales.db"`  
**修复**：改为依赖注入 Repository：
```python
class FormulaCostSkill:
    def __init__(self, formula_repo, price_repo):
        self.formula_repo = formula_repo
        self.price_repo = price_repo
```

---

### P1-02: FormulaCostSkill 字段名与 Schema 不匹配

**问题**：查询 `animal_category` 和 `stage`，Schema 中是 `stage_type` 和 `notes`  
**修复**：统一字段名，以 Schema 为准。

---

### P1-03: PriceLookupSkill 中英文原料名不一致

**问题**：代码用中文（玉米、豆粕），数据库用英文（Corn, Soybean meal）  
**修复**：建立中英文映射表，或统一为一种语言。

---

### P1-04: 货币单位混乱

**问题**：FormulaCostSkill 默认价格是 USD，PriceLookupSkill 返回 CNY  
**修复**：明确约定：
- 数据库存储统一用 CNY/吨
- Barchart API 获取的 USD 价格在入库前转换
- `convert_to_cny_ton()` 方法应被调用

---

### P1-05: CustomerRecordSkill 未实现

**文件**：`skills/customer_record_skill/skill.py`  
**问题**：execute() 只返回 "功能开发中"  
**修复**：实现基本 CRUD：
- 添加客户（提取姓名、电话、养殖类型）
- 查询客户列表
- 根据姓名查询客户

---

### P1-06: NutritionAnalysisSkill 未实现

**文件**：`skills/nutrition_analysis_skill/skill.py`  
**问题**：execute() 只返回 "功能开发中"  
**修复**：实现基本营养分析：
- 查询配方成分
- 计算粗蛋白、钙、磷（根据原料营养成分表）
- 对比 NRC 标准
- 输出达标/不达标判断

前提：需要 P0-04 种子数据中包含原料营养成分数据。

---

### P1-07: 测试硬编码路径

**文件**：`tests/test_database.py:16`, `tests/test_performance.py:20`, `tests/test_skills_real.py:24`  
**问题**：`"data/feed_sales.db"` 硬编码  
**修复**：统一使用 `tmp_path` fixture：
```python
@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")
```

---

## P2 — 建议改进

### P2-01: 技能工厂函数参数不统一
- 统一为 `create_skill(db_pool, repos...)` 模式

### P2-02: RateLimiter 未集成到 BarchartAPI
- 在 `get_commodity_price()` 中添加 `@rate_limit` 装饰器

### P2-03: Schema 缺少 CHECK 约束
- `price > 0`
- `stage_type IN ('保育','育肥','母猪',...)`

### P2-04: CHANGELOG 缺少 v1.6.2/v1.6.3 记录
- 补充变更日志

### P2-05: daily_price_update.sh 路径硬编码
- 将 `/home/kenny/.openclaw/workspace/` 改为相对路径或环境变量

---

## P3 — 可选优化

### P3-01: 类型注解完善
- 使用 TypedDict 定义 Formula、Ingredient 等数据结构

### P3-02: 魔法数字提取为常量
- `cache_size=10000` → `DEFAULT_CACHE_SIZE = 10000`

### P3-03: 测试断言添加详细消息
- `assert x is not None, f"期望非空，实际: {x}"`

---

## 修复顺序建议

```
Phase 1（阻塞解除，预计 6h）
├── P0-04 种子数据    ← 最优先，其他技能测试依赖
├── P0-01 SQL 字段名
├── P0-02 INSERT 缺字段
├── P0-03 方法名不匹配
├── P0-05 print→logging
├── P0-06 测试 fixture
├── P0-07 base_skill
└── P0-08 pytest-asyncio

Phase 2（核心功能，预计 10h）
├── P1-01/02 FormulaCostSkill 重构
├── P1-03/04 货币/原料名统一
├── P1-05 CustomerRecordSkill
├── P1-06 NutritionAnalysisSkill
└── P1-07 测试路径修复

Phase 3（质量提升，预计 8h）
├── P2 全部
└── P3 全部
```

---

## 修复后验证清单

```bash
# 1. 数据库初始化 + 种子数据
python scripts/init_database.py
sqlite3 data/feed_sales.db "SELECT COUNT(*) FROM formulas"
sqlite3 data/feed_sales.db "SELECT COUNT(*) FROM ingredient_prices"

# 2. 脚本执行
python scripts/update_prices.py
python scripts/scrape_formulas.py
python scripts/cleanup_duplicates.py

# 3. 全量测试
pip install pytest-asyncio
python -m pytest tests/ -v --tb=long

# 4. 技能 import
python -c "from skills.formula_cost_skill.skill import FormulaCostSkill"
python -c "from skills.price_lookup_skill.skill import PriceLookupSkill"
python -c "from skills.customer_record_skill.skill import CustomerRecordSkill"
python -c "from skills.nutrition_analysis_skill.skill import NutritionAnalysisSkill"

# 5. 日志检查（应无 print）
grep -rn "print(" src/ skills/ --include="*.py" | grep -v "__main__" | grep -v "# "
```

---

**文档生成**: Lucky  
**基于**: QA_TEST_REPORT_v1.6.3.md + CODE_REVIEW_v1.6.3.md
