"""
FeedSales AI - TaskRouter

任务路由器，将用户消息分类为固定任务类型
"""

import re
from typing import Dict, List


class TaskRouter:
    """
    任务路由器
    
    将用户消息分类为固定的任务类型，避免模型在所有能力里乱猜
    """
    
    # 任务类型定义（按优先级排序）
    TASK_TYPES = [
        'formula_cost_query',   # 配方成本查询
        'formula_manage',       # 配方管理
        'price_manage',         # 价格管理（优先于查询）
        'price_query',          # 价格查询
        'customer_manage',      # 客户管理
        'quote_generate',       # 报价生成
        'nutrition_analysis',   # 营养分析
        'unknown',              # 未知类型
    ]
    
    # 匹配模式（正则表达式）
    TASK_PATTERNS = {
        'formula_cost_query': [
            r'计算.*成本',
            r'查.*成本',
            r'配方.*成本',
            r'多少钱(一吨|每吨)',
        ],
        'formula_manage': [
            r'(创建|添加|新建|增加).*(配方)',
            r'(修改|更新|编辑).*(配方|保育料|育肥料)',
            r'(删除|移除).*(配方)',
            r'(查看|列出|显示|所有).*(配方)',
        ],
        'price_manage': [
            r'(设置|更新|修改).*(价格|采购价)',
            r'我的.*价格.*\d',  # 包含数字的
            r'我的.*价格(列表|清单)',
            r'(录入|输入).*价格',
        ],
        'price_query': [
            r'(今天|当前|最新).*(价格|行情)',
            r'(查|查询|问).*(价格|行情)',
            r'(玉米|豆粕|鱼粉|原料).*(价格|多少钱)',
        ],
        'customer_manage': [
            r'(添加|创建|新增|增加).*(客户)',
            r'(修改|更新|编辑).*(客户)',
            r'(删除|移除).*(客户)',
            r'(查看|列出|显示).*(客户)',
        ],
        'quote_generate': [
            r'(生成|做|开|制作).*(报价|报价单)',
            r'给.*(报价)',
        ],
        'nutrition_analysis': [
            r'(分析|查看).*(营养|成分)',
            r'配方.*(营养|成分)',
            r'(营养|成分).*(分析|查询)',
        ],
    }
    
    def __init__(self):
        """初始化任务路由器"""
        # 编译正则表达式（提高性能）
        self._compiled_patterns = {}
        for task_type, patterns in self.TASK_PATTERNS.items():
            self._compiled_patterns[task_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def classify(self, message: str) -> str:
        """
        分类用户消息
        
        Args:
            message: 用户消息
            
        Returns:
            str: 任务类型
        """
        if not message:
            return 'unknown'
        
        # 按优先级匹配
        for task_type in self.TASK_TYPES[:-1]:  # 排除 unknown
            patterns = self._compiled_patterns.get(task_type, [])
            for pattern in patterns:
                if pattern.search(message):
                    return task_type
        
        return 'unknown'
    
    def get_task_types(self) -> List[str]:
        """获取所有任务类型"""
        return self.TASK_TYPES.copy()
    
    def get_patterns(self, task_type: str) -> List[str]:
        """获取指定任务类型的匹配模式"""
        return self.TASK_PATTERNS.get(task_type, [])