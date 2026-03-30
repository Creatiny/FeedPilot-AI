"""
FeedSales AI - Customer Record Skill

Manage customer records for North America feed sales
Uses CustomerService (v1.7 architecture: Skill → Service → Repository)
"""

import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CustomerRecordSkill:
    """Customer record management skill"""
    
    def __init__(self, customer_service=None):
        """
        Initialize skill
        
        Args:
            customer_service: CustomerService instance (injected)
        """
        self.customer_service = customer_service
    
    async def execute(self, user_id: str, message: str) -> Dict[str, Any]:
        """Execute skill"""
        try:
            logger.info(f"CustomerRecordSkill.execute: {message[:50]}...")
            
            if not self.customer_service:
                return self._error("CustomerService not initialized")
            
            action = self._parse_action(message)
            
            if action == 'add':
                return self._add_customer(user_id, message)
            elif action == 'list':
                return self._list_customers(user_id)
            elif action == 'get' or action == 'find':
                return self._get_customer(user_id, message)
            elif action == 'update':
                return self._update_customer(user_id, message)
            elif action == 'delete':
                return self._delete_customer(user_id, message)
            elif action == 'count':
                return self._count_customers(user_id)
            else:
                return self._success({
                    'message': 'Customer management ready',
                    'hint': 'Try: "show all customers", "add customer John"'
                })
            
        except Exception as e:
            logger.error(f"CustomerRecordSkill error: {e}")
            return self._error(f"Operation failed: {str(e)}")
    
    def _parse_action(self, message: str) -> str:
        msg = message.lower()
        if 'add' in msg or 'new' in msg or 'create' in msg:
            return 'add'
        elif 'list' in msg or 'all' in msg or 'show' in msg:
            return 'list'
        elif 'find' in msg or 'search' in msg:
            return 'find'
        elif 'get' in msg:
            return 'get'
        elif 'update' in msg or 'change' in msg:
            return 'update'
        elif 'delete' in msg or 'remove' in msg:
            return 'delete'
        elif 'how many' in msg or 'count' in msg:
            return 'count'
        return 'unknown'
    
    def _extract_name(self, message: str) -> Optional[str]:
        match = re.search(r'customer\s+([A-Za-z][A-Za-z\s]+?)(?:,|\s+(?:phone|address|animal|$))', message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r'customer\s+([A-Za-z\s]+)', message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _add_customer(self, user_id: str, message: str) -> Dict:
        name = self._extract_name(message)
        if not name:
            return self._error("Customer name required")
        
        # Extract fields
        animal_type = None
        for kw in ['pig', 'swine', 'cattle', 'beef', 'dairy', 'chicken', 'broiler', 'layer']:
            if kw in message.lower():
                animal_type = kw
                break
        
        phone_match = re.search(r'phone[:\s]*([\d\-]+)', message, re.IGNORECASE)
        phone = phone_match.group(1) if phone_match else None
        
        customer_data = {
            'name': name,
            'phone': phone,
            'notes': message,
        }
        
        result = self.customer_service.create_customer(user_id, customer_data)
        
        if result.success:
            return self._success({
                'message': f"Customer '{name}' added",
                'customer': result.data,
            })
        else:
            return self._error(result.error_message)
    
    def _list_customers(self, user_id: str) -> Dict:
        result = self.customer_service.list_customers(user_id)
        
        if result.success:
            customers = result.data.get('customers', [])
            return self._success({
                'message': f"Found {len(customers)} customers",
                'count': len(customers),
                'customers': customers,
            })
        else:
            return self._error(result.error_message)
    
    def _get_customer(self, user_id: str, message: str) -> Dict:
        name = self._extract_name(message)
        if not name:
            return self._error("Customer name required")
        
        result = self.customer_service.get_customer(user_id, name)
        
        if result.success:
            return self._success({
                'message': f"Customer found",
                'customers': [result.data],
            })
        else:
            # 尝试模糊搜索 - 先列出所有，再本地过滤
            list_result = self.customer_service.list_customers(user_id)
            if list_result.success:
                all_customers = list_result.data.get('customers', [])
                matches = [c for c in all_customers if name.lower() in c.get('name', '').lower()]
                if matches:
                    return self._success({
                        'message': f"Found {len(matches)} customer(s)",
                        'customers': matches,
                    })
            return self._error(f"Customer '{name}' not found")
    
    def _update_customer(self, user_id: str, message: str) -> Dict:
        name = self._extract_name(message)
        if not name:
            return self._error("Customer name required")
        
        phone_match = re.search(r'phone[:\s]*([\d\-]+)', message, re.IGNORECASE)
        if not phone_match:
            return self._error("New phone value required")
        
        # 先查找客户
        result = self.customer_service.get_customer(user_id, name)
        if not result.success:
            # 模糊搜索
            list_result = self.customer_service.list_customers(user_id)
            if list_result.success:
                matches = [c for c in list_result.data.get('customers', []) 
                          if name.lower() in c.get('name', '').lower()]
                if matches:
                    result = type('obj', (object,), {'success': True, 'data': matches[0]})()
        
        if not result.success:
            return self._error(f"Customer '{name}' not found")
        
        customer_id = result.data.get('id')
        update_result = self.customer_service.update_customer(user_id, customer_id, {'phone': phone_match.group(1)})
        
        if update_result.success:
            return self._success({'message': f"Customer '{name}' updated"})
        else:
            return self._error(update_result.error_message)
    
    def _delete_customer(self, user_id: str, message: str) -> Dict:
        name = self._extract_name(message)
        if not name:
            return self._error("Customer name required")
        
        # 先查找客户
        result = self.customer_service.get_customer(user_id, name)
        if not result.success:
            # 模糊搜索
            list_result = self.customer_service.list_customers(user_id)
            if list_result.success:
                matches = [c for c in list_result.data.get('customers', []) 
                          if name.lower() in c.get('name', '').lower()]
                if matches:
                    result = type('obj', (object,), {'success': True, 'data': matches[0]})()
        
        if not result.success:
            return self._error(f"Customer '{name}' not found")
        
        customer_id = result.data.get('id')
        delete_result = self.customer_service.delete_customer(user_id, customer_id)
        
        if delete_result.success:
            return self._success({'message': f"Customer '{name}' deleted"})
        else:
            return self._error(delete_result.error_message)
    
    def _count_customers(self, user_id: str) -> Dict:
        result = self.customer_service.list_customers(user_id)
        
        if result.success:
            count = result.data.get('total', 0)
            return self._success({
                'message': f"You have {count} customer(s)",
                'count': count,
            })
        else:
            return self._error(result.error_message)
    
    def _success(self, data: Dict) -> Dict:
        return {'success': True, 'data': data}
    
    def _error(self, msg: str) -> Dict:
        return {'success': False, 'error': msg}


def create_skill(customer_service):
    """Factory function - requires CustomerService"""
    return CustomerRecordSkill(customer_service)