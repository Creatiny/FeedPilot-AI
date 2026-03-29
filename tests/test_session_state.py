#!/usr/bin/env python3
"""
FeedSales AI - SessionStateManager 测试

TDD: 先写测试，再写实现
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.harness.session_state import SessionStateManager, SessionState


def test_create_session_state():
    """测试创建会话状态"""
    print("\n🧪 测试：创建会话状态")
    
    manager = SessionStateManager()
    state = manager.get_state('session_1')
    
    assert state is not None, "应该返回状态"
    assert state.user_id is None, "初始 user_id 应该为空"
    assert state.conversation_turn == 0, "初始 turn 应该为 0"
    
    print("  ✅ 会话状态创建成功")


def test_update_session_state():
    """测试更新会话状态"""
    print("\n🧪 测试：更新会话状态")
    
    manager = SessionStateManager()
    
    # 更新状态
    manager.update_state('session_1', user_id='user_a', current_customer='John')
    
    # 获取状态
    state = manager.get_state('session_1')
    
    assert state.user_id == 'user_a', f"user_id 错误: {state.user_id}"
    assert state.current_customer == 'John', f"current_customer 错误: {state.current_customer}"
    
    print("  ✅ 会话状态更新成功")


def test_multiple_sessions():
    """测试多会话隔离"""
    print("\n🧪 测试：多会话隔离")
    
    manager = SessionStateManager()
    
    # 设置不同会话的状态
    manager.update_state('session_1', user_id='user_a', current_formula='Formula A')
    manager.update_state('session_2', user_id='user_b', current_formula='Formula B')
    
    # 验证隔离
    state1 = manager.get_state('session_1')
    state2 = manager.get_state('session_2')
    
    assert state1.user_id == 'user_a', "session_1 user_id 错误"
    assert state2.user_id == 'user_b', "session_2 user_id 错误"
    assert state1.current_formula != state2.current_formula, "会话应该隔离"
    
    print("  ✅ 多会话隔离正确")


def test_increment_turn():
    """测试对话轮次增加"""
    print("\n🧪 测试：对话轮次增加")
    
    manager = SessionStateManager()
    
    state = manager.get_state('session_1')
    assert state.conversation_turn == 0
    
    manager.increment_turn('session_1')
    state = manager.get_state('session_1')
    assert state.conversation_turn == 1
    
    manager.increment_turn('session_1')
    state = manager.get_state('session_1')
    assert state.conversation_turn == 2
    
    print("  ✅ 对话轮次增加正确")


def test_clear_state():
    """测试清除会话状态"""
    print("\n🧪 测试：清除会话状态")
    
    manager = SessionStateManager()
    
    # 设置状态
    manager.update_state('session_1', user_id='user_a', current_customer='John')
    
    # 清除状态
    manager.clear_state('session_1')
    
    # 验证清除
    state = manager.get_state('session_1')
    assert state.user_id is None, "user_id 应该被清除"
    assert state.current_customer is None, "current_customer 应该被清除"
    
    print("  ✅ 会话状态清除成功")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("FeedSales AI - SessionStateManager 测试 (TDD)")
    print("=" * 60)
    
    tests = [
        test_create_session_state,
        test_update_session_state,
        test_multiple_sessions,
        test_increment_turn,
        test_clear_state,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)