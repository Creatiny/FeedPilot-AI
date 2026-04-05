# FeedSales AI MVP v1.6 - 文档索引

## 📚 文档列表

### 核心文档（已完成）

| 文档 | 路径 | 状态 | 说明 |
|------|------|------|------|
| **ARCHITECTURE_v1.6.md** | [docs/ARCHITECTURE_v1.6.md](./docs/ARCHITECTURE_v1.6.md) | ✅ 完成 | 系统架构设计方案 |
| **DEVELOPMENT_TASKS_v1.6.md** | [docs/DEVELOPMENT_TASKS_v1.6.md](./docs/DEVELOPMENT_TASKS_v1.6.md) | ✅ 完成 | 开发任务清单 |

### 缺失文档（待创建）

| 文档 | 路径 | 状态 | 任务 ID |
|------|------|------|--------|
| **API.md** | docs/API.md | ❌ 缺失 | T16 |
| **DEPLOYMENT.md** | docs/DEPLOYMENT.md | ❌ 缺失 | T17 |
| **USER_GUIDE.md** | docs/USER_GUIDE.md | ❌ 缺失 | T18 |
| **CHANGELOG.md** | docs/CHANGELOG.md | ❌ 缺失 | T19 |

---

## 📋 ARCHITECTURE_v1.6.md 内容概要

### 1. 执行摘要
- 架构决策背景
- v1.6 核心变更
- v1.5 vs v1.6 架构对比

### 2. 架构决策总结
- 已确认的架构决策（7 项）
- 架构简化对比图

### 3. 系统架构详述
- 整体架构图
- 技能目录结构（OpenClaw 3.24 标准）
- SKILL.md 标准格式（3.3 节）
  - formula_cost_skill/SKILL.md 示例
  - 其他技能结构

### 4. 数据库设计
- SQLite Schema（WAL 模式）
- DatabasePool 实现
- Repository 层实现

### 5. 开发任务清单
- P0 任务（10 个，22.5 小时）
- P1 任务（5 个，18 小时）
- P2 任务（6 个，16 小时）

### 6. 开发计划
- 时间安排（2 周周期）
- 里程碑（4 个）

### 7. 测试策略
- 测试范围
- 关键测试场景

### 8. 部署配置
- 环境变量（.env.example）
- Docker Compose（可选）

### 9. 风险评估
- 5 项风险及缓解措施

### 10. 验收标准
- 功能验收
- 性能验收
- 代码质量
- 文档验收

### 11. 附录
- 参考文档
- 相关文件
- 版本历史

---

## 📋 DEVELOPMENT_TASKS_v1.6.md 内容概要

### 1. 任务总览
- 任务分类表
- 里程碑图

### 2. P0 任务详情（10 个）
- T01: 修复 Git 远程配置 ✅
- T02: 删除 `agent/` 目录 ✅
- T03: 实现 DatabasePool 📋
- T04: 实现 Repository 层 📋
- T05: 创建 SQLite Schema 📋
- T06: 实现多租户隔离 📋
- T07: 配置 OpenClaw Triggers 📋
- T08: 完善 SKILL.md 格式 📋
- T09: 删除 llm_extractor.py 📋
- T10: 迁移 JSON 数据到 SQLite 📋

每个任务包含：
- 状态、工作量、优先级
- 子任务分解
- 实现步骤（含代码示例）
- 验收标准

### 3. P1 任务详情（5 个）
- T11: Barchart API 集成
- T12: OpenClaw LLM 测试
- T13: 错误处理装饰器
- T14: Rate Limiter 实现
- T15: 补充单元测试

### 4. P2 任务详情（6 个）
- T16-T21: 文档和测试

### 5. 任务进度跟踪
- 燃尽图
- 每日站会模板

### 6. 变更日志

---

## 🎯 下一步行动

### 立即执行（今天）

1. **审查文档**
   - 阅读 ARCHITECTURE_v1.6.md
   - 确认架构决策
   - 提出修改意见

2. **准备开发环境**
   ```bash
   # 确认 Git 配置
   git remote -v
   
   # 确认 Python 环境
   python3 --version
   
   # 安装依赖
   pip install -r requirements.txt
   ```

### 本周完成

1. **实现 P0 任务**
   - T03: DatabasePool（3h）
   - T04: Repository 层（4h）
   - T05: SQLite Schema（2h）

2. **创建缺失文档**
   - API.md（T16）
   - DEPLOYMENT.md（T17）

### 下周完成

1. **完成剩余 P0 任务**
   - T06-T10

2. **开始 P1 任务**
   - T11: Barchart API 集成

---

## 📞 联系方式

- **项目仓库**: https://gitee.com/kenny-chenym/feed-sales-ai-mvp
- **文档问题**: 在仓库中提 Issue
- **架构讨论**: 飞书群聊

---

**最后更新**: 2026-03-27  
**版本**: v1.6.0
