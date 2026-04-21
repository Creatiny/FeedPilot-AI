# FeedSales AI v1.7 全场景测试用例方案

> 目标：覆盖所有业务场景和饲料种类，支持中文自然语言输入，支持 Telegram 自动化测试

---

## 1. 测试范围矩阵

### 1.1 业务场景
| 场景 | 覆盖内容 |
|------|----------|
| 配方成本查询 | 公共配方、私有配方、混合价格来源 |
| 私有配方管理 | 创建、修改、删除、列表 |
| 私有价格管理 | 设置、查询、列表 |
| 客户管理 | 创建、查询、更新、删除 |
| 报价生成 | 选择客户 + 配方 → 生成报价 |
| 营养分析 | 配方营养成分、NRC 对比 |

### 1.2 饲料种类
| 动物类型 | 饲养阶段 | 典型配方名 |
|----------|----------|-----------|
| Swine | Nursery | 保育料 1 号、Nursery Diet 1 |
| Swine | Growing | 生长猪料、Growing Diet |
| Swine | Finishing | 育肥料、Finishing Diet |
| Beef Cattle | Starter | 肉牛开食料 |
| Beef Cattle | Growing | 肉牛生长期料 |
| Beef Cattle | Finishing | 肉牛育肥料 |
| Dairy Cattle | Calf | 犊牛料 |
| Dairy Cattle | Heifer | 育成牛料 |
| Dairy Cattle | Lactating | 泌乳牛料 |
| Broiler | Starter | 肉鸡开食料 |
| Broiler | Grower | 肉鸡生长期料 |
| Broiler | Finisher | 肉鸡育肥料 |
| Layer | Starter | 蛋鸡开食料 |
| Layer | Grower | 蛋鸡生长期料 |
| Layer | Laying | 产蛋期料 |

### 1.3 语言模式
| 模式 | 示例 |
|------|------|
| 中文简体 | 计算保育料 1 号成本 |
| 中文口语化 | 保育料多少钱一吨 |
| 中英混合 | 计算 Nursery Diet 1 的成本 |
| 英文 | Calculate Nursery Diet 1 cost |

---

## 2. 测试用例设计

### 2.1 配方成本查询（核心场景）

#### TC-01：公共配方成本查询
```
输入：计算保育料 1 号的成本
预期：
- 成功返回成本结果
- 配方来源：public
- 价格来源：public
- 总成本 > 0
```

#### TC-02：私有配方成本查询
```
前置：用户已创建私有配方"我的保育料"
输入：计算我的保育料成本
预期：
- 成功返回成本结果
- 配方来源：private
```

#### TC-03：私有价格覆盖
```
前置：
- 公共配方：Nursery Diet 1
- 用户设置私有玉米价格：175 USD/ton
输入：计算 Nursery Diet 1 成本
预期：
- 玉米使用私有价格
- 价格来源：private
```

#### TC-04：混合价格来源
```
前置：
- 用户设置玉米私有价格
- 其他原料使用公共价格
输入：计算保育料成本
预期：
- 玉米：private
- 豆粕：public
- 价格来源汇总正确
```

#### TC-05：缺失价格处理
```
前置：某原料无价格数据
输入：计算包含缺失原料的配方成本
预期：
- 返回默认价格
- 标记 missing_prices
```

#### TC-06：不存在的配方
```
输入：计算不存在的配方成本
预期：
- 返回 E002 错误
- 错误信息：配方不存在
```

---

### 2.2 私有配方管理

#### TC-07：创建私有配方
```
输入：创建我的保育料配方，玉米60%，豆粕25%，预混料15%
预期：
- 创建成功
- 返回配方 ID
- 配方归属当前用户
```

#### TC-08：查看私有配方列表
```
输入：列出我的所有配方
预期：
- 返回用户私有配方列表
- 不包含其他用户的配方
```

#### TC-09：修改私有配方
```
前置：用户有私有配方"我的保育料"
输入：修改我的保育料，把豆粕改成20%
预期：
- 修改成功
- 豆粕比例 = 20%
```

#### TC-10：删除私有配方
```
前置：用户有私有配方"测试配方"
输入：删除我的测试配方
预期：
- 删除成功
- 再次查询返回不存在
```

---

### 2.3 私有价格管理

#### TC-11：设置私有价格
```
输入：设置我的玉米价格 175 美元
预期：
- 设置成功
- 下次查询使用私有价格
```

#### TC-12：查看私有价格列表
```
输入：列出我的私有价格
预期：
- 返回用户设置的私有价格列表
```

#### TC-13：价格隔离
```
前置：
- 用户 A 设置玉米价格 175
- 用户 B 设置玉米价格 180
输入：(用户 B) 查询玉米价格
预期：
- 用户 B 返回 180
- 不受用户 A 影响
```

