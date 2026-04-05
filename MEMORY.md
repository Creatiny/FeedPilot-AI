# MEMORY.md - FeedSales AI 长期记忆

## 🎯 身份定位

**我是 FeedPilot AI**，北美饲料配方成本计算助手。

## 👤 用户信息

- **姓名**: Kenny
- **时区**: Asia/Shanghai (GMT+8)
- **语言**: 中文

## 🖥️ 技术配置

### 模型配置

| 模型 | 用途 | Provider |
|------|------|----------|
| mimo-v2-pro | 首选 | OpenRouter |
| qwen3-max | 备用 | DashScope |

### 数据库

- **类型**: SQLite (WAL 模式)
- **位置**: `data/feed_sales.db`
- **表**: ingredient_prices, formulas, formula_ingredients, customers, users, reminders

### Telegram Bot

- **Bot Token**: `8755704577:AAEZ_K0Y07_SA7jAmF6g3qpQjjXenjlCsKQ`
- **Agent ID**: `feedsales`

## 📁 项目结构

```
~/.openclaw/workspace-feedsales/
├── AGENTS.md          # Agent 定义
├── USER.md            # 用户画像
├── MEMORY.md          # 长期记忆
├── data/
│   ├── feed_sales.db  # 主数据库
│   └── authorized.json # 授权用户
├── scripts/           # 工具脚本
├── skills/            # 技能目录
│   ├── price_lookup_skill/
│   ├── formula_cost_skill/
│   ├── customer_record_skill/
│   ├── nutrition_analysis_skill/
│   └── reminder_skill/
└── src/
    ├── database/      # 数据库层
    ├── services/      # 服务层
    └── utils/         # 工具
```

## 🔗 相关链接

### 代码仓库
- **Gitee**: https://gitee.com/kenny-chenym/feed-sales-ai-mvp
- **本地路径**: `~/.openclaw/workspace-feedsales/`

### 数据源
- **CBOT**: 芝加哥期货交易所 (期货价格)
- **USDA NASS**: 美国农业部 (现货价格)

## 📊 业务数据

### 配方 (38 个)

| 类型 | 数量 | 示例 |
|------|------|------|
| 保育料 | 6 | Nursery Diet 1-6 |
| 生长料 | 6 | Grower Diet 1-6 |
| 育肥料 | 6 | Finishing Diet 1-6 |
| 肉鸡料 | 8 | Broiler Starter/Grower/Finisher |
| 蛋鸡料 | 6 | Layer Diet 1-6 |
| 肉牛料 | 6 | Beef Cattle Starter/Finisher |

### 原料 (13+ 种)

| 原料 | 代码 | 来源 |
|------|------|------|
| 豆粕 48% | ING_SBM_48 | CBOT |
| 玉米 | ING_CORN | CBOT |
| 鱼粉 65% | ING_FISH_65 | USDA |
| DDGS 28% | ING_DDGS_28 | USDA |

## 🤖 功能模块

### 已实现
- ✅ 价格查询 (price_lookup_skill)
- ✅ 配方成本计算 (formula_cost_skill)
- ✅ 客户管理 (customer_record_skill)
- ✅ 营养分析 (nutrition_analysis_skill)
- ✅ 价格提醒 (reminder_skill) - 支持用户隔离

### 定时任务
- 每日 8:00 AM (Chicago) 更新价格
- 每日 8:00 AM (Chicago) 检查价格提醒

## 🔑 关键决策

1. **数据库**: SQLite WAL 模式，单文件，易备份
2. **服务层**: 统一使用 ServiceResult 返回类型
3. **用户隔离**: 通过 user_id 字段实现
4. **价格单位**: USD/ton (美元/吨)

## 📝 Cron 任务

| 任务 ID | 名称 | 时间 |
|---------|------|------|
| d73fe845-... | Check All User Reminders | 每日 8:00 AM Chicago |

---

**最后更新**: 2026-04-05  
**身份**: FeedPilot AI  
**版本**: v1.0
