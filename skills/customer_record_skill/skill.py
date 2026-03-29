"""
FeedSales AI - Customer Record Skill

Manage customer records for North America feed sales
"""

import logging
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class CustomerRecordSkill:
    """Customer record management skill"""
    
    def __init__(self, customer_repo=None):
        """
        Initialize skill
        
        Args:
            customer_repo: Customer repository
        """
        self.customer_repo = customer_repo
    
    async def execute(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Execute skill
        
        Args:
            user_id: User ID
            message: User message
            
        Returns:
            Dict: Execution result
        """
        try:
            logger.info(f"Executing customer record (user: {user_id})")
            
            # Parse action from message
            action = self._parse_action(message)
            
            if action == 'add':
                return self._handle_add(user_id, message)
            elif action == 'list':
                return self._handle_list(user_id)
            elif action == 'get':
                return self._handle_get(user_id, message)
            elif action == 'update':
                return self._handle_update(user_id, message)
            elif action == 'delete':
                return self._handle_delete(user_id, message)
            else:
                return self._success({
                    'message': 'Customer record management',
                    'hint': 'Available actions: add customer, list customers, get customer [name], update customer [name], delete customer [name]'
                })
            
        except Exception as e:
            logger.error(f"Customer record failed: {e}")
            return self._error(f"Operation failed: {str(e)}")
    
    def _parse_action(self, message: str) -> str:
        """Parse action from message"""
        message_lower = message.lower()
        
        if 'add' in message_lower or 'new' in message_lower or 'create' in message_lower:
            return 'add'
        elif 'list' in message_lower or 'show' in message_lower or 'all' in message_lower:
            return 'list'
        elif 'get' in message_lower or 'find' in message_lower or 'search' in message_lower:
            return 'get'
        elif 'update' in message_lower or 'edit' in message_lower or 'modify' in message_lower:
            return 'update'
        elif 'delete' in message_lower or 'remove' in message_lower:
            return 'delete'
        
        return 'unknown'
    
    def _handle_add(self, user_id: str, message: str) -> Dict[str, Any]:
        """Handle add customer"""
        customer_data = self._extract_customer_info(message)
        
        if not customer_data.get('name'):
            return self._error("Customer name is required")
        
        customer_id = self.customer_repo.create_customer(user_id, customer_data)
        
        return self._success({
            'message': f"Customer '{customer_data['name']}' added successfully",
            'customer_id': customer_id,
            'customer': customer_data
        })
    
    def _handle_list(self, user_id: str) -> Dict[str, Any]:
        """Handle list customers"""
        customers = self.customer_repo.list_customers(user_id)
        
        if not customers:
            return self._success({
                'message': 'No customers found',
                'customers': []
            })
        
        return self._success({
            'message': f"Found {len(customers)} customers",
            'customers': customers
        })
    
    def _handle_get(self, user_id: str, message: str) -> Dict[str, Any]:
        """Handle get customer"""
        name = self._extract_customer_name(message)
        
        if not name:
            return self._error("Customer name not specified")
        
        customer = self.customer_repo.get_customer(user_id, name)
        
        if not customer:
            return self._error(f"Customer '{name}' not found")
        
        return self._success({
            'message': f"Customer '{name}' found",
            'customer': customer
        })
    
    def _handle_update(self, user_id: str, message: str) -> Dict[str, Any]:
        """Handle update customer"""
        name = self._extract_customer_name(message)
        
        if not name:
            return self._error("Customer name not specified")
        
        customer = self.customer_repo.get_customer(user_id, name)
        if not customer:
            return self._error(f"Customer '{name}' not found")
        
        customer_data = self._extract_customer_info(message)
        customer_data['name'] = name  # Keep original name
        
        success = self.customer_repo.update_customer(user_id, customer['id'], customer_data)
        
        if success:
            return self._success({
                'message': f"Customer '{name}' updated successfully",
                'customer': customer_data
            })
        else:
            return self._error(f"Failed to update customer '{name}'")
    
    def _handle_delete(self, user_id: str, message: str) -> Dict[str, Any]:
        """Handle delete customer"""
        name = self._extract_customer_name(message)
        
        if not name:
            return self._error("Customer name not specified")
        
        customer = self.customer_repo.get_customer(user_id, name)
        if not customer:
            return self._error(f"Customer '{name}' not found")
        
        success = self.customer_repo.delete_customer(user_id, customer['id'])
        
        if success:
            return self._success({
                'message': f"Customer '{name}' deleted successfully"
            })
        else:
            return self._error(f"Failed to delete customer '{name}'")
    
    def _extract_customer_name(self, message: str) -> Optional[str]:
        """Extract customer name from message"""
        # Match patterns like "get customer John" or "find John"
        patterns = [
            r'customer\s+([A-Za-z]+)',
            r'get\s+([A-Za-z]+)',
            r'find\s+([A-Za-z]+)',
            r'update\s+([A-Za-z]+)',
            r'delete\s+([A-Za-z]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_customer_info(self, message: str) -> Dict:
        """Extract customer info from message"""
        data = {}
        
        # Extract name
        name_match = re.search(r'name[:\s]+([A-Za-z\s]+)', message, re.IGNORECASE)
        if name_match:
            data['name'] = name_match.group(1).strip()
        else:
            # Try to extract name after "add/new customer"
            name_match = re.search(r'(?:add|new|create)\s+customer\s+([A-Za-z]+)', message, re.IGNORECASE)
            if name_match:
                data['name'] = name_match.group(1).strip()
        
        # Extract phone
        phone_match = re.search(r'phone[:\s]+(\d[\d\s\-]+)', message, re.IGNORECASE)
        if phone_match:
            data['phone'] = phone_match.group(1).strip()
        
        # Extract address
        address_match = re.search(r'address[:\s]+([A-Za-z0-9\s,]+)', message, re.IGNORECASE)
        if address_match:
            data['address'] = address_match.group(1).strip()
        
        # Extract animal type
        animal_match = re.search(r'(?:animal|type)[:\s]+([A-Za-z]+)', message, re.IGNORECASE)
        if animal_match:
            data['animal_type'] = animal_match.group(1).strip()
        
        # Extract scale
        scale_match = re.search(r'scale[:\s]+(\d+)', message, re.IGNORECASE)
        if scale_match:
            data['scale'] = int(scale_match.group(1))
        
        # Extract notes
        notes_match = re.search(r'notes[:\s]+(.+)', message, re.IGNORECASE)
        if notes_match:
            data['notes'] = notes_match.group(1).strip()
        
        return data
    
    def _success(self, data: Dict) -> Dict[str, Any]:
        """Success response"""
        return {
            'success': True,
            'data': data
        }
    
    def _error(self, message: str) -> Dict[str, Any]:
        """Error response"""
        return {
            'success': False,
            'error': message
        }


# Skill factory function
def create_skill(customer_repo):
    """Create skill instance"""
    return CustomerRecordSkill(customer_repo)