---

### 2.4 客户管理

#### TC-14：创建客户
```
输入：添加客户张三，电话 13800138000
预期：
- 创建成功
- 客户归属当前用户
```

#### TC-15：查看客户列表
```
输入：列出我的客户
预期：
- 返回当前用户的客户列表
```

#### TC-16：客户隔离
```
前置：用户 A 有客户"李四"
输入：(用户 B) 查询客户李四
预期：
- 返回不存在
- 用户 B 无法看到用户 A 的客户
```

---

### 2.5 多语言测试

#### TC-17：中文口语化
```
输入：保育料多少钱一吨
预期：
- 识别为成本查询
- 返回成本结果
```

#### TC-18：中英混合
```
输入：计算 Nursery Diet 1 的成本
预期：
- 识别配方名
- 返回成本结果
```

#### TC-19：英文输入
```
输入：Calculate Nursery Diet 1 cost
预期：
- 识别配方名
- 返回成本结果
```

---

### 2.6 饲料种类覆盖测试

#### TC-20~TC-35：各动物类型成本查询
```
TC-20: 计算 Swine Nursery 成本
TC-21: 计算 Swine Growing 成本
TC-22: 计算 Swine Finishing 成本
TC-23: 计算 Beef Cattle Starter 成本
TC-24: 计算 Beef Cattle Growing 成本
TC-25: 计算 Beef Cattle Finishing 成本
TC-26: 计算 Dairy Cattle Calf 成本
TC-27: 计算 Dairy Cattle Heifer 成本
TC-28: 计算 Dairy Cattle Lactating 成本
TC-29: 计算 Broiler Starter 成本
TC-30: 计算 Broiler Grower 成本
TC-31: 计算 Broiler Finisher 成本
TC-32: 计算 Layer Starter 成本
TC-33: 计算 Layer Grower 成本
TC-34: 计算 Layer Laying 成本
TC-35: 计算不存在的配方（错误处理）
```

---

## 3. Telegram 自动化测试方案

### 3.1 方案概述

使用 Python + pytest + python-telegram-bot 实现自动化测试：

```
┌─────────────────────────────────┐
│      测试脚本 (pytest)           │
│  test_telegram_e2e.py           │
└─────────────────────────────────┘
              ↓
┌─────────────────────────┐
│  Telegram Bot API       │
│  sendMessage / getUpdates │
└─────────────────────────┘
              ↓
┌─────────────────────────┐
│  FeedSalesHarness       │
│  (生产环境)              │
└─────────────────────────┘
```

### 3.2 实现方案

#### 安装依赖
```bash
pip install pytest python-telegram-bot pytest-asyncio
```

#### 测试脚本框架
```python
# tests/test_telegram_e2e.py
import pytest
import asyncio
from telegram import Bot
from telegram.ext import Application
import os

# 配置
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TEST_CHAT_ID = os.getenv('TELEGRAM_TEST_CHAT_ID')  # 测试用户/群组 ID

class TelegramTestClient:
    """Telegram 测试客户端"""
    
    def __init__(self, token: str, chat_id: str):
        self.bot = Bot(token)
        self.chat_id = chat_id
        self.last_message_id = None
    
    async def send_message(self, text: str):
        """发送消息"""
        msg = await self.bot.send_message(
            chat_id=self.chat_id,
            text=text
        )
        self.last_message_id = msg.message_id
        return msg
    
    async def get_response(self, timeout: int = 30):
        """获取回复"""
        updates = await self.bot.get_updates(
            offset=-1,
            timeout=timeout,
            allowed_updates=['message']
        )
        
        for update in updates:
            if update.message and update.message.reply_to_message:
                if update.message.reply_to_message.message_id == self.last_message_id:
                    return update.message.text
        
        return None


@pytest.fixture
def telegram_client():
    """Telegram 客户端 fixture"""
    return TelegramTestClient(BOT_TOKEN, TEST_CHAT_ID)


# ========== 测试用例 ==========

@pytest.mark.asyncio
async def test_formula_cost_query_public(telegram_client):
    """测试公共配方成本查询"""
    # 发送消息
    await telegram_client.send_message("计算 Nursery Diet 1 的成本")
    
    # 获取回复
    response = await telegram_client.get_response()
    
    # 验证
    assert response is not None
    assert "成本" in response or "cost" in response.lower()
    assert "$" in response or "USD" in response


@pytest.mark.asyncio
async def test_set_private_price(telegram_client):
    """测试设置私有价格"""
    await telegram_client.send_message("设置我的玉米价格 175")
    response = await telegram_client.get_response()
    
    assert response is not None
    assert "成功" in response or "设置" in response


@pytest.mark.asyncio
async def test_create_customer(telegram_client):
    """测试创建客户"""
    await telegram_client.send_message("添加客户测试用户，电话 123456")
    response = await telegram_client.get_response()
    
    assert response is not None
    assert "成功" in response or "客户" in response


@pytest.mark.asyncio
async def test_swine_nursery_cost(telegram_client):
    """测试 Swine Nursery 成本"""
    await telegram_client.send_message("计算保育料 1 号成本")
    response = await telegram_client.get_response()
    
    assert response is not None
    assert "$" in response


@pytest.mark.asyncio
async def test_chinese_colloquial(telegram_client):
    """测试中文口语化"""
    await telegram_client.send_message("保育料多少钱一吨")
    response = await telegram_client.get_response()
    
    assert response is not None
```

