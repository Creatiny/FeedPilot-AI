# FeedSales AI MVP v1.7 - Harness 详细设计方案

## 文档信息

| 项目 | 内容 |
|------|------|
| **版本** | v1.7.0 (Harness Layer) |
| **前置版本** | v1.6.0 |
| **设计日期** | 2026-03-28 |
| **状态** | 📋 设计中 |

---

## 🎯 设计目标

### 核心原则

1. **薄 Harness** - 包裹现有逻辑，不重写
2. **Single Skill 保持** - 不改多 Agent
3. **渐进式演进** - v1.7 薄层 → v1.8 持久化 → v2.0 Harness Layer

### 设计约束

- ✅ 兼容 OpenClaw 3.24 技能格式（SKILL.md + scripts/）
- ✅ 不改现有 `llm_extractor.py` 和 `barchart_api.py` 主体逻辑
- ✅ 保留现有测试体系
- ✅ 为 v1.8 SQLite/Owner 隔离铺好轨道

---

## 📐 架构设计

### v1.6 架构（当前）

```
Telegram / OpenClaw Runtime
 → Agent 读取 SKILL.md
   → 执行指令（调用 scripts/llm_extractor.py 等）
```

### v1.7 架构（目标）

```
Telegram / OpenClaw Runtime
 → Agent 读取 SKILL.md
   → 调用 scripts/harness/input_guard.py (输入守门)
   → 调用 scripts/llm_extractor.py (被 execution_guard 包装)
   → 调用 scripts/barchart_api.py (被 execution_guard 包装)
   → 调用 scripts/harness/evaluator.py (结果评估)
   → 调用 scripts/harness/trace_store.py (轨迹记录)
```

---

## 📁 文件结构

### 新增文件

```
skills/formula_cost_skill/scripts/harness/
├── __init__.py
├── schemas.py            # 标准结构定义 (200 行)
├── input_guard.py        # 输入守门 (150 行)
├── execution_guard.py    # 执行守门 (200 行)
├── evaluator.py          # 结果评估 (250 行)
└── trace_store.py        # 轨迹记录 (150 行)
```

### 修改文件

```
skills/formula_cost_skill/
├── SKILL.md              # 接入 Harness 调用 (修改工作流程部分)
└── scripts/
    ├── llm_extractor.py  # 被包装，不改主体
    └── barchart_api.py   # 被包装，不改主体
```

### 新增测试

```
tests/test_harness/
├── test_input_guard.py
├── test_execution_guard.py
├── test_evaluator.py
└── test_trace_store.py
```

---

## 🔍 详细设计

### schemas.py

```python
"""
Harness 标准结构定义

定义所有 Harness 模块使用的标准数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import time
import uuid


class RequestType(str, Enum):
    """请求类型"""
    FORMULA_NAME = "formula_name"           # 标准配方查询
    CUSTOM_RATIO = "custom_ratio"           # 自定义配比
    PRICE_QUERY = "price_query"             # 价格查询
    FORMULA_RECOMMENDATION = "recommendation"  # 配方推荐
    UNKNOWN = "unknown"                     # 无法识别


@dataclass
class ParsedRequest:
    """解析后的请求对象"""
    request_type: RequestType
    raw_message: str
    normalized_message: str
    formula_name: Optional[str] = None
    custom_ratio_text: Optional[str] = None
    weight_kg: Optional[float] = None
    ingredient: Optional[str] = None
    needs_llm: bool = False
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_type": self.request_type.value,
            "raw_message": self.raw_message,
            "normalized_message": self.normalized_message,
            "formula_name": self.formula_name,
            "custom_ratio_text": self.custom_ratio_text,
            "weight_kg": self.weight_kg,
            "ingredient": self.ingredient,
            "needs_llm": self.needs_llm,
            "valid": self.valid,
            "errors": self.errors
        }


@dataclass
class ToolResult:
    """工具执行结果"""
    ok: bool
    source: str  # qwen | barchart | local_cache | json | fallback
    degraded: bool
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "ok": self.ok,
            "source": self.source,
            "degraded": self.degraded,
            "data": self.data,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": self.metadata
        }
    
    @classmethod
    def success(cls, source: str, data: Dict[str, Any], **kwargs) -> 'ToolResult':
        """创建成功结果"""
        return cls(ok=True, source=source, degraded=False, data=data, **kwargs)
    
    @classmethod
    def failure(cls, source: str, error_code: str, error_message: str, **kwargs) -> 'ToolResult':
        """创建失败结果"""
        return cls(ok=False, source=source, degraded=True, 
                  error_code=error_code, error_message=error_message, **kwargs)


@dataclass
class EvalResult:
    """评估结果"""
    pass_: bool
    user_message: str
    user_payload: Dict[str, Any]
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pass": self.pass_,
            "user_message": self.user_message,
            "user_payload": self.user_payload,
            "details": self.details
        }


@dataclass
class Trace:
    """执行轨迹"""
    trace_id: str
    user_id: str
    raw_message: str
    stages: List[Dict[str, Any]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "raw_message": self.raw_message,
            "stages": self.stages,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error": self.error,
            "metadata": self.metadata,
            "duration": (self.end_time or time.time()) - self.start_time
        }


def generate_trace_id() -> str:
    """生成轨迹 ID"""
    return f"trace_{uuid.uuid4().hex[:12]}"


def generate_id() -> str:
    """生成通用 ID"""
    return uuid.uuid4().hex[:8]
```

