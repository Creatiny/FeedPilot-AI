"""
FeedSales AI - Formula Cost Skill

Calculate feed formula cost. Uses CalculationService (v1.7 architecture).

Requires CalculationService to be injected at initialization.
"""

import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FormulaCostSkill:
    """Formula cost calculation skill"""
    
    def __init__(self, calculation_service=None):
        """
        Initialize skill
        
        Args:
            calculation_service: CalculationService instance (required)
        """
        self.calculation_service = calculation_service
    
    async def execute(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Execute skill - calculate formula cost
        
        Args:
            user_id: User ID
            message: Message containing formula name
            
        Returns:
            Dict with cost calculation result
        """
        try:
            logger.info(f"FormulaCostSkill.execute: {message[:50]}...")
            
            if not self.calculation_service:
                return self._error("CalculationService not initialized")
            
            # Extract formula name
            formula_name = self._extract_formula_name(message)
            if not formula_name:
                return self._error("Formula name not found in message")
            
            # Calculate cost via service
            result = self.calculation_service.calculate_cost(user_id, formula_name)
            
            if result.success:
                data = result.data
                return self._success({
                    'formula_name': data['formula_name'],
                    'animal_type': data.get('animal_type'),
                    'stage': data.get('stage_type'),
                    'cost_per_ton': data['total_cost'],
                    'cost_per_kg': round(data['total_cost'] / 1000, 4),
                    'currency': data.get('currency', 'USD'),
                    'details': data.get('details', [])[:10],  # Limit details
                    'price_sources': data.get('price_sources', {}),
                    'source': result.source,
                })
            else:
                return self._error(result.error_message)
                
        except Exception as e:
            logger.error(f"FormulaCostSkill error: {e}")
            return self._error(f"Calculation failed: {str(e)}")
    
    def _extract_formula_name(self, message: str) -> Optional[str]:
        """Extract formula name from message"""
        # Match: xxx成本
        match = re.search(r'(.+?)成本', message)
        if match:
            name = match.group(1).strip()
            if len(name) < 50:
                return name

        # Match: xxx多少钱
        match = re.search(r'(.+?)(多少钱|多少钱一吨)', message)
        if match:
            name = match.group(1).strip()
            if len(name) < 50:
                return name

        # Match: calculate xxx cost
        match = re.search(r'(?:calculate\s+)?(.+?)\s+(?:cost|price)', message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) < 50:
                return name

        # Match: cost for xxx
        match = re.search(r'(?:cost|price)\s+for\s+(.+)', message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) < 50:
                return name

        return None
    
    def _success(self, data: Dict) -> Dict:
        return {'success': True, 'data': data}
    
    def _error(self, msg: str) -> Dict:
        return {'success': False, 'error': msg}


def create_skill(calculation_service):
    """Factory function - requires CalculationService"""
    return FormulaCostSkill(calculation_service)