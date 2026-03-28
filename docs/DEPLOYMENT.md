# FeedSales AI - 生产环境部署指南

## 📋 概述

本文档总结从零开始部署 FeedSales AI 到生产环境的完整流程，包括所有已知问题和解决方案。

**适用场景**：全新服务器部署，确保一次部署成功，避免开发过程中遇到的所有问题。

---

## 🚀 快速部署（推荐）

### 前置要求

- OpenClaw 已安装并运行
- 服务器：Linux (Ubuntu 24.04+)
- 用户权限：普通用户 + sudo

### 一键部署脚本

```bash
#!/bin/bash
# FeedSales AI 生产环境部署脚本

set -e

echo "🚀 开始部署 FeedSales AI..."

# 1. 复制技能文件
echo "📦 复制技能文件..."
mkdir -p ~/.openclaw/workspace-feedsales/skills
cp -r ~/feed-sales-ai-mvp/skills/formula_cost_skill ~/.openclaw/workspace-feedsales/skills/
cp -r ~/feed-sales-ai-mvp/skills/price_lookup_skill ~/.openclaw/workspace-feedsales/skills/
cp -r ~/feed-sales-ai-mvp/skills/nutrition_analysis_skill ~/.openclaw/workspace-feedsales/skills/
cp -r ~/feed-sales-ai-mvp/skills/customer_record_skill ~/.openclaw/workspace-feedsales/skills/

# 2. 创建 FeedSales Agent
echo "🤖 创建 FeedSales Agent..."
openclaw agents add feedsales \
  --workspace ~/.openclaw/workspace-feedsales \
  --model modelstudio/qwen3.5-plus

# 3. 配置 Telegram Bot
echo "📱 配置 Telegram Bot..."
read -p "输入 Telegram Bot Token: " BOT_TOKEN
read -p "输入用户 Telegram ID: " USER_ID

openclaw config set --json channels.telegram "{
  \"enabled\": true,
  \"botToken\": \"$BOT_TOKEN\",
  \"allowFrom\": [$USER_ID],
  \"groupPolicy\": \"allowlist\",
  \"groupAllowFrom\": [$USER_ID],
  \"groups\": {\"*\": {\"requireMention\": true}},
  \"streaming\": \"partial\",
  \"proxy\": \"http://127.0.0.1:7897\"
}"

# 4. 绑定 Telegram 到 FeedSales Agent
echo "🔗 绑定 Telegram 到 FeedSales Agent..."
openclaw config set --json bindings "[{
  \"agentId\": \"feedsales\",
  \"match\": {
    \"channel\": \"telegram\",
    \"accountId\": \"default\"
  }
}]"

# 5. 配置 Agent 工具权限
echo "🔧 配置 Agent 工具权限..."
cat > ~/.openclaw/agents/feedsales/agent/tools.json << 'EOF'
{
  "allow": [
    "formula_cost_skill",
    "price_lookup_skill",
    "nutrition_analysis_skill",
    "customer_record_skill"
  ],
  "deny": [
    "exec",
    "shell",
    "bash",
    "skill",
    "update_superpowers_skills",
    "superpowers_version"
  ],
  "exec": {
    "enabled": false
  }
}
EOF

# 6. 更新 Agent IDENTITY
echo "📝 更新 Agent IDENTITY..."
cat > ~/.openclaw/agents/feedsales/agent/IDENTITY.md << 'EOF'
# 📊 FeedSales AI - 饲料配方成本计算专家

你是 FeedSales AI，专门帮助用户计算饲料配方成本和查询原料价格的专业助手。

## ⚠️ 重要规则

### 绝对禁止
- ❌ **禁止**让用户自己运行任何命令（SQL、shell、Python 等）
- ❌ **禁止**给用户 SQL 查询语句
- ❌ **禁止**说"你可以运行这个命令..."
- ❌ **禁止**说"要查询数据库，请运行..."

### 必须执行
- ✅ **直接**调用技能获取数据
- ✅ **直接**给出答案
- ✅ 如果技能失败，友好说明原因并提供帮助

## 核心能力

### 1. 配方成本计算
当用户询问配方成本时：
1. **立即调用** `formula_cost_skill` 技能
2. 等待技能返回结果
3. **直接格式化输出**成本信息

### 2. 原料价格查询
当用户询问原料价格时：
1. **立即调用** `price_lookup_skill` 技能
2. 等待技能返回结果
3. **直接格式化输出**价格信息

### 3. 价格更新
当用户要求更新价格时：
1. **立即调用**价格更新脚本
2. 等待执行结果
3. **直接报告**更新状态

## 响应原则

### 正确做法 ✅
```
用户：查询豆粕价格

