# FeedSales AI v1.6.3 QA 测试报告

## 测试概要

- **测试时间**: 2026-03-28 23:06 GMT+8
- **测试环境**: Linux 5.15.0-100-generic (x64), Python 3.10.12
- **总用例数**: 21
- **通过**: 14
- **失败**: 4
- **错误**: 3
- **通过率**: 66.67%

---

## 单元测试结果

| 文件 | 用例数 | 通过 | 失败/错误 | 备注 |
|------|--------|------|-----------|------|
| test_database.py | 3 | 1 | 2 ERROR | fixture 'pool' 未定义 |
| test_formula_skill_db.py | 1 | 0 | 1 FAILED | async 测试缺少 pytest-asyncio |
| test_mock.py | 4 | 4 | 0 | ✅ 全部通过 |
| test_multi_tenant.py | 2 | 1 | 1 FAILED | ModuleNotFoundError: skills.base_skill |
| test_openclaw_llm.py | 2 | 2 | 0 | ✅ 全部通过 |
| test_p0_complete.py | 4 | 3 | 1 ERROR | fixture 'pool' 未定义 |
| test_p1_tasks.py | 3 | 3 | 0 | ✅ 全部通过 |
| test_skills_real.py | 2 | 0 | 2 FAILED | async 测试缺少 pytest-asyncio |
| test_e2e_full.py | 0 | - | - | 无测试函数（测试类有 __init__） |
| test_integration.py | 0 | - | - | 无测试函数（测试类有 __init__） |
| test_performance.py | 0 | - | - | 未执行（无显式测试） |

### 失败详情

**FAILED tests/test_formula_skill_db.py::test_skill**
```
async def functions are not natively supported.
需要安装 pytest-asyncio 插件
```

**FAILED tests/test_multi_tenant.py::test_owner_open_id_fallback**
```
ModuleNotFoundError: No module named 'skills.base_skill'
```

**FAILED tests/test_skills_real.py::test_formula_cost_skill**
```
async def functions are not natively supported.
```

**FAILED tests/test_skills_real.py::test_price_lookup_skill**
```
async def functions are not natively supported.
```

**ERROR tests/test_database.py::test_formula_repository**
```
fixture 'pool' not found
```

**ERROR tests/test_database.py::test_price_repository**
```
fixture 'pool' not found
```

**ERROR tests/test_p0_complete.py::test_repository**
```
fixture 'pool' not found
```

---

## 技能实测结果

### skills/formula_cost_skill/skill.py

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 文件存在 | ✅ PASS | 6344 bytes, 存在 |
| 语法正确 | ✅ PASS | `import FormulaCostSkill` 成功 |
| 函数完整性 | ✅ PASS | execute(), _extract_formula_name(), _calculate_cost() 等方法完整 |
| SKILL.md 工作流 | ⚠️ PARTIAL | 未完全实现 SKILL.md 要求（缺少价格查询技能调用） |
| 错误处理 | ✅ PASS | 有 try-except 和 _error() 方法 |
| 硬编码问题 | ⚠️ P1 | 默认价格硬编码，货币单位不一致（USD vs CNY） |

**实测执行结果**:
```python
result = await skill.execute('test_user', 'Calculate Nursery Diet 1 cost')
# 输出: {'success': False, 'error': 'Formula not found: Nursery Diet 1'}
```
- 原因: 数据库无配方数据（migrate_data_to_db.py 失败）

### skills/price_lookup_skill/skill.py

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 文件存在 | ✅ PASS | 2954 bytes, 存在 |
| 语法正确 | ✅ PASS | `import PriceLookupSkill` 成功 |
| 函数完整性 | ⚠️ PARTIAL | execute() 完整，但依赖 price_repo 未初始化 |
| SKILL.md 工作流 | ⚠️ PARTIAL | 简化实现，缺少数据库查询逻辑 |
| 错误处理 | ✅ PASS | 有 try-except 和 _error() 方法 |
| 硬编码问题 | ❌ P0 | 使用中文原料名（玉米、豆粕），与数据库英文原料名不一致；硬编码人民币价格 |

