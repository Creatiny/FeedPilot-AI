"""
FeedSales AI - Harness 入口集成测试 (v1.7)

测试完整的 Harness 工作流
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.harness.task_router import TaskRouter
from src.harness.session_state import SessionStateManager
from src.harness.result_validator import ResultValidator


def test_task_router():
    """测试 TaskRouter"""
    print("\n🧪 测试：TaskRouter")
    
    router = TaskRouter()
    
    # 测试任务分类
    task = router.classify("Nursery Diet 1 cost")
    assert task is not None, "应该识别任务"
    print(f"✅ 任务分类: {task}")


def test_session_state():
    """测试 SessionState"""
    print("\n🧪 测试：SessionState")
    
    manager = SessionStateManager()
    
    # 测试会话状态
    state = manager.get_state("test_session")
    assert state is not None, "应该返回状态"
    print(f"✅ 会话状态: {state}")


def test_result_validator():
    """测试 ResultValidator"""
    print("\n🧪 测试：ResultValidator")
    
    validator = ResultValidator()
    
    # 测试成功结果（需要 total_cost 字段）
    result = {'success': True, 'data': {'cost_per_ton': 284.3, 'total_cost': 284.3}}
    validated = validator.validate_cost_result(result)
    assert validated.valid, f"应该验证成功: {validated.errors}"
    print(f"✅ 结果验证成功")