[直接调用技能]

豆粕价格：
- $350.00/吨
- 2026-03-28
- CBOT
```

### 错误做法 ❌
```
用户：查询豆粕价格

你可以运行这个命令查询：
sqlite3 ~/.openclaw/workspace/... "SELECT * FROM ..."
```

## 技能列表

你拥有以下技能，**必须使用它们**：
- `formula_cost_skill` - 配方成本计算
- `price_lookup_skill` - 原料价格查询
- `nutrition_analysis_skill` - 营养分析
- `customer_record_skill` - 客户记录

## 故障处理

如果技能调用失败：
1. 道歉并说明原因
2. 提供替代方案
3. **不要**给用户 shell 命令

**示例**：
```
抱歉，暂时无法查询到价格数据。可能是数据库连接问题。请稍后再试或联系管理员。
```

## 记住

你的工作是**直接提供答案**，不是教用户如何查询数据库！
EOF

# 7. 更新 Agent 模型配置
echo "⚙️ 更新 Agent 模型配置..."
sed -i 's|"model": "modelstudio/glm-5"|"model": "modelstudio/qwen3.5-plus"|g' ~/.openclaw/openclaw.json

# 8. 重启 Gateway
echo "🔄 重启 Gateway..."
systemctl --user restart openclaw-gateway.service
sleep 5

# 9. 验证部署
echo "✅ 验证部署..."
openclaw status | grep -A5 "feedsales"

echo ""
echo "🎉 部署完成！"
echo ""
echo "📝 测试步骤："
echo "1. 在 Telegram 中发送 '玉米价格'"
echo "2. 在 Telegram 中发送 'Nursery Diet 1 成本'"
echo "3. 确认直接返回结果，没有 shell 命令"
echo ""
echo "🐛 如有问题，查看日志：journalctl --user -u openclaw-gateway -f"
```

---

## 📚 分步部署（详细版）

### 步骤 1：准备技能文件

**问题**：技能路径不能逃逸 workspace 根目录

**解决方案**：
```bash
# ❌ 错误：使用 symlink 会逃逸
ln -sf /home/kenny/.openclaw/workspace/feed-sales-ai-mvp/skills/xxx ~/.openclaw/workspace-feedsales/skills/

# ✅ 正确：直接复制文件
cp -r /home/kenny/.openclaw/workspace/feed-sales-ai-mvp/skills/xxx ~/.openclaw/workspace-feedsales/skills/
```

**验证**：
```bash
ls ~/.openclaw/workspace-feedsales/skills/
# 应该看到：
# - formula_cost_skill
# - price_lookup_skill
# - nutrition_analysis_skill
# - customer_record_skill
```

---

### 步骤 2：创建 FeedSales Agent

**命令**：
```bash
openclaw agents add feedsales \
  --workspace ~/.openclaw/workspace-feedsales \
  --model modelstudio/qwen3.5-plus
```

**验证**：
```bash
openclaw agents list | grep feedsales
```

---

### 步骤 3：配置 Telegram Bot

**获取 Bot Token**：
1. 在 Telegram 搜索 @BotFather
2. 发送 `/newbot`
3. 按提示设置名称和用户名
4. 保存 Bot Token

**获取用户 Telegram ID**：
1. 在 Telegram 搜索 @userinfobot
2. 发送任意消息
3. 保存返回的 ID

**配置命令**：
```bash
openclaw config set --json channels.telegram "{
  \"enabled\": true,
  \"botToken\": \"YOUR_BOT_TOKEN\",
  \"allowFrom\": [YOUR_USER_ID],
  \"groupPolicy\": \"allowlist\",
  \"groupAllowFrom\": [YOUR_USER_ID],
  \"groups\": {\"*\": {\"requireMention\": true}},
  \"streaming\": \"partial\",
  \"proxy\": \"http://127.0.0.1:7897\"
}"
```

---

### 步骤 4：绑定 Telegram 到 FeedSales Agent

