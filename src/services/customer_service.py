"""
FeedSales AI - CustomerService

客户管理服务，支持多租户隔离
import sys as _sys
from pathlib import _Path
if _Path(__file__).parent.parent not in _sys.path:
    _sys.path.insert(0, str(_Path(__file__).parent.parent))
字段与 schema.sql 一致：id, owner_open_id, name, phone, address, animal_type, scale, notes, version
"""

import logging
from typing import Dict, List, Optional
from ..database.pool import DatabasePool
from ..result_types import ServiceResult

logger = logging.getLogger(__name__)


class CustomerService:
    """客户管理服务"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
    
    def get_customer(self, user_id: str, name: str) -> ServiceResult:
        """获取客户（精确匹配）"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone, address, animal_type, scale, notes, created_at
                FROM customers
                WHERE owner_open_id = ? AND name = ?
            ''', (user_id, name))
            
            row = cursor.fetchone()
            if row:
                return ServiceResult(success=True, data=dict(row))
            
            return ServiceResult(
                success=False,
                error_code='E002',
                error_message=f"Customer '{name}' not found"
            )
    
    def list_customers(self, user_id: str) -> ServiceResult:
        """列出用户所有客户"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone, address, animal_type, scale, notes, created_at
                FROM customers
                WHERE owner_open_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            
            customers = [dict(row) for row in cursor.fetchall()]
            
            return ServiceResult(
                success=True,
                data={'customers': customers, 'total': len(customers)}
            )
    
    def create_customer(self, user_id: str, data: Dict) -> ServiceResult:
        """创建客户"""
        if not data.get('name'):
            return ServiceResult(
                success=False,
                error_code='E001',
                error_message='Customer name cannot be empty'
            )
        
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute(
                "SELECT id FROM customers WHERE owner_open_id = ? AND name = ?",
                (user_id, data['name'])
            )
            if cursor.fetchone():
                return ServiceResult(
                    success=False,
                    error_code='E004',
                    error_message=f"Customer '{data['name']}' already exists"
                )
            
            # 插入客户（字段与 schema.sql 一致）
            cursor.execute('''
                INSERT INTO customers (owner_open_id, name, phone, address, animal_type, scale, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data['name'],
                data.get('phone'),
                data.get('address'),
                data.get('animal_type'),
                data.get('scale'),
                data.get('notes')
            ))
            
            customer_id = cursor.lastrowid
            conn.commit()
            
            return ServiceResult(
                success=True,
                data={
                    'id': customer_id,
                    'name': data['name'],
                    'phone': data.get('phone'),
                    'address': data.get('address'),
                    'animal_type': data.get('animal_type'),
                    'scale': data.get('scale'),
                    'notes': data.get('notes')
                }
            )
    
    def update_customer(self, user_id: str, customer_id: int, data: Dict) -> ServiceResult:
        """更新客户"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查权限
            cursor.execute(
                "SELECT id FROM customers WHERE id = ? AND owner_open_id = ?",
                (customer_id, user_id)
            )
            if not cursor.fetchone():
                return ServiceResult(
                    success=False,
                    error_code='E003',
                    error_message='No permission to update this customer or customer not found'
                )
            
            # 构建更新语句（字段与 schema.sql 一致）
            update_fields = []
            update_values = []
            
            for field in ['name', 'phone', 'address', 'animal_type', 'scale', 'notes']:
                if field in data:
                    update_fields.append(f'{field} = ?')
                    update_values.append(data[field])
            
            if not update_fields:
                return ServiceResult(
                    success=False,
                    error_code='E001',
                    error_message='No fields to update'
                )
            
            update_values.extend([customer_id, user_id])
            
            cursor.execute(f'''
                UPDATE customers 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_open_id = ?
            ''', update_values)
            
            conn.commit()
            
            # 返回更新后的客户
            cursor.execute(
                "SELECT id, name, phone, address, animal_type, scale, notes FROM customers WHERE id = ?",
                (customer_id,)
            )
            customer = dict(cursor.fetchone())
            
            return ServiceResult(success=True, data=customer)
    
    def delete_customer(self, user_id: str, customer_id: int) -> ServiceResult:
        """删除客户"""
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查权限
            cursor.execute(
                "SELECT id FROM customers WHERE id = ? AND owner_open_id = ?",
                (customer_id, user_id)
            )
            if not cursor.fetchone():
                return ServiceResult(
                    success=False,
                    error_code='E003',
                    error_message='No permission to delete this customer or customer not found'
                )
            
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
            
            return ServiceResult(success=True)