### input_guard.py

```python
"""
输入守门员

职责：
1. 输入校验增强
2. 意图归类
3. 结构化请求对象生成
"""

import re
from typing import List, Tuple
from .schemas import ParsedRequest, RequestType


class InputGuard:
    """输入守门员"""
    
    # 意图关键词映射
    INTENT_KEYWORDS = {
        RequestType.FORMULA_NAME: [
            "计算.*成本", "配方.*多少钱", ".*配方成本", 
            "calculate.*cost", "formula.*cost"
        ],
        RequestType.CUSTOM_RATIO: [
            "自定义.*配比", "自己.*配方", "我想.*配",
            "custom.*ratio", "my.*formula"
        ],
        RequestType.PRICE_QUERY: [
            ".*价格", ".*多少钱一吨", "查询.*价格",
            "price.*query", "how much.*ton"
        ],
        RequestType.FORMULA_RECOMMENDATION: [
            ".*推荐.*配方", ".*用什么配方", ".*阶段.*配方",
            "recommend.*formula", "what formula.*use"
        ]
    }
    
    # 体重阶段关键词
    WEIGHT_STAGES = {
        "仔猪": (5.0, 25.0),
        "保育": (25.0, 60.0),
        "育肥": (60.0, 120.0),
        "母猪": (120.0, 250.0)
    }
    
    def parse(self, message: str) -> ParsedRequest:
        """
        解析用户消息
        
        Args:
            message: 用户原始消息
            
        Returns:
            ParsedRequest: 解析后的请求对象
        """
        # 1. 标准化消息
        normalized = self._normalize_message(message)
        
        # 2. 识别意图
        request_type = self._identify_intent(normalized)
        
        # 3. 提取参数
        params = self._extract_params(normalized, request_type)
        
        # 4. 构建请求对象
        req = ParsedRequest(
            request_type=request_type,
            raw_message=message,
            normalized_message=normalized,
            needs_llm=(request_type == RequestType.CUSTOM_RATIO),
            **params
        )
        
        # 5. 校验请求
        self._validate_request(req)
        
        return req
    
    def _normalize_message(self, message: str) -> str:
        """标准化消息"""
        # 转小写
        normalized = message.lower()
        # 去除多余空格
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        # 中文转小写（简单处理）
        return normalized
    
    def _identify_intent(self, message: str) -> RequestType:
        """识别意图"""
        for request_type, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if re.search(keyword, message):
                    return request_type
        return RequestType.UNKNOWN
    
    def _extract_params(self, message: str, request_type: RequestType) -> dict:
        """提取参数"""
        params = {}
        
        if request_type == RequestType.FORMULA_NAME:
            # 提取配方名称
            match = re.search(r'(保育.*? | 育肥.*? | 母猪.*? | 仔猪.*?)', message)
            if match:
                params["formula_name"] = match.group(1).strip()
        
        elif request_type == RequestType.CUSTOM_RATIO:
            # 提取自定义配比文本
            params["custom_ratio_text"] = message
        
        elif request_type == RequestType.PRICE_QUERY:
            # 提取原料名称
            for ingredient in ["玉米", "豆粕", "豆油", "小麦", "鱼粉"]:
                if ingredient in message:
                    params["ingredient"] = ingredient
                    break
        
        elif request_type == RequestType.FORMULA_RECOMMENDATION:
            # 提取体重
            weight_match = re.search(r'(\d+(?:\.\d+)?)\s*kg', message)
            if weight_match:
                params["weight_kg"] = float(weight_match.group(1))
            
            # 提取阶段
            for stage, (min_w, max_w) in self.WEIGHT_STAGES.items():
                if stage in message:
                    params["weight_kg"] = (min_w + max_w) / 2
                    break
        
        return params
    
    def _validate_request(self, req: ParsedRequest) -> None:
        """校验请求"""
        if req.request_type == RequestType.UNKNOWN:
            req.valid = False
            req.errors.append("无法识别请求类型")
        
        elif req.request_type == RequestType.FORMULA_NAME:
            if not req.formula_name:
                req.valid = False
                req.errors.append("未指定配方名称")
        
        elif req.request_type == RequestType.PRICE_QUERY:
            if not req.ingredient:
                req.valid = False
                req.errors.append("未指定原料名称")
```

