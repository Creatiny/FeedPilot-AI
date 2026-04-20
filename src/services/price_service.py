"""
FeedSales AI - PriceService

原料价格管理服务，支持多租户隔离和私有优先查询
import sys as _sys
from pathlib import _Path
if _Path(__file__).parent.parent not in _sys.path:
    _sys.path.insert(0, str(_Path(__file__).parent.parent))
"""

import logging
from typing import Dict, List, Optional
from datetime import date
from ..database.pool import DatabasePool
from ..result_types import ServiceResult
from ..utils.ingredient_codes import generate_ingredient_code

logger = logging.getLogger(__name__)


class PriceService:
    """原料价格管理服务"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
    
    def get_price(self, user_id: str, ingredient_identifier: str) -> ServiceResult:
        """
        获取原料价格（私有优先，支持 name 或 code 识别）

        Args:
            user_id: 用户 ID
            ingredient_identifier: 原料代码（如 ING_CORN）或原料名称（如 "Corn, grain"）
                                 会自动转换为 ingredient_code 查询

        Returns:
            ServiceResult: 包含价格数据和来源
        """
        # 自动将名称转换为 code（支持传入 name 或 code）
        # 如果已经是标准格式（ING_开头），直接使用
        if ingredient_identifier.startswith('ING_'):
            ingredient_code = ingredient_identifier
        else:
            ingredient_code = generate_ingredient_code(ingredient_identifier)

        # 1. 先查私有价格（按 ingredient_code 精确查找）
        price = self._get_price_by_owner(user_id, ingredient_code)
        if price:
            return ServiceResult(
                success=True,
                data=price,
                source='private'
            )

        # 2. 再查公共价格（按 ingredient_code 精确查找）
        price = self._get_price_by_owner('system_public', ingredient_code)
        if price:
            return ServiceResult(
                success=True,
                data=price,
                source='public'
            )

        # 3. 不存在
        return ServiceResult(
            success=False,
            error_code='E002',
            error_message=f"原料 '{ingredient_identifier}' 价格不存在"
        )
    
    def get_public_price(self, ingredient_code: str) -> ServiceResult:
        """
        仅获取公共价格（按 ingredient_code 精确查找）
        
        Args:
            ingredient_code: 原料代码（如 ING_CORN）
            
        Returns:
            ServiceResult: 包含价格数据
        """
        price = self._get_price_by_owner('system_public', ingredient_code)
        if price:
            return ServiceResult(
                success=True,
                data=price,
                source='public'
            )
        
        return ServiceResult(
            success=False,
            error_code='E002',
            error_message=f"公共价格 '{ingredient_code}' 不存在"
        )
    
    def set_private_price(self, user_id: str, ingredient_name: str, 
                         price: float, source: str = 'manual',
                         expected_version: int = None) -> ServiceResult:
        """
        设置私有价格（支持乐观锁）
        
        Args:
            user_id: 用户 ID
            ingredient_name: 原料名称
            price: 价格 (USD/ton)
            source: 价格来源
            expected_version: 期望版本号（用于乐观锁，更新时必须提供）
            
        Returns:
            ServiceResult: 操作结果
        """
        if price <= 0:
            return ServiceResult(
                success=False,
                error_code='E001',
                error_message='价格必须大于 0'
            )
        
        # 生成 ingredient_code（使用共享映射表）
        ingredient_code = generate_ingredient_code(ingredient_name)
        today = date.today().isoformat()
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查现有记录版本
            cursor.execute('''
                SELECT id, version FROM ingredient_prices
                WHERE owner_open_id = ? AND ingredient_code = ? AND price_date = ?
            ''', (user_id, ingredient_code, today))
            
            existing = cursor.fetchone()
            
            if existing and expected_version is not None:
                # 乐观锁检查
                if existing['version'] != expected_version:
                    return ServiceResult(
                        success=False,
                        error_code='E006',
                        error_message='数据已被其他用户修改，请刷新后重试'
                    )
            
            # UPSERT
            if existing:
                cursor.execute('''
                    UPDATE ingredient_prices 
                    SET price = ?, source = ?, version = version + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (price, source, existing['id']))
            else:
                cursor.execute('''
                    INSERT INTO ingredient_prices 
                    (owner_open_id, ingredient_code, ingredient_name, price, price_date, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, ingredient_code, ingredient_name, price, today, source))
            
            conn.commit()
            
            return ServiceResult(success=True)
    
    def list_private_prices(self, user_id: str) -> ServiceResult:
        """
        列出用户所有私有价格
        
        Args:
            user_id: 用户 ID
            
        Returns:
            ServiceResult: 包含价格列表
        """
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ingredient_code, ingredient_name, price, currency, unit, source, price_date
                FROM ingredient_prices
                WHERE owner_open_id = ?
                ORDER BY ingredient_name
            ''', (user_id,))
            
            prices = [dict(row) for row in cursor.fetchall()]
            
            return ServiceResult(
                success=True,
                data={'prices': prices, 'total': len(prices)}
            )
    
    def list_public_prices(self) -> ServiceResult:
        """
        列出所有公共价格
        
        Returns:
            ServiceResult: 包含价格列表
        """
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ingredient_code, ingredient_name, price, currency, unit, source, price_date
                FROM ingredient_prices
                WHERE owner_open_id = 'system_public'
                ORDER BY ingredient_name
            ''', ())
            
            prices = [dict(row) for row in cursor.fetchall()]
            
            return ServiceResult(
                success=True,
                data={'prices': prices, 'total': len(prices)}
            )
    
    def _get_price_by_owner(self, owner_id: str, ingredient_code: str) -> Optional[Dict]:
        """获取指定所有者的价格（按 ingredient_code 精确查找）"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 精确匹配原料代码
            cursor.execute('''
                SELECT ingredient_code, ingredient_name, price, currency, unit, source, price_date
                FROM ingredient_prices
                WHERE owner_open_id = ? AND ingredient_code = ?
                ORDER BY price_date DESC
                LIMIT 1
            ''', (owner_id, ingredient_code))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def _batch_get_private_prices(self, user_id: str, ingredient_codes: List[str]) -> Dict:
        """批量获取私有价格（优化 N+1 查询）"""
        if not ingredient_codes:
            return {}
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 使用 ingredient_code 精确匹配
            placeholders = ','.join(['?' for _ in ingredient_codes])
            params = [user_id] + ingredient_codes
            
            cursor.execute(f'''
                SELECT ingredient_code, price, price_date
                FROM ingredient_prices
                WHERE owner_open_id = ? AND ingredient_code IN ({placeholders})
                ORDER BY price_date DESC
            ''', params)
            
            results = {}
            for row in cursor.fetchall():
                code = row['ingredient_code']
                if code not in results:
                    results[code] = {'price': row['price']}
            
            return results
    
    def _batch_get_public_prices(self, ingredient_codes: List[str]) -> Dict:
        """批量获取公共价格（优化 N+1 查询）"""
        if not ingredient_codes:
            return {}
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 使用 ingredient_code 精确匹配
            placeholders = ','.join(['?' for _ in ingredient_codes])
            params = ['system_public'] + ingredient_codes
            
            cursor.execute(f'''
                SELECT ingredient_code, price, price_date
                FROM ingredient_prices
                WHERE owner_open_id = ? AND ingredient_code IN ({placeholders})
                ORDER BY price_date DESC
            ''', params)
            
            results = {}
            for row in cursor.fetchall():
                code = row['ingredient_code']
                if code not in results:
                    results[code] = {'price': row['price']}
            
            return results
    
    def _generate_ingredient_code(self, ingredient_name: str) -> str:
        """废弃：使用 utils.ingredient_codes.generate_ingredient_code 替代"""
        return generate_ingredient_code(ingredient_name)