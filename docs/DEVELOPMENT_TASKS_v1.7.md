# FeedSales AI MVP v1.7 - Harness 版本规划

## 版本信息

| 项目 | 内容 |
|------|------|
| **版本** | v1.7.0 (Harness Layer) |
| **前置版本** | v1.6.0 (已完成) |
| **预计周期** | 2 周 |
| **预计工作量** | 40 小时 |
| **状态** | 📋 规划中 |

---

## 🎯 版本目标

### 核心目标

**在现有 Single Skill 外围新增 4 层薄 Harness**：
1. Input Guard - 输入守门
2. Execution Guard - 执行守门
3. Evaluator - 结果评估
4. Trace Store - 轨迹记录

### 不做的内容

- ❌ 不改写为多 Agent 架构
- ❌ 不复杂长期记忆
- ❌ 不把 Harness 写成另一个 Skill

---

## 📐 架构设计

### v1.6 架构（当前）

```
Telegram / OpenClaw Runtime
 → FormulaCostSkill.execute()
   → LLMExtractor (占位)
   → BarchartAPI (占位)
   → ErrorHandler (已有)
```

### v1.7 架构（目标）

```
Telegram / OpenClaw Runtime
 → Harness Input Guard
   → 意图识别 (formula_name | custom_ratio | price_query | recommendation)
   → 输入校验
 → FormulaCostSkill Core Logic (不变)
   → Harness Execution Guard
     → LLMExtractor (包装)
     → BarchartAPI (包装)
   → Harness Evaluator
     → 配方提取评估
     → 价格结果评估
     → 成本结果评估
 → Harness Trace Store
   → 执行轨迹记录
   → 为 v1.8 SQLite 持久化做准备
```

---

## 📁 文件结构

### 新增文件

```
skills/formula_cost_skill/harness/
├── __init__.py
├── input_guard.py        # 输入守门
├── execution_guard.py    # 执行守门
├── evaluator.py          # 结果评估
├── trace_store.py        # 轨迹记录
└── schemas.py            # 标准结构定义
```

### 修改文件

```
skills/formula_cost_skill/
├── skill.py              # 接入 Harness 层
└── tests/
    ├── test_harness/
    │   ├── test_input_guard.py
    │   ├── test_execution_guard.py
    │   ├── test_evaluator.py
    │   └── test_trace_store.py
    └── test_integration_v1.7.py
```

### 暂不改动

- `llm_extractor.py` - 只被包装，不改主体逻辑
- `barchart_api.py` - 只被包装，不改主体逻辑
- `error_handler.py` - 保留，Harness 与其协作

---

## 📋 任务清单

### P0: Harness 核心层（16 小时）

| 任务 ID | 任务名称 | 工作量 | 优先级 |
|--------|---------|-------|--------|
| **H01** | schemas.py - 标准结构定义 | 2h | P0 |
| **H02** | input_guard.py - 输入守门 | 4h | P0 |
| **H03** | execution_guard.py - 执行守门 | 4h | P0 |
| **H04** | evaluator.py - 结果评估 | 4h | P0 |
| **H05** | trace_store.py - 轨迹记录 | 2h | P0 |

### P1: Skill 接入（8 小时）

| 任务 ID | 任务名称 | 工作量 | 优先级 |
|--------|---------|-------|--------|
| **H06** | skill.py 接入 Harness 层 | 4h | P0 |
| **H07** | 现有测试适配 v1.7 | 2h | P1 |
| **H08** | Harness 单元测试 | 2h | P1 |

### P2: 集成测试（8 小时）

| 任务 ID | 任务名称 | 工作量 | 优先级 |
|--------|---------|-------|--------|
| **H09** | Telegram 渠道集成测试 | 3h | P1 |
| **H10** | SQLite 持久化准备 | 3h | P2 |
| **H11** | Owner 隔离适配 | 2h | P2 |

### P3: 文档（8 小时）

| 任务 ID | 任务名称 | 工作量 | 优先级 |
|--------|---------|-------|--------|
| **H12** | Harness 设计文档 | 3h | P1 |
| **H13** | API 文档更新 | 2h | P1 |
| **H14** | 用户手册更新 | 2h | P1 |
| **H15** | CHANGELOG v1.7 | 1h | P1 |

---

## 🔍 详细设计

### H01: schemas.py

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ParsedRequest:
    """解析后的请求对象"""
    request_type: str  # formula_name | custom_ratio | price_query | recommendation | unknown
    raw_message: str
    normalized_message: str
    formula_name: Optional[str]
    custom_ratio_text: Optional[str]
    weight_kg: Optional[float]
    ingredient: Optional[str]
    needs_llm: bool
    valid: bool

@dataclass
class ToolResult:
    """工具执行结果"""
    ok: bool
    source: str  # qwen | barchart | local_cache | json | fallback
    degraded: bool
    data: Optional[Dict[str, Any]]
    error_code: Optional[str]
    error_message: Optional[str]

