"""
FeedSales AI - 统一结果类型

所有服务返回统一格式
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class ServiceResult:
    """服务返回结果"""
    success: bool
    data: Optional[Dict] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    source: Optional[str] = None  # 'private' | 'public' | 'default' | None


@dataclass
class ValidationResult:
    """校验结果"""
    valid: bool
    errors: List[str] = field(default_factory=list)