### execution_guard.py

```python
"""
执行守门员

职责：
1. 统一包装对 llm_extractor 和 barchart_api 的调用
2. 打标签：成功 / 失败 / 降级
3. 保证返回结构统一
"""

import asyncio
from typing import Any, Dict
from .schemas import ToolResult


class ExecutionGuard:
    """执行守门员"""
    
    def __init__(self):
        self.local_cache = {}  # 本地缓存
    
    async def extract_formula(
        self, 
        llm_extractor: Any,
        text: str,
        timeout: float = 10.0
    ) -> ToolResult:
        """
        包装 LLM 配方提取
        
        Args:
            llm_extractor: LLM 提取器实例
            text: 自定义配比文本
            timeout: 超时时间（秒）
            
        Returns:
            ToolResult: 执行结果
        """
        try:
            # 调用 LLM 提取器
            result = await asyncio.wait_for(
                llm_extractor.extract(text),
                timeout=timeout
            )
            
            return ToolResult.success(
                source="qwen",
                data=result,
                metadata={"timeout": timeout}
            )
            
        except asyncio.TimeoutError:
            return ToolResult.failure(
                source="qwen",
                error_code="ERR_LLM_TIMEOUT",
                error_message=f"LLM 提取超时（{timeout}秒）"
            )
            
        except Exception as e:
            return ToolResult.failure(
                source="qwen",
                error_code="ERR_LLM_FAILED",
                error_message=f"LLM 提取失败：{str(e)}"
            )
    
    async def fetch_price(
        self, 
        barchart_api: Any,
        ingredient: str,
        use_cache: bool = True
    ) -> ToolResult:
        """
        包装 Barchart 价格获取
        
        Args:
            barchart_api: Barchart API 实例
            ingredient: 原料名称
            use_cache: 是否使用缓存
            
        Returns:
            ToolResult: 执行结果
        """
        try:
            # 调用 Barchart API
            price = await barchart_api.get_price(ingredient)
            
            return ToolResult.success(
                source="barchart",
                data={"price": price, "ingredient": ingredient}
            )
            
        except Exception as e:
            # 降级到本地缓存
            if use_cache:
                cached_price = self._get_cached_price(ingredient)
                if cached_price:
                    return ToolResult.success(
                        source="local_cache",
                        data={"price": cached_price, "ingredient": ingredient},
                        metadata={"degraded": True, "reason": "barchart_failed"}
                    )
            
            return ToolResult.failure(
                source="barchart",
                error_code="ERR_PRICE_MISSING",
                error_message=f"价格获取失败：{str(e)}"
            )
    
    def _get_cached_price(self, ingredient: str) -> float:
        """获取缓存价格"""
        # 默认价格表
        default_prices = {
            "玉米": 2800.00,
            "豆粕": 4200.00,
            "豆油": 6500.00,
            "小麦": 2700.00,
            "鱼粉": 9000.00,
            "预混料": 3200.00,
        }
        return default_prices.get(ingredient)
```

### evaluator.py