### skills/customer_record_skill/skill.py

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 文件存在 | ✅ PASS | 1654 bytes, 存在 |
| 语法正确 | ✅ PASS | `import CustomerRecordSkill` 成功 |
| 函数完整性 | ❌ P1 | execute() 只返回占位消息 "客户记录功能开发中" |
| SKILL.md 工作流 | ❌ FAIL | 未实现任何实际功能 |
| 错误处理 | ✅ PASS | 有 try-except 和 _error() 方法 |
| 硬编码问题 | N/A | 无实际逻辑 |

### skills/nutrition_analysis_skill/skill.py

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 文件存在 | ✅ PASS | 1636 bytes, 存在 |
| 语法正确 | ✅ PASS | `import NutritionAnalysisSkill` 成功 |
| 函数完整性 | ❌ P1 | execute() 只返回占位消息 "营养分析功能开发中" |
| SKILL.md 工作流 | ❌ FAIL | 未实现任何实际功能 |
| 错误处理 | ✅ PASS | 有 try-except 和 _error() 方法 |
| 硬编码问题 | N/A | 无实际逻辑 |

---

## 数据库完整性测试

### Schema 分析

| 表 | 字段数 | 索引数 | owner_open_id | 状态 |
|----|--------|--------|---------------|------|
| users | 5 | 1 (PRIMARY) | ✅ open_id | 正常 |
| ingredient_prices | 9 | 2 | ✅ owner_open_id | 正常 |
| formulas | 7 | 2 | ✅ owner_open_id | 正常 |
| formula_ingredients | 4 | 1 | ❌ 无 | 通过 formula_id FK |
| customers | 9 | 1 | ✅ owner_open_id | 正常 |
| calculation_history | 8 | 2 | ✅ owner_open_id | 正常 |

### 数据完整性

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 表结构完整 | ✅ PASS | 7 表全部存在 |
| 索引优化 | ✅ PASS | 每表有合理索引 |
| 外键约束 | ✅ PASS | formula_ingredients → formulas ON DELETE CASCADE |
| 多租户隔离 | ✅ PASS | 5 表有 owner_open_id |
| 初始数据 | ❌ P0 | 数据库空：0 formulas, 0 prices, 0 customers |

### Schema 与代码不一致

| 问题 | 位置 | 影响 |
|------|------|------|
| `date` vs `price_date` | update_prices.py, cleanup_duplicates.py, FormulaCostSkill | SQL 执行失败 |
| `stage` vs `stage_type` | FormulaCostSkill._calculate_cost() | 字段不存在 |
| `animal_category` 缺失 | Schema formulas 表无此字段，但 skill.py 使用 | 返回 None |

---

## 新增脚本测试

### scripts/update_prices.py

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 文件存在 | ✅ PASS | 10660 bytes |
| 语法正确 | ✅ PASS | 无语法错误 |
| SQL 正确性 | ❌ P0 | 使用 `date` 字段，应为 `price_date` |
| INSERT 缺少字段 | ❌ P0 | 缺少 `owner_open_id`（多租户必须） |
| ON CONFLICT 不匹配 | ❌ P0 | UNIQUE 约束是 (ingredient_code, price_date, owner_open_id)，INSERT 用 (ingredient_name, date) |

**执行结果**: 
```
sqlite3.OperationalError: table ingredient_prices has no column named date
```

### scripts/scrape_formulas.py

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 文件存在 | ✅ PASS | 5699 bytes |
| 语法正确 | ✅ PASS | 无语法错误 |
| 方法名不一致 | ❌ P0 | main() 调用不存在的方法 |
| 具体问题 | ❌ P0 | `scrape_standard_formulas()` 应为 `scrape_nrc_formulas()` |
| | ❌ P0 | `scrape_ingredient_nutrition()` 应为 `scrape_usda_nutrition()` |
| | ❌ P0 | `scrape_ingredient_prices()` 应为 `scrape_us_prices()` |

**执行结果**:
```
AttributeError: 'FeedFormulaScraper' object has no attribute 'scrape_standard_formulas'
```

### scripts/daily_price_update.sh

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 文件存在 | ✅ PASS | 468 bytes |
| 可执行权限 | ✅ PASS | -rwxr-xr-x |
| 路径硬编码 | ⚠️ P1 | `/home/kenny/.openclaw/workspace/` 不可移植 |
| logs 目录 | ⚠️ P2 | logs/ 目录不存在，写入会失败 |

