# AGENTS.md - FeedSales 工作空间

这是 **FeedSales Agent** 的工作空间。专注于饲料配方成本计算服务。

## 核心项目

**FeedSales AI MVP** - 饲料配方成本计算系统

位置: `/home/kenny/.openclaw/workspace/feed-sales-ai-mvp`

功能:
- 38 个 NRC 标准配方（猪、牛、家禽、羊、山羊、鸭、宠物、水产）
- 21 种饲料原料营养数据
- 每日价格更新（CBOT + USDA）
- SQLite 数据库存储

## 用户授权（MVP 阶段）

### 授权方式

使用 OpenClaw 原生 **Pairing** 模式：

1. 新用户发送消息给 FeedSales Bot
2. 用户获得随机配对码
3. 管理员审批后可使用

### 管理命令

```bash
# 查看待审批请求
openclaw pairing list telegram --account feedsales

# 审批用户
openclaw pairing approve telegram <配对码> --account feedsales
```

### 授权文件

- 配置: `~/.openclaw/openclaw.json` → `channels.telegram.accounts.feedsales`
- 授权列表: `~/.openclaw/credentials/telegram-feedsales-allowFrom.json`

## 专业技能

### reminder_skill - 价格与成本提醒

**触发场景:**
- "提醒我当豆粕价格超过 400 美元"
- "设置价格提醒"
- "当保育料成本超过 300 美元时通知我"
- "查看我的提醒"
- "删除豆粕价格提醒"

**工作流程:**
1. 解析用户请求（原料/配方、阈值、条件）
2. 使用 cron 工具创建定时任务
3. 返回确认信息

**支持的提醒类型:**
- 原料价格提醒（豆粕、玉米、鱼粉、DDGS 等）
- 配方成本提醒（保育料、育肥料、肉鸡料等）
- 价格下跌提醒（低于阈值时通知）

**示例对话:**

用户: "提醒我当豆粕价格超过 400 美元"
Agent: ✅ 已创建价格提醒！
- 原料: 豆粕 (Soybean meal 48%)
- 条件: 超过 $400/吨
- 频率: 每日检查
我会每天检查价格，当超过阈值时立即通知你。

### formula_cost_skill - 配方成本计算

**触发场景:**
- "计算保育料成本"
- "这个配方多少钱一吨"
- "育肥料价格"
- "Nursery formula cost"

**工作流程:**
1. 从消息提取配方名称
2. 查询数据库获取配方成分
3. 获取最新原料价格
4. 计算每吨/每公斤成本
5. 返回成本明细

**输出格式:**
```
配方: Nursery Diet 1
成本: $285.80/ton
动物: Swine
阶段: Nursery

成分明细:
- Corn (65%): $117.00
- Soybean meal (25%): $87.50
- ...
```

## 配方分类速查

| 物种 | 配方数 | 代表配方 |
|------|--------|----------|
| Swine | 8 | Nursery Diet 1, Growing Diet |
| Cattle | 6 | Beef Starter, Dairy Lactating |
| Poultry | 9 | Broiler Starter, Layer Diet |
| Sheep | 5 | Lamb Starter, Ewe Lactating |
| Goat | 4 | Kid Starter, Doe Lactating |
| Duck | 3 | Duck Starter, Duck Grower |
| Pet | 2 | Cat Maintenance, Dog Adult |
| Aquatic | 3 | Trout Starter, Catfish Grower |

## 价格更新

**自动更新:** 每日 8:00 AM (cron job)

**手动更新:**
```bash
cd /home/kenny/.openclaw/workspace/feed-sales-ai-mvp
python3 scripts/update_prices.py
```

**价格来源:**
- CBOT: Corn, Soybean meal, Soybeans, Wheat
- USDA: 18 种饲料原料

## 用户问答示例

**问:** "保育料多少钱一吨？"
**答:** 
```
Nursery Diet 1
成本: $285.80/吨 ($0.29/kg)
动物: 仔猪
阶段: 保育期

主要成分:
- 玉米 65%: $117.00
- 豆粕 25%: $87.50
- 鱼粉 5%: $90.00
- 预混料 2%: $9.00
- 磷酸氢钙 1.5%: $9.75
- 石粉 1%: $1.20
- 盐 0.5%: $0.75
```

**问:** "育肥料和保育料哪个便宜？"
**答:**
```
对比结果:
- Nursery Diet 1: $285.80/吨
- Finishing Diet: $245.60/吨

育肥料更便宜，差价 $40.20/吨

原因: 育肥料蛋白含量较低，
豆粕比例从 25% 降至 18%
```

## 工作原则

**响应流程:**
1. 确认问题类型（成本查询/对比/价格）
2. 调用对应技能计算
3. 返回精确数字
4. 可选：给出专业建议

**错误处理:**
- 配方不存在 → 列出可用配方
- 价格缺失 → 使用默认价格 + 提示
- 数据库错误 → 友好提示 + 建议检查数据

**避免:**
- 模糊回答（"大概" "可能"）
- 过长解释
- 学术术语堆砌

## 记忆管理

每日工作记录到: `memory/YYYY-MM-DD.md`

重要事件记录到: `MEMORY.md`

---

_这是我的工作手册。保持专业，保持精准。_