### 3.3 测试执行

```bash
# 设置环境变量
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_TEST_CHAT_ID="your_test_chat_id"

# 运行测试
pytest tests/test_telegram_e2e.py -v

# 运行特定测试
pytest tests/test_telegram_e2e.py::test_formula_cost_query_public -v
```

### 3.4 CI/CD 集成

```yaml
# .github/workflows/telegram-e2e.yml
name: Telegram E2E Tests

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install pytest python-telegram-bot pytest-asyncio
    
    - name: Run Telegram E2E Tests
      env:
        TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
        TELEGRAM_TEST_CHAT_ID: ${{ secrets.TELEGRAM_TEST_CHAT_ID }}
      run: |
        pytest tests/test_telegram_e2e.py -v --tb=short
```

---

## 4. 测试数据准备

### 4.1 测试用户
```
用户 A: test_user_a (Telegram ID: xxx)
用户 B: test_user_b (Telegram ID: yyy)
```

### 4.2 测试配方
```
公共配方：
- Nursery Diet 1 (Swine Nursery)
- Growing Diet (Swine Growing)
- Finishing Diet (Swine Finishing)

私有配方（测试用）：
- 我的保育料 (用户 A)
- 测试育肥料 (用户 B)
```

### 4.3 测试价格
```
公共价格：
- Corn: 180 USD/ton
- Soybean meal: 350 USD/ton
- Premix: 450 USD/ton

私有价格（测试用）：
- 用户 A 玉米: 175 USD/ton
- 用户 B 玉米: 185 USD/ton
```

---

## 5. 测试用例总表

| ID | 场景 | 输入 | 预期结果 |
|----|------|------|----------|
| TC-01 | 公共配方成本 | 计算保育料 1 号的成本 | 成功，来源 public |
| TC-02 | 私有配方成本 | 计算我的保育料成本 | 成功，来源 private |
| TC-03 | 私有价格覆盖 | 设置玉米价格后查询成本 | 使用私有价格 |
| TC-04 | 混合价格来源 | 部分私有部分公共 | 来源汇总正确 |
| TC-05 | 缺失价格 | 缺失原料配方 | 使用默认价格 |
| TC-06 | 不存在配方 | 不存在的配方 | E002 错误 |
| TC-07 | 创建配方 | 创建我的保育料配方 | 创建成功 |
| TC-08 | 列出配方 | 列出我的所有配方 | 返回私有列表 |
| TC-09 | 修改配方 | 修改豆粕比例 | 修改成功 |
| TC-10 | 删除配方 | 删除测试配方 | 删除成功 |
| TC-11 | 设置价格 | 设置玉米价格 175 | 设置成功 |
| TC-12 | 列出价格 | 列出我的私有价格 | 返回列表 |
| TC-13 | 价格隔离 | 不同用户同原料 | 各自价格隔离 |
| TC-14 | 创建客户 | 添加客户张三 | 创建成功 |
| TC-15 | 列出客户 | 列出我的客户 | 返回列表 |
| TC-16 | 客户隔离 | 不同用户同客户名 | 各自隔离 |
| TC-17 | 中文口语 | 保育料多少钱一吨 | 识别并返回 |
| TC-18 | 中英混合 | 计算 Nursery Diet 1 成本 | 识别并返回 |
| TC-19 | 英文输入 | Calculate Nursery Diet 1 cost | 识别并返回 |
| TC-20~35 | 各动物类型 | 各阶段配方成本查询 | 成功返回 |

**合计：35 个测试用例**

---

## 6. 结论

本方案覆盖：
- ✅ 6 大业务场景
- ✅ 16 种饲料类型
- ✅ 4 种语言模式
- ✅ 35 个测试用例
- ✅ Telegram 自动化测试框架
- ✅ CI/CD 集成方案

### 下一步
1. 实现测试脚本 `tests/test_telegram_e2e.py`
2. 配置测试用户和数据
3. 集成到 CI/CD 流程