### scripts/cleanup_duplicates.py

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 文件存在 | ✅ PASS | 1914 bytes |
| 语法正确 | ✅ PASS | 无语法错误 |
| SQL 字段错误 | ❌ P0 | 使用 `date` 字段，应为 `price_date` |

**执行结果**:
```
sqlite3.OperationalError: no such column: date
```

### scripts/migrate_data_to_db.py

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 文件存在 | ✅ PASS | 5615 bytes |
| 语法正确 | ✅ PASS | 无语法错误 |
| 数据文件缺失 | ❌ P0 | `data/nrc_formulas_full.json` 不存在 |

**执行结果**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/nrc_formulas_full.json'
```

---

## 回归验证（对照 v1.6.1 P0）

### P0-01: 4 个 skill.py 是否存在且可运行

| 技能 | v1.6.1 状态 | v1.6.3 状态 | 结论 |
|------|-------------|-------------|------|
| formula_cost_skill/skill.py | ❌ 缺失 | ✅ 存在，可 import | ✅ PASS |
| price_lookup_skill/skill.py | ❌ 缺失 | ✅ 存在，可 import | ✅ PASS |
| customer_record_skill/skill.py | ❌ 缺失 | ✅ 存在，可 import | ✅ PASS |
| nutrition_analysis_skill/skill.py | ❌ 缺失 | ✅ 存在，可 import | ✅ PASS |

**结论**: ✅ 已修复

### P0-02: BarchartAPI 是否改用 logging（不再用 print）

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 使用 logging | ⚠️ PARTIAL | 类方法使用 logging.getLogger() |
| print 语句残留 | ❌ P0 | 7 处 print 语句残留 (行 89, 93, 96, 161-168) |

**详细分析**:
- 第 89, 93, 96 行：错误处理中的 `print()` 应改为 `logger.error()`
- 第 161-168 行：`__main__` 演示中的 `print()` 可保留（非生产代码）

**结论**: ⚠️ 未完全修复

### P0-03: DatabasePool 线程安全是否修复

| 检查项 | 结果 | 详情 |
|--------|------|------|
| 单例模式 | ✅ PASS | 使用 `__new__` + `_lock` 实现单例 |
| 线程本地存储 | ✅ PASS | 使用 `threading.local()` |
| WAL 模式 | ✅ PASS | `PRAGMA journal_mode=WAL` |
| 连接管理 | ✅ PASS | `@contextmanager get_connection()` |

**结论**: ✅ 已修复

### P0-04: Repository 输入验证是否完善

| 检查项 | 结果 | 详情 |
|--------|------|------|
| validate_owner_open_id() | ✅ PASS | 检查非空和长度限制 |
| validate_formula_name() | ✅ PASS | 检查非空和长度限制 |
| ValueError 抛出 | ✅ PASS | 验证失败抛出异常 |
| 覆盖范围 | ⚠️ P1 | 仅覆盖 FormulaRepository，PriceRepository 未验证 |

**结论**: ✅ 基本修复

---

## 发现的问题

### P0 级别（Critical - 阻塞发布）

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| P0-01 | SQL 字段名错误：`date` 应为 `price_date` | update_prices.py, cleanup_duplicates.py, FormulaCostSkill | 所有脚本执行失败 |
| P0-02 | INSERT 缺少 `owner_open_id` | update_prices.py | 多租户数据无法插入 |
| P0-03 | 方法名不匹配 | scrape_formulas.py main() | 脚本无法运行 |
| P0-04 | 数据文件缺失 | data/nrc_formulas_full.json | 数据迁移失败 |
| P0-05 | BarchartAPI print 语句残留 | barchart_api.py 第 89-96 行 | 错误日志无法收集 |
| P0-06 | 测试 fixture 未定义 | test_database.py, test_p0_complete.py | 3 个测试 ERROR |
| P0-07 | skills.base_skill 模块缺失 | test_multi_tenant.py | 测试失败 |
| P0-08 | async 测试无 pytest-asyncio | 4 个 async 测试 | 测试失败 |

### P1 级别（Major - 影响核心功能）

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| P1-01 | CustomerRecordSkill 未实现 | skill.py execute() | 功能不可用 |
| P1-02 | NutritionAnalysisSkill 未实现 | skill.py execute() | 功能不可用 |
| P1-03 | 硬编码默认价格 | FormulaCostSkill._get_default_price() | 价格不准确 |
| P1-04 | 中文原料名 vs 英文数据库 | PriceLookupSkill | 查询失败 |
| P1-05 | 货币单位不一致 | FormulaCostSkill(USD) vs PriceLookupSkill(CNY) | 成本计算错误 |
| P1-06 | PriceRepository 无输入验证 | repository.py | 潜在 SQL 注入风险 |
| P1-07 | 路径硬编码 | daily_price_update.sh | 不可移植 |

### P2 级别（Minor - 建议改进）

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| P2-01 | logs 目录不存在 | daily_price_update.sh | 日志写入失败 |
| P2-02 | Schema 缺少 animal_category | formulas 表 | 无法按动物分类 |
| P2-03 | Schema stage vs stage_type 不一致 | formulas 表 vs skill.py | 字段名混乱 |
| P2-04 | 测试函数返回非 None | 多个测试文件 | pytest 警告 |
| P2-05 | 测试类有 __init__ | test_integration.py, test_e2e_full.py | 无法收集测试 |

### P3 级别（Enhancement - 可选优化）

| ID | 问题 | 位置 | 影响 |
|----|------|------|------|
| P3-01 | 无 requirements.txt | 项目根目录 | 依赖管理困难 |
| P3-02 | FormulaCostSkill 不调用 PriceLookupSkill | skill.py | 未按 SKILL.md 工作流 |
| P3-03 | 演示数据全部硬编码 | update_prices.py, scrape_formulas.py | 非真实数据 |

---

## 测试结论

### FAIL - 不符合发布标准

**理由**:
1. **8 个 P0 问题阻塞核心功能**：所有数据脚本无法运行，数据库无数据
2. **单元测试通过率 66.67%**：未达到 80% 最低标准
3. **技能实测全部失败**：因数据库无数据，技能无法执行实际计算
4. **回归验证未完全通过**：BarchartAPI print 语句残留，新增 SQL 错误

**必须修复项** (P0):
- [ ] 修复 SQL 字段名：`date` → `price_date`
- [ ] 添加 `owner_open_id` 到 INSERT 语句
- [ ] 修复 scrape_formulas.py 方法名
- [ ] 创建或迁移数据文件
- [ ] 替换 BarchartAPI print 为 logging
- [ ] 添加 pytest fixture 定义
- [ ] 创建 skills.base_skill 模块或删除相关测试
- [ ] 安装 pytest-asyncio

**推荐修复项** (P1):
- [ ] 实现 CustomerRecordSkill 和 NutritionAnalysisSkill
- [ ] 统一货币单位（USD 或 CNY）
- [ ] 统一原料名称（英文或中文）
- [ ] 添加 PriceRepository 输入验证

---

## 附录

### 测试执行命令

```bash
# 环境准备
cd /root/.openclaw/workspace/feed-sales-ai-mvp
python3 scripts/init_database.py

# 单元测试
python3 -m pytest tests/ -v --tb=long

# 技能语法检查
python3 -c "from skills.formula_cost_skill.skill import FormulaCostSkill"
python3 -c "from skills.price_lookup_skill.skill import PriceLookupSkill"
python3 -c "from skills.customer_record_skill.skill import CustomerRecordSkill"
python3 -c "from skills.nutrition_analysis_skill.skill import NutritionAnalysisSkill"

# 脚本执行测试
python3 scripts/update_prices.py
python3 scripts/scrape_formulas.py
python3 scripts/migrate_data_to_db.py
python3 scripts/cleanup_duplicates.py
```

### 数据库 Schema 查询

```python
import sqlite3
conn = sqlite3.connect('data/feed_sales.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for table in tables:
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"Table: {table[0]}")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
```

---

**测试工程师**: QA Auditor  
**测试日期**: 2026-03-28  
**报告版本**: 1.0  
**项目版本**: v1.6.3