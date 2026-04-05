"""
FeedSales AI - 错误处理装饰器

提供统一的错误处理和日志记录
"""

import logging
from functools import wraps
from typing import Callable, Any, Dict


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def handle_errors(default_return: Any = None):
    """
    错误处理装饰器
    
    Args:
        default_return: 出错时的默认返回值
        
    Usage:
        @handle_errors(default_return={"error": "操作失败"})
        def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                logger.info(f"执行 {func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"{func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} 执行失败：{e}", exc_info=True)
                if default_return is not None:
                    return default_return
                raise
        return wrapper
    return decorator


def validate_input(required_fields: list):
    """
    输入验证装饰器
    
    Args:
        required_fields: 必需的字段列表
        
    Usage:
        @validate_input(["formula_name", "owner_open_id"])
        def calculate_cost(formula_name, owner_open_id, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 检查必需字段
            for field in required_fields:
                if field not in kwargs or not kwargs[field]:
                    error_msg = f"缺少必需字段：{field}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
            
            logger.info(f"输入验证通过：{required_fields}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """
    失败重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔（秒）
        
    Usage:
        @retry_on_failure(max_attempts=3, delay=1.0)
        def call_external_api():
            ...
    """
    import time
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(f"执行 {func.__name__} (尝试 {attempt}/{max_attempts})")
                    result = func(*args, **kwargs)
                    logger.info(f"{func.__name__} 执行成功")
                    return result
                except Exception as e:
                    last_exception = e
                    logger.warning(f"{func.__name__} 失败 (尝试 {attempt}/{max_attempts}): {e}")
                    if attempt < max_attempts:
                        time.sleep(delay)
            
            logger.error(f"{func.__name__} 最终失败：{last_exception}")
            raise last_exception
        return wrapper
    return decorator


def log_execution_time():
    """
    执行时间日志装饰器
    
    Usage:
        @log_execution_time()
        def slow_function():
            ...
    """
    import time
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                logger.info(f"{func.__name__} 执行时间：{execution_time:.3f}秒")
        return wrapper
    return decorator


# 使用示例
if __name__ == "__main__":
    # 测试错误处理
    @handle_errors(default_return={"success": False, "error": "操作失败"})
    def test_function(should_fail: bool = False):
        if should_fail:
            raise ValueError("测试错误")
        return {"success": True}
    
    print("测试 1: 成功情况")
    result = test_function(should_fail=False)
    print(f"  结果：{result}")
    
    print("\n测试 2: 失败情况")
    result = test_function(should_fail=True)
    print(f"  结果：{result}")
    
    # 测试输入验证
    @validate_input(["name", "value"])
    def test_validate(name: str, value: int):
        return f"{name}: {value}"
    
    print("\n测试 3: 输入验证通过")
    try:
        result = test_validate(name="test", value=123)
        print(f"  结果：{result}")
    except ValueError as e:
        print(f"  错误：{e}")
    
    print("\n测试 4: 输入验证失败")
    try:
        result = test_validate(name="test")  # 缺少 value
    except ValueError as e:
        print(f"  错误：{e}")