**命令**：
```bash
openclaw config set --json bindings "[{
  \"agentId\": \"feedsales\",
  \"match\": {
    \"channel\": \"telegram\",
    \"accountId\": \"default\"
  }
}]"
```

**验证**：
```bash
openclaw status | grep -A3 "Telegram"
```

---

### 步骤 5：配置 Agent 工具权限

**问题**：Agent 默认有 exec 权限，会让用户运行 shell 命令

**解决方案**：创建 `tools.json` 禁用 exec

**文件**：`~/.openclaw/agents/feedsales/agent/tools.json`

```json
{
  "allow": [
    "formula_cost_skill",
    "price_lookup_skill",
    "nutrition_analysis_skill",
    "customer_record_skill"
  ],
  "deny": [
    "exec",
    "shell",
    "bash",
    "skill",
    "update_superpowers_skills",
    "superpowers_version"
  ],
  "exec": {
    "enabled": false
  }
}
```

---

### 步骤 6：配置 Agent IDENTITY

**问题**：Agent 不知道应该直接调用技能，而是给用户 shell 命令

**解决方案**：明确禁止给命令，强制直接回答

**文件**：`~/.openclaw/agents/feedsales/agent/IDENTITY.md`

**关键内容**：
```markdown
## ⚠️ 重要规则

### 绝对禁止
- ❌ **禁止**让用户自己运行任何命令（SQL、shell、Python 等）
- ❌ **禁止**给用户 SQL 查询语句
- ❌ **禁止**说"你可以运行这个命令..."

### 必须执行
- ✅ **直接**调用技能获取数据
- ✅ **直接**给出答案
```

---

### 步骤 7：更新 Agent 模型

**命令**：
```bash
sed -i 's|"model": "modelstudio/glm-5"|"model": "modelstudio/qwen3.5-plus"|g' ~/.openclaw/openclaw.json
```

**验证**：
```bash
cat ~/.openclaw/openclaw.json | python3 -c "import sys,json; d=json.load(sys.stdin); agents=d.get('agents',{}).get('list',[]); print([a['model'] for a in agents if a.get('id')=='feedsales'])"
```

---

### 步骤 8：重启 Gateway

**命令**：
```bash
systemctl --user restart openclaw-gateway.service
sleep 5
```

**验证**：
```bash
systemctl --user status openclaw-gateway.service
```

---

### 步骤 9：测试验证

**测试命令**（在 Telegram 中）：
1. "玉米价格" - 应该直接返回价格
2. "Nursery Diet 1 成本" - 应该直接计算成本
3. "更新价格" - 应该直接调用更新脚本

**预期结果**：
- ✅ 直接返回答案
- ❌ 不给任何 shell/SQL 命令

---

## 🐛 已知问题和解决方案

### 问题 1：技能路径逃逸

**错误信息**：
```
Detected workspace `skills/**/SKILL.md` paths whose realpath escapes their workspace root
```

**原因**：使用 symlink 链接技能文件

**解决方案**：
```bash
# 删除 symlink
rm -rf ~/.openclaw/workspace-feedsales/skills

# 重新复制
mkdir -p ~/.openclaw/workspace-feedsales/skills
cp -r ~/feed-sales-ai-mvp/skills/* ~/.openclaw/workspace-feedsales/skills/
```

---

### 问题 2：Agent 给用户 shell 命令

**现象**：Agent 回复"你可以运行这个 SQL 命令..."

**原因**：
1. tools.json 没有禁用 exec
2. IDENTITY.md 没有明确禁止

**解决方案**：
1. 创建 `tools.json` 禁用 exec
2. 更新 `IDENTITY.md` 明确规则
3. 重启 Gateway

---

### 问题 3：Agent 使用错误的模型

**现象**：Agent 使用 glm-5 而不是 qwen3.5-plus

**原因**：创建 Agent 时默认使用 glm-5

**解决方案**：
```bash
sed -i 's|"model": "modelstudio/glm-5"|"model": "modelstudio/qwen3.5-plus"|g' ~/.openclaw/openclaw.json
systemctl --user restart openclaw-gateway.service
```

---

### 问题 4：Telegram Bot 不响应

**检查清单**：
1. Bot Token 是否正确
2. 用户 ID 是否在 allowFrom 列表
3. Gateway 是否运行
4. Telegram 通道是否启用