```python
"""
结果评估器

职责：
1. 对关键输出做业务校验
2. 判断结果能不能直接返回用户
"""

from typing import Any, Dict
from .schemas import ToolResult, EvalResult


class Evaluator:
    """结果评估器"""
    
    def evaluate_formula_extraction(self, result: ToolResult) -> EvalResult:
        """
        评估配方提取结果
        
        规则：
        1. LLM 提取结果不可信时，不能直接进成本计算
        2. 置信度 < 0.80 失败
        3. 空结果失败
        """
        if not result.ok:
            return EvalResult(
                pass_=False,
                user_message="配方提取失败，请明确配方名称或配比",
                user_payload={"error": result.error_message},
                details={"tool_result": result.to_dict()}
            )
        
        # 置信度检查
        confidence = result.data.get("confidence", 0)
        if confidence < 0.80:
            return EvalResult(
                pass_=False,
                user_message="配方提取置信度不足，请明确配方名称",
                user_payload={"error": "置信度不足", "confidence": confidence},
                details={"tool_result": result.to_dict()}
            )
        
        # 空结果检查
        ingredients = result.data.get("ingredients", [])
        if not ingredients:
            return EvalResult(
                pass_=False,
                user_message="未提取到有效原料",
                user_payload={"error": "空结果"},
                details={"tool_result": result.to_dict()}
            )
        
        # 配比总和检查
        ratio_sum = sum(ing.get("ratio", 0) for ing in ingredients)
        if not 99.9 <= ratio_sum <= 100.1:
            return EvalResult(
                pass_=False,
                user_message=f"配比不合法 ({ratio_sum}%), 请确保总和为 100%",
                user_payload={"error": "配比不合法", "ratio_sum": ratio_sum},
                details={"tool_result": result.to_dict()}
            )
        
        return EvalResult(
            pass_=True,
            user_message="配方提取成功",
            user_payload=result.data,
            details={"tool_result": result.to_dict()}
        )
    
    def evaluate_price_result(self, result: ToolResult) -> EvalResult:
        """
        评估价格结果
        
        规则：
        1. Barchart 不可用时，明确标注为缓存价
        2. 缺失价格不能伪装成完整成本
        """
        if not result.ok:
            return EvalResult(
                pass_=False,
                user_message="价格查询失败",
                user_payload={"error": result.error_message},
                details={"tool_result": result.to_dict()}
            )
        
        # 构建输出
        output = {
            "ingredient": result.data.get("ingredient"),
            "price": result.data.get("price"),
            "metadata": {
                "data_source": result.source,
                "degraded": result.degraded
            }
        }
        
        user_message = f"{output['ingredient']}价格：¥{output['price']}/吨"
        if result.degraded:
            user_message += " (缓存价格)"
        
        return EvalResult(
            pass_=True,
            user_message=user_message,
            user_payload=output,
            details={"tool_result": result.to_dict()}
        )
    
    def evaluate_ratio(self, formula: Dict[str, Any]) -> EvalResult:
        """
        评估配比合法性
        
        规则：
        1. 配比总和必须在 [99.9, 100.1] 范围内
        """
        ingredients = formula.get("ingredients", [])
        ratio_sum = sum(ing.get("ratio", 0) for ing in ingredients)
        
        if not 99.9 <= ratio_sum <= 100.1:
            return EvalResult(
                pass_=False,
                user_message=f"配比不合法 ({ratio_sum}%), 请确保总和为 100%",
                user_payload={"error": "配比不合法", "ratio_sum": ratio_sum},
                details={"formula": formula}
            )
        
        return EvalResult(
            pass_=True,
            user_message="配比合法",
            user_payload=formula,
            details={"ratio_sum": ratio_sum}
        )
    
    def evaluate_cost_result(self, cost_data: Dict[str, Any]) -> EvalResult:
        """
        评估成本结果
        
        规则：
        1. 缺失价格的原料要标记 null
        2. 放进 missing_ingredients
        """
        # 检查缺失原料
        missing = cost_data.get("missing_ingredients", [])
        if missing:
            user_message = f"成本计算完成（{len(missing)} 种原料无价格）"
        else:
            user_message = f"成本计算完成：¥{cost_data.get('cost_per_ton', 0):.2f}/吨"
        
        return EvalResult(
            pass_=True,
            user_message=user_message,
            user_payload=cost_data,
            details={"missing_count": len(missing)}
        )
```

### trace_store.py

