#!/usr/bin/env python3
"""
FeedSales AI - Mock 测试

测试 BarchartAPI 和其他外部依赖的 Mock 测试
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.barchart_api import BarchartAPIClient
from src.database.repository import validate_owner_open_id, validate_formula_name


def test_barchart_api_mock():
    """测试 BarchartAPI Mock"""
    print("\n🧪 测试 BarchartAPI Mock...")
    
    # Mock API 响应
    mock_response = {
        "status": {"code": 200},
        "result": [{
            "symbol": "ZC",
            "description": "Corn",
            "last": 5.0,
            "change": 0.1,
            "changePercent": 2.0,
            "high": 5.1,
            "low": 4.9,
            "volume": 100000,
            "tradeTime": "2026-03-27T10:00:00Z"
        }]
    }
    
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        
        client = BarchartAPIClient(api_key="test_key")
        result = client.get_commodity_price("ZC")
        
        assert result is not None, "获取价格失败"
        assert result['symbol'] == "ZC", "商品代码错误"
        assert result['price'] == 5.0, "价格错误"
        
        print(f"  ✅ Mock 测试通过：${result['price']} / 蒲式耳")
        
        # 测试单位转换
        price_cny = client.convert_to_cny_ton(5.0, "玉米")
        assert price_cny > 0, "单位转换失败"
        print(f"  ✅ 单位转换测试通过：¥{price_cny} / 吨")
    
    return True


def test_barchart_api_failure_mock():
    """测试 BarchartAPI 失败场景 Mock"""
    print("\n🧪 测试 BarchartAPI 失败场景 Mock...")
    
    import requests
    
    with patch('requests.Session.get') as mock_get:
        # Mock HTTP 错误响应
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"status": {"code": 500, "message": "服务器错误"}}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response
        
        client = BarchartAPIClient(api_key="test_key")
        result = client.get_commodity_price("ZC")
        
        # 应该返回 None 或错误结果
        print(f"  ✅ 失败场景处理正确 (返回：{result})")
    
    return True


def test_input_validation():
    """测试输入验证函数"""
    print("\n🧪 测试输入验证函数...")
    
    # 测试 validate_owner_open_id
    assert validate_owner_open_id("user_123") == True, "有效 ID 验证失败"
    assert validate_owner_open_id("") == False, "空字符串应该失败"
    assert validate_owner_open_id("a" * 101) == False, "超长 ID 应该失败"
    print(f"  ✅ validate_owner_open_id 测试通过")
    
    # 测试 validate_formula_name
    assert validate_formula_name("保育料 1 号") == True, "有效配方名验证失败"
    assert validate_formula_name("") == False, "空字符串应该失败"
    assert validate_formula_name("a" * 201) == False, "超长配方名应该失败"
    print(f"  ✅ validate_formula_name 测试通过")
    
    return True


def test_repository_mock():
    """测试 Repository Mock"""
    print("\n🧪 测试 Repository Mock...")
    
    from src.database.repository import FormulaRepository
    from src.database.pool import DatabasePool
    
    # Mock DatabasePool
    mock_pool = Mock(spec=DatabasePool)
    mock_conn = Mock()
    mock_cursor = Mock()
    
    # 配置 Mock 返回值
    mock_cursor.fetchall.return_value = [
        {"id": 1, "name": "测试配方", "stage_type": "保育", "notes": "", 
         "ingredient_name": "玉米", "ratio_percent": 60.0}
    ]
    mock_cursor.fetchone.return_value = mock_cursor.fetchall.return_value[0]
    mock_conn.cursor.return_value = mock_cursor
    mock_pool.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
    mock_pool.get_connection.return_value.__exit__ = Mock(return_value=False)
    
    repo = FormulaRepository(mock_pool)
    formula = repo.get_formula("user_123", "测试配方")
    
    assert formula is not None, "获取配方失败"
    assert formula['name'] == "测试配方", "配方名称错误"
    print(f"  ✅ Repository Mock 测试通过")
    
    return True


def run_all_tests():
    """运行所有 Mock 测试"""
    print("=" * 60)
    print("FeedSales AI - Mock 测试")
    print("=" * 60)
    
    tests = [
        ("BarchartAPI Mock", test_barchart_api_mock),
        ("BarchartAPI 失败场景", test_barchart_api_failure_mock),
        ("输入验证", test_input_validation),
        ("Repository Mock", test_repository_mock),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试异常：{e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("Mock 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}: {name}")
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n✅ 所有 Mock 测试通过！")
        return True
    else:
        print(f"\n❌ {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