**调试命令**：
```bash
# 检查 Gateway 状态
systemctl --user status openclaw-gateway.service

# 检查配置
openclaw status | grep -A5 "Telegram"

# 查看日志
journalctl --user -u openclaw-gateway -f
```

---

## 📊 配置验证清单

部署完成后，运行以下验证：

```bash
# 1. 检查 Agent 配置
echo "=== Agent 配置 ==="
openclaw agents list | grep -A5 "feedsales"

# 2. 检查技能文件
echo "=== 技能文件 ==="
ls ~/.openclaw/workspace-feedsales/skills/

# 3. 检查工具权限
echo "=== 工具权限 ==="
cat ~/.openclaw/agents/feedsales/agent/tools.json

# 4. 检查 Telegram 配置
echo "=== Telegram 配置 ==="
openclaw status | grep -A5 "Telegram"

# 5. 检查模型配置
echo "=== 模型配置 ==="
cat ~/.openclaw/openclaw.json | python3 -c "import sys,json; d=json.load(sys.stdin); print([a for a in d.get('agents',{}).get('list',[]) if a.get('id')=='feedsales'])"
```

---

## 🔧 故障排查

### Gateway 无法启动

```bash
# 查看详细错误
journalctl --user -u openclaw-gateway -n 50 --no-pager

# 检查配置语法
cat ~/.openclaw/openclaw.json | python3 -m json.tool

# 重启服务
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway.service
```

### 技能不加载

```bash
# 检查技能路径
ls -la ~/.openclaw/workspace-feedsales/skills/

# 检查 SKILL.md 是否存在
find ~/.openclaw/workspace-feedsales/skills/ -name "SKILL.md"

# 查看技能加载日志
journalctl --user -u openclaw-gateway -f | grep -i skill
```

### Agent 不响应

```bash
# 检查 Agent 状态
openclaw agents list

# 检查绑定关系
openclaw status | grep -A10 "Sessions"

# 查看会话日志
journalctl --user -u openclaw-gateway -f | grep -i feedsales
```

---

## 📝 维护指南

### 日常维护

```bash
# 查看服务状态
systemctl --user status openclaw-gateway.service

# 查看日志
journalctl --user -u openclaw-gateway -n 100 --no-pager

# 重启服务
systemctl --user restart openclaw-gateway.service
```

### 技能更新

```bash
# 1. 更新技能文件
cp -r ~/feed-sales-ai-mvp/skills/xxx ~/.openclaw/workspace-feedsales/skills/

# 2. 重启 Gateway
systemctl --user restart openclaw-gateway.service
```

### 配置备份

```bash
# 备份配置
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d)

# 恢复配置
cp ~/.openclaw/openclaw.json.backup.YYYYMMDD ~/.openclaw/openclaw.json
systemctl --user restart openclaw-gateway.service
```

---

## 🎯 性能优化

### 数据库优化

```bash
# 定期清理旧会话
sqlite3 ~/.openclaw/workspace-feedsales/data.db "DELETE FROM sessions WHERE last_access < datetime('now', '-30 days');"

# 优化数据库
sqlite3 ~/.openclaw/workspace-feedsales/data.db "VACUUM;"
```

### 日志轮转

```bash
# 创建日志轮转配置
cat > /etc/systemd/system/openclaw-gateway.service.d/log-rotate.conf << 'EOF'
[Service]
StandardOutput=journal
StandardError=journal
EOF

systemctl --user daemon-reload
```

---

## 📞 技术支持

### 日志位置

```bash
# Gateway 日志
journalctl --user -u openclaw-gateway -f

# 系统日志
journalctl -f | grep openclaw
```

### 常见问题

- **技能不加载**：检查路径和 SKILL.md
- **Agent 不响应**：检查绑定和模型配置
- **Telegram 不工作**：检查 Token 和 allowFrom

### 获取帮助

1. 查看日志
2. 检查配置
3. 重启服务
4. 联系技术支持

---

## 📚 参考文档

- [OpenClaw 官方文档](https://docs.openclaw.ai/)
- [OpenClaw 技能开发](https://docs.openclaw.ai/skills/)
- [OpenClaw Agent 配置](https://docs.openclaw.ai/agents/)

---

**最后更新**：2026-03-28  
**版本**：1.0  
**适用版本**：OpenClaw 2026.3.24+