@dataclass
class EvalResult:
    """评估结果"""
    pass_: bool
    user_message: str
    user_payload: Dict[str, Any]
    details: Dict[str, Any]

@dataclass
class Trace:
    """执行轨迹"""
    trace_id: str
    user_id: str
    raw_message: str
    stages: list
    start_time: float
    end_time: Optional[float]
    error: Optional[str]
```

### H02: input_guard.py

```python
class InputGuard:
    """输入守门员"""
    
    def parse(self, message: str) -> ParsedRequest:
        """解析用户消息"""
        # 意图识别
        # 输入校验
        # 结构化请求对象生成
        pass
    
    def validate_formula_name(self, name: str) -> bool:
        """校验配方名称"""
        pass
    
    def validate_custom_ratio(self, text: str) -> bool:
        """校验自定义配比"""
        pass
```

### H03: execution_guard.py

```python
class ExecutionGuard:
    """执行守门员"""
    
    async def extract_formula(
        self, 
        llm_extractor, 
        text: str
    ) -> ToolResult:
        """包装 LLM 配方提取"""
        try:
            result = await llm_extractor.extract(text)
            return ToolResult(ok=True, source="qwen", degraded=False, data=result)
        except Exception as e:
            return ToolResult(ok=False, source="qwen", degraded=True, 
                           error_code="ERR_LLM_FAILED", error_message=str(e))
    
    async def fetch_price(
        self, 
        barchart_api, 
        ingredient: str
    ) -> ToolResult:
        """包装 Barchart 价格获取"""
        try:
            price = barchart_api.get_price(ingredient)
            return ToolResult(ok=True, source="barchart", degraded=False, 
                           data={"price": price})
        except Exception as e:
            # 降级到本地缓存
            cached_price = self._get_cached_price(ingredient)
            if cached_price:
                return ToolResult(ok=True, source="local_cache", degraded=True, 
                               data={"price": cached_price})
            return ToolResult(ok=False, source="barchart", degraded=True, 
                           error_code="ERR_PRICE_MISSING", error_message=str(e))
```

### H04: evaluator.py

```python
class Evaluator:
    """结果评估器"""
    
    def evaluate_formula_extraction(self, result: ToolResult) -> EvalResult:
        """评估配方提取结果"""
        if not result.ok:
            return EvalResult(pass_=False, user_message="配方提取失败", ...)
        
        # 置信度检查
        if result.data.get("confidence", 0) < 0.80:
            return EvalResult(pass_=False, 
                           user_message="配方提取置信度不足，请明确配方名称", ...)
        
        # 空结果检查
        if not result.data.get("ingredients"):
            return EvalResult(pass_=False, 
                           user_message="未提取到有效原料", ...)
        
        return EvalResult(pass_=True, user_message="提取成功", 
                         user_payload=result.data)
    
    def evaluate_price_result(self, result: ToolResult) -> EvalResult:
        """评估价格结果"""
        if not result.ok:
            return EvalResult(pass_=False, user_message="价格获取失败", ...)
        
        # 降级标记
        metadata = {"data_source": result.source, "degraded": result.degraded}
        
        return EvalResult(pass_=True, user_message="价格查询成功", 
                         user_payload={**result.data, "metadata": metadata})
    
    def evaluate_ratio(self, formula: dict) -> EvalResult:
        """评估配比合法性"""
        ratio_sum = sum(ing["ratio"] for ing in formula["ingredients"])
        if not 99.9 <= ratio_sum <= 100.1:
            return EvalResult(pass_=False, 
                           user_message=f"配比不合法 ({ratio_sum}%), 请确保总和为 100%", ...)
        return EvalResult(pass_=True, user_message="配比合法", ...)
```

### H05: trace_store.py

```python
class TraceStore:
    """轨迹存储"""
    
    def start_trace(self, user_id: str, raw_message: str) -> Trace:
        """开始轨迹记录"""
        trace = Trace(
            trace_id=generate_id(),
            user_id=user_id,
            raw_message=raw_message,
            stages=[],
            start_time=time.time(),
            end_time=None,
            error=None
        )
        return trace
    
    def record_stage(self, trace: Trace, stage_name: str, data: Any):
        """记录阶段数据"""
        trace.stages.append({
            "name": stage_name,
            "data": data,
            "timestamp": time.time()
        })
    
    def record_error(self, trace: Trace, error: Exception):
        """记录错误"""
        trace.error = str(error)
        trace.end_time = time.time()
    
    def save_trace(self, trace: Trace):
        """保存轨迹（v1.8 持久化到 SQLite）"""
        # v1.7: 仅内存存储
        # v1.8: 持久化到 SQLite，挂 owner_open_id
        pass
