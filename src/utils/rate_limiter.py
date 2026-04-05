"""
FeedSales AI - Rate Limiter

API 限流器，防止触发 API 限流
"""

import time
from threading import Lock
from typing import Dict, Optional
from datetime import datetime, timedelta


class RateLimiter:
    """
    令牌桶限流器
    
    Usage:
        limiter = RateLimiter(max_calls=100, period=60)  # 60 秒内最多 100 次
        
        @limiter.limit()
        def call_api():
            ...
    """
    
    def __init__(self, max_calls: int, period: float = 60.0):
        """
        初始化限流器
        
        Args:
            max_calls: 最大调用次数
            period: 时间窗口（秒）
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: Dict[str, list] = {}
        self.lock = Lock()
    
    def _get_key(self, key: Optional[str] = None) -> str:
        """获取限流键"""
        return key or "default"
    
    def _clean_old_calls(self, key: str) -> None:
        """清理过期的调用记录"""
        now = time.time()
        cutoff = now - self.period
        
        if key in self.calls:
            self.calls[key] = [t for t in self.calls[key] if t > cutoff]
    
    def is_allowed(self, key: Optional[str] = None) -> bool:
        """
        检查是否允许调用
        
        Args:
            key: 限流键（用于区分不同的 API 或用户）
            
        Returns:
            是否允许调用
        """
        key = self._get_key(key)
        
        with self.lock:
            self._clean_old_calls(key)
            return len(self.calls.get(key, [])) < self.max_calls
    
    def record_call(self, key: Optional[str] = None) -> None:
        """
        记录一次调用
        
        Args:
            key: 限流键
        """
        key = self._get_key(key)
        
        with self.lock:
            self._clean_old_calls(key)
            if key not in self.calls:
                self.calls[key] = []
            self.calls[key].append(time.time())
    
    def wait_if_needed(self, key: Optional[str] = None, timeout: float = 30.0) -> bool:
        """
        如果需要则等待
        
        Args:
            key: 限流键
            timeout: 最大等待时间（秒）
            
        Returns:
            是否成功获得调用许可
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_allowed(key):
                self.record_call(key)
                return True
            time.sleep(0.1)
        
        return False
    
    def get_remaining_calls(self, key: Optional[str] = None) -> int:
        """
        获取剩余调用次数
        
        Args:
            key: 限流键
            
        Returns:
            剩余调用次数
        """
        key = self._get_key(key)
        
        with self.lock:
            self._clean_old_calls(key)
            current_calls = len(self.calls.get(key, []))
            return max(0, self.max_calls - current_calls)
    
    def get_reset_time(self, key: Optional[str] = None) -> datetime:
        """
        获取限流重置时间
        
        Args:
            key: 限流键
            
        Returns:
            重置时间
        """
        key = self._get_key(key)
        
        with self.lock:
            self._clean_old_calls(key)
            if key in self.calls and len(self.calls[key]) > 0:
                oldest_call = min(self.calls[key])
                reset_time = datetime.fromtimestamp(oldest_call + self.period)
                return reset_time
            else:
                return datetime.now()
    
    def limit(self, key: Optional[str] = None, timeout: float = 30.0):
        """
        限流装饰器
        
        Args:
            key: 限流键
            timeout: 最大等待时间（秒）
            
        Usage:
            @limiter.limit(key="barchart_api", timeout=30.0)
            def call_barchart_api():
                ...
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.wait_if_needed(key, timeout):
                    reset_time = self.get_reset_time(key)
                    raise Exception(
                        f"API 限流，请在 {reset_time} 后重试"
                    )
                return func(*args, **kwargs)
            return wrapper
        return decorator


# 预定义的限流器实例
class PredefinedLimiters:
    """预定义限流器"""
    
    # Barchart API: 100 次/小时
    barchart = RateLimiter(max_calls=100, period=3600)
    
    # DashScope API: 1000 次/分钟
    dashscope = RateLimiter(max_calls=1000, period=60)
    
    # OpenRouter API: 60 次/分钟
    openrouter = RateLimiter(max_calls=60, period=60)
    
    # 数据库操作：1000 次/秒
    database = RateLimiter(max_calls=1000, period=1)


# 使用示例
if __name__ == "__main__":
    # 创建限流器：5 秒内最多 3 次
    limiter = RateLimiter(max_calls=3, period=5.0)
    
    print("测试限流器：5 秒内最多 3 次调用")
    
    for i in range(5):
        if limiter.is_allowed():
            limiter.record_call()
            remaining = limiter.get_remaining_calls()
            reset_time = limiter.get_reset_time()
            print(f"  ✅ 调用 {i+1} 成功 (剩余 {remaining} 次，重置时间 {reset_time.strftime('%H:%M:%S')})")
        else:
            print(f"  ❌ 调用 {i+1} 被限流")
            reset_time = limiter.get_reset_time()
            print(f"     重置时间：{reset_time.strftime('%H:%M:%S')}")
        
        time.sleep(1.0)
