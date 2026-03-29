"""
FeedSales AI - CustomerService

客户管理服务，支持多租户隔离
"""

import logging
from typing import Dict, List, Optional
from ..database.pool import DatabasePool
from ..types import ServiceResult

logger = logging.getLogger(__name__)


class CustomerService:
    """客户管理服务"""
    
    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool
    
    def get_customer(self, user_id: str, name: str) -> ServiceResult:
        """
        获取客户
        
        Args:
            user_id: 用户 ID
            name: 客户名称
            
        Returns:
            ServiceResult: 包含客户数据
        """
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, company, phone, email, region, notes, created_at
                FROM customers
                WHERE owner_open_id = ? AND name = ?
            ''', (user_id, name))
            
            row = cursor.fetchone()
            if row:
                return ServiceResult(success=True, data=dict(row))
            
            return ServiceResult(
                success=False,
                error_code='E002',
                error_message=f"客户 '{name}' 不存在"
            )
    
    def list_customers(self, user_id: str) -> ServiceResult:
        """
        列出用户所有客户
        
        Args:
            user_id: 用户 ID
            
        Returns:
            ServiceResult: 包含客户列表
        """
        with self.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, company, phone, email, region, notes, created_at
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
        """
        创建客户
        
        Args:
            user_id: 用户 ID
            data: 客户数据
            
        Returns:
            ServiceResult: 包含创建的客户
        """
        # 验证必填字段
        if not data.get('name'):
            return ServiceResult(
                success=False,
                error_code='E001',
                error_message='客户名称不能为空'
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
                    error_message=f"客户 '{data['name']}' 已存在"
                )
            
            # 插入客户
            cursor.execute('''
                INSERT INTO customers (owner_open_id, name, company, phone, email, region, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data['name'],
                data.get('company'),
                data.get('phone'),
                data.get('email'),
                data.get('region'),
                data.get('notes')
            ))
            
            customer_id = cursor.lastrowid
            conn.commit()
            
            # 返回创建的客户
            return ServiceResult(
                success=True,
                data={
                    'id': customer_id,
                    'name': data['name'],
                    'company': data.get('company'),
                    'phone': data.get('phone'),
                    'email': data.get('email'),
                    'region': data.get('region'),
                    'notes': data.get('notes')
                }
            )
    
    def update_customer(self, user_id: str, customer_id: int, data: Dict) -> ServiceResult:
        """
        更新客户
        
        Args:
            user_id: 用户 ID
            customer_id: 客户 ID
            data: 更新数据
            
        Returns:
            ServiceResult: 包含更新后的客户
        """
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
                    error_message='无权修改此客户或客户不存在'
                )
            
            # 构建更新语句
            update_fields = []
            update_values = []
            
            for field in ['name', 'company', 'phone', 'email', 'region', 'notes']:
                if field in data:
                    update_fields.append(f'{field} = ?')
                    update_values.append(data[field])
            
            if not update_fields:
                return ServiceResult(
                    success=False,
                    error_code='E001',
                    error_message='没有要更新的字段'
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
                "SELECT id, name, company, phone, email, region, notes FROM customers WHERE id = ?",
                (customer_id,)
            )
            customer = dict(cursor.fetchone())
            
            return ServiceResult(success=True, data=customer)
    
    def delete_customer(self, user_id: str, customer_id: int) -> ServiceResult:
        """
        删除客户
        
        Args:
            user_id: 用户 ID
            customer_id: 客户 ID
            
        Returns:
            ServiceResult: 操作结果
        """
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
                    error_message='无权删除此客户或客户不存在'
                )
            
            cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            conn.commit()
            
            return ServiceResult(success=True)