```

### H06: skill.py 接入

```python
async def execute(self, user_id: str, message: str) -> Dict[str, Any]:
    """执行技能（v1.7 Harness 版本）"""
    # 开始轨迹记录
    trace = self.trace_store.start_trace(user_id=user_id, raw_message=message)
    
    try:
        # 1. 输入守门
        req = self.input_guard.parse(message)
        self.trace_store.record_stage(trace, "input_parsed", req)
        
        if not req.valid:
            return self._error("输入格式无效")
        
        # 2. 根据请求类型执行
        if req.request_type == "formula_name":
            formula = self._get_formula_from_db(req.formula_name)
            
        elif req.request_type == "custom_ratio":
            llm_result = await self.execution_guard.extract_formula(
                self.llm_extractor, req.custom_ratio_text
            )
            eval_result = self.evaluator.evaluate_formula_extraction(llm_result)
            if not eval_result.pass_:
                return self._error(eval_result.user_message)
            formula = llm_result.data["ingredients"]
            
        elif req.request_type == "price_query":
            price_result = await self.execution_guard.fetch_price(
                self.barchart_api, req.ingredient
            )
            eval_result = self.evaluator.evaluate_price_result(price_result)
            return self._success(eval_result.user_payload)
            
        elif req.request_type == "formula_recommendation":
            formula = self._recommend_by_weight(req.weight_kg)
            
        else:
            return self._error("无法识别请求类型")
        
        # 3. 配比评估
        ratio_eval = self.evaluator.evaluate_ratio(formula)
        if not ratio_eval.pass_:
            return self._error(ratio_eval.user_message)
        
        # 4. 成本计算
        cost_data = self._calculate_cost(formula)
        cost_eval = self.evaluator.evaluate_cost_result(cost_data)
        
        # 5. 记录轨迹
        self.trace_store.record_stage(trace, "completed", cost_eval)
        
        return self._success(cost_eval.user_payload)
        
    except Exception as e:
        self.trace_store.record_error(trace, e)
        return self._error(str(e))
```

---

## 📊 验收标准

### 功能验收

- [ ] Input Guard 能正确识别 5 种请求类型
- [ ] Execution Guard 能正确包装 LLM 和 Barchart 调用
- [ ] Evaluator 能正确评估 4 类结果
- [ ] Trace Store 能正确记录执行轨迹
- [ ] skill.py 成功接入 Harness 层

### 测试验收

- [ ] Harness 单元测试通过率 100%
- [ ] 集成测试通过率 100%
- [ ] 性能测试达标（平均 < 20ms）

### 文档验收

- [ ] Harness 设计文档完成
- [ ] API 文档更新完成
- [ ] 用户手册更新完成
- [ ] CHANGELOG v1.7 完成

---

## 🗓️ 时间安排

### 第 1 周（20 小时）

- **Day 1-2**: H01-H05 (Harness 核心层)
- **Day 3-4**: H06-H08 (Skill 接入 + 测试)
- **Day 5**: 周中 Review

### 第 2 周（20 小时）

- **Day 6-7**: H09-H11 (集成测试)
- **Day 8-9**: H12-H15 (文档)
- **Day 10**: 最终 Review + 发布

---

## 📈 预期收益

### 直接收益

1. **模糊输入不再直接冲进核心逻辑** - Input Guard 守门
2. **LLM 提取失败不会污染成本计算** - Execution Guard 隔离
3. **Barchart 降级变得可见、可追踪** - ToolResult 标记来源
4. **输出结果更稳定** - Evaluator 统一评估
5. **为 v1.8 SQLite/Owner 隔离铺好轨道** - Trace Store 结构化

### 长期收益

1. **自然演进到 v2.0 Harness Layer** - 不需重构
2. **易于接入多 Agent** - Harness 层已就绪
3. **易于接入 RAG/Memory** - Trace Store 已就绪

---

## ⚠️ 风险提示

### 技术风险

- **风险**: Harness 层增加延迟
- **缓解**: 性能测试确保 < 20ms
- **风险**: 现有测试失效
- **缓解**: 保留现有测试，新增 Harness 测试

### 进度风险

- **风险**: Harness 设计过于复杂
- **缓解**: 保持薄 Harness，不做大重构
- **风险**: Telegram 集成延期
- **缓解**: 分阶段，先核心层后渠道

---

## 📝 关键决策

### 已确认决策

1. ✅ **薄 Harness** - 包裹现有逻辑，不重写
2. ✅ **Single Skill 保持** - 不改多 Agent
3. ✅ **渐进式演进** - v1.7 薄层 → v1.8 持久化 → v2.0 Harness Layer

### 待确认决策

1. ⏳ **Trace 存储方式** - v1.7 内存 / v1.8 SQLite
2. ⏳ **Harness 配置化** - 是否需要配置文件
3. ⏳ **监控告警** - 是否接入告警系统

---

## 🎯 成功标准

### 必须满足

- [ ] 所有现有功能正常工作
- [ ] Harness 单元测试 100% 通过
- [ ] 性能指标达标
- [ ] 文档完整

### 期望满足

- [ ] Telegram 集成测试通过
- [ ] Trace 可查询
- [ ] 降级场景可追踪

---

**文档版本**: v1.0  
**创建日期**: 2026-03-28  
**审查状态**: 📋 待审查
