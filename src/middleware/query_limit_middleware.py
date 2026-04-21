"""
FeedSales AI - Query Limit Middleware

Middleware that checks query limits before allowing requests to proceed.
"""

from typing import Dict


class QueryLimitMiddleware:
    """Middleware for checking and enforcing query limits."""
    
    # Skills that are exempt from query limits
    EXEMPT_SKILLS = {'onboarding'}
    
    def __init__(self, subscription_service):
        """
        Initialize middleware with subscription service.
        
        Args:
            subscription_service: SubscriptionService instance for checking limits
        """
        self.subscription_service = subscription_service
    
    def check_and_record(self, user_id: str, skill_name: str) -> Dict:
        """
        Check if user can make a query and record usage if allowed.
        
        Args:
            user_id: User identifier
            skill_name: Name of the skill being invoked
            
        Returns:
            dict with:
                - allowed: bool indicating if request is allowed
                - message: str with status message (if blocked or exempt)
                - remaining: int with queries remaining (if allowed)
                - exempt: bool if skill is exempt from limits
        """
        # Check if skill is exempt from limits
        if skill_name.lower() in self.EXEMPT_SKILLS:
            return {
                'allowed': True,
                'message': 'Skill exempt from query limits',
                'exempt': True
            }
        
        # Check query limit
        limit_check = self.subscription_service.check_query_limit(user_id)
        
        if not limit_check['allowed']:
            return {
                'allowed': False,
                'message': f"{limit_check['message']} Upgrade to Pro for unlimited queries."
            }
        
        # Record usage
        self.subscription_service.record_usage(user_id)
        
        # Get updated remaining count
        updated_check = self.subscription_service.check_query_limit(user_id)
        
        return {
            'allowed': True,
            'remaining': updated_check['queries_remaining'],
            'message': limit_check['message']
        }
