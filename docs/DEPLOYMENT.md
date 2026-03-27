# FeedSales AI MVP - 部署手册

## 文档信息

| 项目 | 内容 |
|------|------|
| **版本** | v1.6.0 |
| **创建日期** | 2026-03-27 |
| **状态** | 📋 草稿 |
| **作者** | Kenny Chen |

---

## 1. 部署方式

### 1.1 部署架构

```
┌─────────────────────────────────────────┐
│         用户设备                         │
│  - Telegram App                         │
│  - 飞书 App                              │
└─────────────────┬───────────────────────┘
                  │ Internet
┌─────────────────▼───────────────────────┐
│         OpenClaw Gateway                 │
│  - 端口：18789                           │
│  - 进程：openclaw gateway                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         FeedSales AI Skills              │
│  - formula_cost_skill                    │
│  - price_lookup_skill                    │
│  - customer_record_skill                 │
│  - nutrition_analysis_skill              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         SQLite Database (WAL)            │
│  - data/feed_sales.db                   │
│  - data/feed_sales.db-wal               │
│  - data/feed_sales.db-shm               │
└─────────────────────────────────────────┘
```

### 1.2 部署选项

| 选项 | 适用场景 | 复杂度 |
|------|---------|--------|
| **本地部署** | 开发/测试 | 低 |
| **VPS 部署** | 生产环境 | 中 |
| **Docker 部署** | 容器化环境 | 中 |

---

## 2. 前置要求

### 2.1 系统要求

| 组件 | 版本 | 说明 |
|------|------|------|
| **操作系统** | Linux/macOS | Ubuntu 22.04+ 推荐 |
| **Python** | 3.10+ | 必需 |
| **Node.js** | 22+ | OpenClaw 依赖 |
| **Git** | 任意 | 代码管理 |

### 2.2 账号要求

| 服务 | 用途 | 必需 |
|------|------|------|
| **阿里云 DashScope** | LLM API | ✅ |
| **Barchart** | 价格数据 | ✅ |
| **Telegram Bot** | 消息通道 | ✅ |
| **飞书 Bot** | 消息通道 | 可选 |

---

## 3. 本地部署（开发环境）

### 3.1 安装 OpenClaw

```bash
# 使用 npm 全局安装
npm install -g openclaw

# 验证安装
openclaw --version
# 应显示：OpenClaw 2026.3.24
```

### 3.2 克隆项目

```bash
# 克隆代码
git clone git@gitee.com:kenny-chenym/feed-sales-ai-mvp.git
cd feed-sales-ai-mvp

# 确认目录结构
ls -la
# 应包含：skills/, src/, data/, docs/
```

### 3.3 安装 Python 依赖

```bash
# 创建虚拟环境（可选）
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3.4 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env
```

**.env 内容**：
```bash
# OpenClaw 配置
OPENCLAW_WORKSPACE=/home/kenny/.openclaw/workspace

# DashScope API Key（LLM）
DASHSCOPE_API_KEY=sk-sp-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Barchart API Key（价格数据）
BARCHART_API_KEY=your_barchart_api_key

# 数据库配置
DATABASE_URL=sqlite:///data/feed_sales.db

# Telegram Bot Token（可选，OpenClaw 已提供）
TELEGRAM_BOT_TOKEN=xxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxx

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/feed_sales.log
```

### 3.5 初始化数据库

```bash
# 创建数据目录
mkdir -p data

# 初始化数据库
python3 scripts/init_database.py

# 验证数据库
ls -la data/
# 应包含：feed_sales.db, feed_sales.db-wal, feed_sales.db-shm
```

### 3.6 启动 OpenClaw Gateway

```bash
# 启动 Gateway
openclaw gateway start

# 检查状态
openclaw gateway status

# 查看日志
openclaw logs --follow
```

### 3.7 验证部署

```bash
# 健康检查
curl http://localhost:18789/health

# 应返回：{"status":"healthy"}
```

---

## 4. VPS 部署（生产环境）

### 4.1 服务器要求

| 配置 | 要求 | 说明 |
|------|------|------|
| **CPU** | 1 核+ | 基础需求 |
| **内存** | 2GB+ | 推荐 4GB |
| **存储** | 20GB+ | SSD 推荐 |
| **带宽** | 1Mbps+ | 根据用户量调整 |

### 4.2 安装步骤

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# 3. 安装 Python
sudo apt install -y python3 python3-pip python3-venv

# 4. 安装 OpenClaw
sudo npm install -g openclaw

# 5. 克隆项目
cd /opt
sudo git clone git@gitee.com:kenny-chenym/feed-sales-ai-mvp.git
sudo chown -R $USER:$USER feed-sales-ai-mvp
cd feed-sales-ai-mvp

# 6. 安装依赖
pip3 install -r requirements.txt

# 7. 配置环境变量
cp .env.example .env
nano .env  # 填写实际配置

# 8. 初始化数据库
mkdir -p data
python3 scripts/init_database.py

# 9. 配置 systemd 服务
sudo nano /etc/systemd/system/feed-sales-ai.service
```

**systemd 服务配置**：
```ini
[Unit]
Description=FeedSales AI MVP
After=network.target