```python
"""
轨迹存储

职责：
1. 记录执行轨迹
2. 为后续 SQLite / owner 隔离 / Memory 做铺垫
"""

import time
from typing import Any, Dict, List, Optional
from .schemas import Trace, generate_trace_id


class TraceStore:
    """轨迹存储"""
    
    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.max_traces = 1000  # 内存中最多保留 1000 条轨迹
    
    def start_trace(self, user_id: str, raw_message: str) -> Trace:
        """
        开始轨迹记录
        
        Args:
            user_id: 用户 ID
            raw_message: 原始消息
            
        Returns:
            Trace: 轨迹对象
        """
        trace = Trace(
            trace_id=generate_trace_id(),
            user_id=user_id,
            raw_message=raw_message
        )
        
        # 保存到内存
        self.traces[trace.trace_id] = trace
        
        # 清理旧轨迹
        if len(self.traces) > self.max_traces:
            oldest_id = next(iter(self.traces))
            del self.traces[oldest_id]
        
        return trace
    
    def record_stage(
        self, 
        trace: Trace, 
        stage_name: str, 
        data: Any,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        记录阶段数据
        
        Args:
            trace: 轨迹对象
            stage_name: 阶段名称
            data: 阶段数据
            metadata: 附加元数据
        """
        stage = {
            "name": stage_name,
            "data": data,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        trace.stages.append(stage)
    
    def record_error(self, trace: Trace, error: Exception) -> None:
        """
        记录错误
        
        Args:
            trace: 轨迹对象
            error: 异常对象
        """
        trace.error = str(error)
        trace.end_time = time.time()
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """获取轨迹"""
        return self.traces.get(trace_id)
    
    def get_user_traces(self, user_id: str, limit: int = 10) -> List[Trace]:
        """获取用户轨迹"""
        user_traces = [
            t for t in self.traces.values() 
            if t.user_id == user_id
        ]
        return sorted(user_traces, key=lambda t: t.start_time, reverse=True)[:limit]
    
    def save_to_file(self, trace: Trace, filepath: str) -> None:
        """
        保存轨迹到文件（v1.8 持久化到 SQLite）
        
        Args:
            trace: 轨迹对象
            filepath: 文件路径
        """
        import json
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(trace.to_dict(), f, ensure_ascii=False, indent=2)
    
    def clear(self) -> None:
        """清空轨迹"""
        self.traces.clear()


# 全局轨迹存储实例
_global_store = TraceStore()

def get_trace_store() -> TraceStore:
    """获取全局轨迹存储"""
    return _global_store
```

---

## 📝 SKILL.md 修改示例

### 修改前

```markdown
# 饲料配方成本计算技能

## 工作流程

1. **获取配方名称** - 从用户消息中提取配方名称
2. **查询配方数据** - 从数据库获取配方成分和比例
3. **获取原料价格** - 查询最新原料价格
4. **计算成本** - 计算每吨成本和每公斤成本
5. **返回结果** - 格式化输出成本明细
```

### 修改后

```markdown
# 饲料配方成本计算技能

## 工作流程

1. **输入守门** - 调用 `{baseDir}/scripts/harness/input_guard.py`
   ```bash
   python3 {baseDir}/scripts/harness/input_guard.py --message "$USER_MESSAGE"
   ```

2. **配方提取** - 调用 `{baseDir}/scripts/llm_extractor.py`（被 execution_guard 包装）
   ```bash
   python3 {baseDir}/scripts/harness/execution_guard.py --tool llm_extractor --text "$CUSTOM_RATIO"
   ```

3. **价格获取** - 调用 `{baseDir}/scripts/barchart_api.py`（被 execution_guard 包装）
   ```bash
   python3 {baseDir}/scripts/harness/execution_guard.py --tool barchart_api --ingredient "$INGREDIENT"
   ```

4. **结果评估** - 调用 `{baseDir}/scripts/harness/evaluator.py`
   ```bash
   python3 {baseDir}/scripts/harness/evaluator.py --stage formula_extraction --result "$EXTRACTION_RESULT"
   ```

5. **轨迹记录** - 调用 `{baseDir}/scripts/harness/trace_store.py`
   ```bash
   python3 {baseDir}/scripts/harness/trace_store.py --trace-id "$TRACE_ID" --stage completed
   ```

## 错误处理

- **配方不存在**: Harness Input Guard 返回友好提示
- **价格缺失**: Harness Evaluator 标记为 null，放进 missing_ingredients
- **LLM 失败**: Harness Execution Guard 降级到模板响应
```

---

## ✅ 验收标准

### 代码验收

- [ ] schemas.py 定义 5 个标准数据结构
- [ ] input_guard.py 能正确识别 5 种请求类型
- [ ] execution_guard.py 能正确包装 LLM 和 Barchart 调用
- [ ] evaluator.py 能正确评估 4 类结果
- [ ] trace_store.py 能正确记录执行轨迹

### 测试验收

- [ ] Harness 单元测试通过率 100%
- [ ] 集成测试通过率 100%
- [ ] 性能测试达标（Harness 层 < 10ms）

### 文档验收

- [ ] SKILL.md 修改完成
- [ ] Harness 设计文档完成
- [ ] API 文档更新完成

---

**文档版本**: v1.0  
**创建日期**: 2026-03-28  
**审查状态**: 📋 待审查
