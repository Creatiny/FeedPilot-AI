"""
FeedSales AI - FeedSalesHarness

完整的业务运行环境，整合所有服务和 Harness 组件
"""

import logging
from typing import Dict, Any, Optional

from ..database.pool import DatabasePool
from ..services.formula_service import FormulaService
from ..services.price_service import PriceService
from ..services.customer_service import CustomerService
from ..services.calculation_service import CalculationService
from .task_router import TaskRouter
from .session_state import SessionStateManager
from .result_validator import ResultValidator

logger = logging.getLogger(__name__)


class FeedSalesHarness:
    """
    FeedSales 业务最小 Harness
    
    整合所有服务和 Harness 组件，提供统一的业务处理入口
    """
    
    def __init__(self, db_pool: DatabasePool):
        """
        初始化 Harness
        
        Args:
            db_pool: 数据库连接池
        """
        self.db_pool = db_pool
        
        # 初始化服务层
        self.formula_service = FormulaService(db_pool)
        self.price_service = PriceService(db_pool)
        self.customer_service = CustomerService(db_pool)
        self.calculation_service = CalculationService(db_pool)
        
        # 初始化 Harness 组件
        self.task_router = TaskRouter()
        self.session_manager = SessionStateManager()
        self.result_validator = ResultValidator()
        
        logger.info("FeedSalesHarness initialized")
    
    def process(self, session_id: str, user_id: str, message: str) -> Dict[str, Any]:
        """
        处理用户消息
        
        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            message: 用户消息
            
        Returns:
            Dict: 处理结果
        """
        try:
            # 1. 更新会话状态
            self.session_manager.update_state(session_id, user_id=user_id)
            self.session_manager.increment_turn(session_id)
            
            # 2. 任务分类
            task_type = self.task_router.classify(message)
            logger.info(f"Task classified: {task_type}")
            
            # 3. 根据任务类型执行
            result = self._execute_task(user_id, message, task_type)
            
            # 4. 添加元数据
            result['task_type'] = task_type
            result['session_id'] = session_id
            
            return result
            
        except Exception as e:
            logger.error(f"Harness process failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'task_type': 'unknown'
            }
    
    def _execute_task(self, user_id: str, message: str, task_type: str) -> Dict[str, Any]:
        """执行任务"""
        
        if task_type == 'formula_cost_query':
            return self._handle_formula_cost_query(user_id, message)
        
        elif task_type == 'formula_manage':
            return self._handle_formula_manage(user_id, message)
        
        elif task_type == 'price_query':
            return self._handle_price_query(user_id, message)
        
        elif task_type == 'price_manage':
            return self._handle_price_manage(user_id, message)
        
        elif task_type == 'customer_manage':
            return self._handle_customer_manage(user_id, message)
        
        elif task_type == 'quote_generate':
            return self._handle_quote_generate(user_id, message)
        
        elif task_type == 'nutrition_analysis':
            return self._handle_nutrition_analysis(user_id, message)
        
        else:
            return {
                'success': False,
                'error': '无法识别的任务类型，请明确您的需求'
            }
    
    def _handle_formula_cost_query(self, user_id: str, message: str) -> Dict[str, Any]:
        """处理配方成本查询"""
        import re
        
        # 提取配方名
        match = re.search(r'计算(.+?)(的成本|成本)', message)
        if not match:
            match = re.search(r'(.+?)成本', message)
        
        if not match:
            return {'success': False, 'error': '请指定要计算的配方名称'}
        
        formula_name = match.group(1).strip()
        
        result = self.calculation_service.calculate_cost(user_id, formula_name)
        
        if result.success:
            # 校验结果
            validation = self.result_validator.validate_cost_result(result.data)
            if not validation.valid:
                logger.warning(f"Cost result validation failed: {validation.errors}")
            
            return {'success': True, 'data': result.data}
        else:
            return {'success': False, 'error': result.error_message, 'error_code': result.error_code}
    
    def _handle_formula_manage(self, user_id: str, message: str) -> Dict[str, Any]:
        """处理配方管理"""
        import re
        
        if re.search(r'(创建|添加|新建)', message):
            # 简化处理：创建配方需要更多参数，这里返回提示
            return {
                'success': True,
                'data': {
                    'message': '创建配方功能需要更多参数，请提供配方名称、动物类型、饲养阶段等信息'
                }
            }
        
        elif re.search(r'(列出|查看|所有)', message):
            result = self.formula_service.list_formulas(user_id)
            return {'success': True, 'data': result.data}
        
        else:
            return {'success': False, 'error': '配方管理操作未识别'}
    
    def _handle_price_query(self, user_id: str, message: str) -> Dict[str, Any]:
        """处理价格查询"""
        # 提取原料名
        ingredient_map = {
            '玉米': 'Corn, grain',
            '豆粕': 'Soybean meal, 48%',
            'corn': 'Corn, grain',
            'soybean': 'Soybean meal, 48%',
        }
        
        ingredient = None
        for key, value in ingredient_map.items():
            if key in message.lower():
                ingredient = value
                break
        
        if not ingredient:
            # 列出所有价格
            result = self.price_service.list_public_prices()
            return {'success': True, 'data': result.data}
        
        result = self.price_service.get_price(user_id, ingredient)
        
        if result.success:
            return {
                'success': True,
                'data': {
                    'ingredient_name': result.data['ingredient_name'],
                    'price': result.data['price'],
                    'currency': result.data.get('currency', 'USD'),
                    'unit': result.data.get('unit', 'ton'),
                    'source': result.source
                }
            }
        else:
            return {'success': False, 'error': result.error_message}
    
    def _handle_price_manage(self, user_id: str, message: str) -> Dict[str, Any]:
        """处理价格管理"""
        import re
        
        if re.search(r'(列出|所有)', message):
            # 列出所有价格
            public = self.price_service.list_public_prices()
            private = self.price_service.list_private_prices(user_id)
            
            return {
                'success': True,
                'data': {
                    'public_prices': public.data,
                    'private_prices': private.data,
                    'total': public.data['total'] + private.data['total']
                }
            }
        
        # 设置价格
        ingredient_map = {
            '玉米': 'Corn, grain',
            '豆粕': 'Soybean meal, 48%',
            'corn': 'Corn, grain',
        }
        
        ingredient = None
        for key, value in ingredient_map.items():
            if key in message.lower():
                ingredient = value
                break
        
        if not ingredient:
            return {'success': False, 'error': '请指定原料名称'}
        
        # 提取价格数字
        match = re.search(r'(\d+(?:\.\d+)?)', message)
        if not match:
            return {'success': False, 'error': '请提供价格数字'}
        
        price = float(match.group(1))
        
        result = self.price_service.set_private_price(user_id, ingredient, price)
        
        if result.success:
            return {
                'success': True,
                'data': {'message': f'已设置 {ingredient} 私有价格为 ${price}/ton'}
            }
        else:
            return {'success': False, 'error': result.error_message}
    
    def _handle_customer_manage(self, user_id: str, message: str) -> Dict[str, Any]:
        """处理客户管理"""
        import re
        
        if re.search(r'(添加|创建)', message):
            # 提取客户信息
            name_match = re.search(r'客户(.+?)(，|,|$)', message)
            phone_match = re.search(r'电话\s*(\d+)', message)
            
            if not name_match:
                return {'success': False, 'error': '请提供客户名称'}
            
            customer_data = {
                'name': name_match.group(1).strip(),
                'phone': phone_match.group(1) if phone_match else None
            }
            
            result = self.customer_service.create_customer(user_id, customer_data)
            
            if result.success:
                return {'success': True, 'data': result.data}
            else:
                return {'success': False, 'error': result.error_message}
        
        elif re.search(r'(列出|查看)', message):
            result = self.customer_service.list_customers(user_id)
            return {'success': True, 'data': result.data}
        
        else:
            return {'success': False, 'error': '客户管理操作未识别'}
    
    def _handle_quote_generate(self, user_id: str, message: str) -> Dict[str, Any]:
        """处理报价生成"""
        return {
            'success': True,
            'data': {
                'message': '报价生成功能需要指定客户和配方，请提供更多信息'
            }
        }
    
    def _handle_nutrition_analysis(self, user_id: str, message: str) -> Dict[str, Any]:
        """处理营养分析"""
        return {
            'success': True,
            'data': {
                'message': '营养分析功能需要指定配方名称'
            }
        }
    
    def get_session_state(self, session_id: str):
        """获取会话状态"""
        return self.session_manager.get_state(session_id)
    
    def clear_session(self, session_id: str):
        """清除会话"""
        self.session_manager.clear_state(session_id)