[Service]
Type=simple
User=kenny
WorkingDirectory=/opt/feed-sales-ai-mvp
Environment="PATH=/opt/feed-sales-ai-mvp/.venv/bin"
ExecStart=/opt/feed-sales-ai-mvp/.venv/bin/python -m openclaw gateway
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启动服务**：
```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable feed-sales-ai

# 启动服务
sudo systemctl start feed-sales-ai

# 检查状态
sudo systemctl status feed-sales-ai
```

### 4.3 配置防火墙

```bash
# 允许 OpenClaw 端口
sudo ufw allow 18789/tcp

# 如果需要 Web UI
sudo ufw allow 18789

# 检查防火墙状态
sudo ufw status
```

### 4.4 配置 Nginx（可选）

```bash
# 安装 Nginx
sudo apt install -y nginx

# 配置反向代理
sudo nano /etc/nginx/sites-available/feed-sales-ai
```

**Nginx 配置**：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:18789;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**启用配置**：
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/feed-sales-ai /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

---

## 5. Docker 部署

### 5.1 创建 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装 Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
RUN apt-get install -y nodejs

# 安装 OpenClaw
RUN npm install -g openclaw

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p data logs

# 启动命令
CMD ["openclaw", "gateway"]
```

### 5.2 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  feed-sales-ai:
    build: .
    container_name: feed-sales-ai-v1.6
    ports:
      - "18789:18789"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - BARCHART_API_KEY=${BARCHART_API_KEY}
      - DATABASE_URL=sqlite:///data/feed_sales.db
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ~/.openclaw:/root/.openclaw
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18789/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 5.3 启动 Docker

```bash
# 构建镜像
docker-compose build

# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查状态
docker-compose ps
```

---

## 6. 配置 Telegram Bot

### 6.1 创建 Bot

1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot`
3. 输入 Bot 名称：FeedSales AI Assistant
4. 输入 Bot 用户名：feedsales_ai_bot
5. 保存 Token

### 6.2 配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "YOUR_BOT_TOKEN"
    }
  }
}
```

### 6.3 重启 Gateway

```bash
openclaw gateway restart
```

---

## 7. 配置飞书 Bot

### 7.1 创建飞书应用

1. 访问 https://open.feishu.cn/app
2. 创建企业自建应用
3. 获取 App ID 和 App Secret

### 7.2 配置 OpenClaw

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_xxxxxxxxxxxxx",
      "appSecret": "xxxxxxxxxxxxxxxx"
    }
  }
}
```

---

## 8. 监控和日志

### 8.1 查看日志

```bash
# OpenClaw 日志
openclaw logs --follow

# 系统日志
sudo journalctl -u feed-sales-ai -f

# Docker 日志
docker-compose logs -f
```

### 8.2 健康检查

```bash
# HTTP 健康检查
curl http://localhost:18789/health

# systemd 状态
sudo systemctl status feed-sales-ai

# Docker 状态
docker-compose ps
```

### 8.3 性能监控

```bash
# CPU 使用
top -p $(pgrep -f openclaw)

# 内存使用
free -h

# 磁盘使用
df -h data/
```

---

## 9. 备份和恢复

### 9.1 数据库备份

```bash
# 备份数据库
cp data/feed_sales.db data/feed_sales.db.backup.$(date +%Y%m%d)
cp data/feed_sales.db-wal data/feed_sales.db-wal.backup.$(date +%Y%m%d)

# 压缩备份
tar -czf feed-sales-backup-$(date +%Y%m%d).tar.gz data/
```

### 9.2 数据库恢复

```bash
# 停止服务
openclaw gateway stop

# 恢复数据库
cp data/feed_sales.db.backup.20260327 data/feed_sales.db

# 启动服务
openclaw gateway start
```

---

## 10. 故障排查

### 10.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| Gateway 无法启动 | 端口被占用 | `lsof -i :18789` 检查端口 |
| 数据库错误 | 权限问题 | `chmod 644 data/*.db` |
| API 调用失败 | Key 配置错误 | 检查 .env 文件 |
| Bot 无响应 | Channel 未启用 | 检查 openclaw.json |

### 10.2 调试模式

```bash
# 启用调试日志
export LOG_LEVEL=DEBUG

# 重启 Gateway
openclaw gateway restart

# 查看详细日志
openclaw logs --follow | grep DEBUG
```

---

## 11. 版本升级

### 11.1 备份数据

```bash
# 备份数据库
cp -r data/ data.backup.$(date +%Y%m%d)

# 备份配置
cp .env .env.backup.$(date +%Y%m%d)
```

### 11.2 升级代码

```bash
# 拉取最新代码
git pull origin master

# 安装新依赖
pip install -r requirements.txt --upgrade

# 数据库迁移（如有）
python3 scripts/migrate_database.py
```

### 11.3 重启服务

```bash
# systemd
sudo systemctl restart feed-sales-ai

# Docker
docker-compose restart

# 本地
openclaw gateway restart
```

---

## 12. 安全检查清单

- [ ] API Key 未提交到 Git
- [ ] 数据库文件权限正确（644）
- [ ] 防火墙配置正确
- [ ] 使用 HTTPS（生产环境）
- [ ] 定期备份数据库
- [ ] 监控系统资源使用
- [ ] 更新系统和依赖

---

## 13. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.6.0 | 2026-03-27 | 初始版本 |

---

**文档结束**
