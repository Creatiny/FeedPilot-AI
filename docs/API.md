# FeedSales AI MVP - API 文档

## 文档信息

| 项目 | 内容 |
|------|------|
| **版本** | v1.6.1 |
| **创建日期** | 2026-03-27 |
| **更新日期** | 2026-03-28 |
| **状态** | ✅ 完成 |

---

## 1. API 概览

### 1.1 架构说明

FeedSales AI 通过 OpenClaw Skill 系统提供 API 能力，所有 API 调用通过 OpenClaw Gateway 统一管理。

### 1.2 支持的平台

| 平台 | 状态 | 说明 |
|------|------|------|
| **Telegram Bot** | ✅ 支持 | 通过 OpenClaw Channel 集成 |
| **飞书 Bot** | ✅ 支持 | 通过 OpenClaw Channel 集成 |
| **OpenClaw CLI** | ✅ 支持 | 直接命令行调用 |
| **OpenClaw Web UI** | ✅ 支持 | 通过 Dashboard 调用 |

---

## 2. 技能 API

### 2.1 formula_cost_skill - 配方成本计算

#### 触发条件
- "成本计算"、"配方成本"、"多少钱"、"保育料成本"

#### 输入参数
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| formula_name | string | 是 | 配方名称 |
| owner_open_id | string | 自动 | 用户标识 |

#### 输出格式
```json
{
  "formula_name": "保育料 1 号",
  "cost_per_ton": 3500.50,
  "cost_per_kg": 3.50,
  "ingredients": [{"name": "玉米", "ratio": 60.0, "cost": 1680.00}]
}
```

---

## 3. 数据库 API

### 3.1 DatabasePool

#### get_connection() → sqlite3.Connection
获取数据库连接。

#### test_connection() → bool
测试数据库连接。

#### get_wal_path() → Path
获取 WAL 文件路径。

#### get_shm_path() → Path
获取 SHM 文件路径。

---

### 3.2 FormulaRepository

#### get_formula(owner_open_id, formula_name) → Optional[Dict]
获取用户专属配方。

**异常**: `ValueError` - 输入验证失败

#### list_formulas(owner_open_id) → List[Dict]
列出用户所有配方。

#### create_formula(owner_open_id, formula_data) → int
创建用户配方。

#### update_formula(owner_open_id, formula_id, formula_data) → bool
更新配方。

#### delete_formula(owner_open_id, formula_id) → bool
删除配方。

---

### 3.3 PriceRepository

#### get_latest_price(owner_open_id, ingredient_code) → Optional[Dict]
获取最新价格。

#### get_prices_by_date(owner_open_id, price_date) → List[Dict]
获取指定日期的所有价格。

#### save_price(owner_open_id, price_data) → int
保存价格。

---

## 4. 外部 API

### 4.1 Barchart API

#### BarchartAPIClient(api_key)

#### get_commodity_price(symbol) → Optional[Dict]
获取商品价格。

#### get_grain_prices() → List[Dict]
获取谷物价格列表。

#### convert_to_cny_ton(price_usd_bushel, commodity) → float
将 USD/蒲式耳 转换为 CNY/吨。

#### test_connection() → bool
测试 API 连接。

---

### 4.2 DashScope API

#### 配置
```bash
DASHSCOPE_API_KEY=sk-sp-xxx
```

#### 支持模型
| 模型 | 用途 | 成本 |
|------|------|------|
| qwen-max | 复杂任务 | 高 |
| qwen-plus | 日常任务 | 中 |
| qwen-turbo | 简单任务 | 低 |

---

## 5. 错误处理

### 5.1 错误码

| 错误码 | 说明 | 处理方案 |
|--------|------|---------|
| FORMULA_NOT_FOUND | 配方不存在 | 询问用户是否创建 |
| PRICE_FETCH_FAILED | 价格获取失败 | 降级到缓存 |
| DATABASE_ERROR | 数据库错误 | 记录日志 |
| API_RATE_LIMITED | API 限流 | 等待后重试 |

### 5.2 错误响应格式
```json
{
  "error": {
    "code": "FORMULA_NOT_FOUND",
    "message": "配方不存在",
    "suggestion": "您想创建新配方吗？"
  }
}
```

---

## 6. 安全说明

### 6.1 数据隔离
- 所有查询包含 `owner_open_id` 过滤
- 用户只能访问自己的数据

### 6.2 API Key 管理
- 存储在 `.env` 文件
- 不提交到 Git
- 通过 OpenClaw 配置注入

### 6.3 SQL 注入防护
- 使用参数化查询
- 不使用字符串拼接

---

## 7. 性能优化

### 7.1 数据库优化
- 启用 WAL 模式
- 使用连接池
- 添加索引优化

### 7.2 缓存策略
- 价格数据缓存 7 天
- 配方数据不缓存

---

## 8. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.6.1 | 2026-03-28 | 补充 API 参考文档 |
| v1.6.0 | 2026-03-27 | 初始版本 |

---

**文档结束**
