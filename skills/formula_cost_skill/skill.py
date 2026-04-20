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
                return self._error("Calculation service is not available. Please try again later.")
            
            # Extract formula name
            formula_name = self._extract_formula_name(message)
            if not formula_name:
                return self._error(
                    "I couldn't identify a formula name in your request. "
                    "Please try something like: 'cost for Nursery Diet 1' or 'calculate Grower Diet 1 price'."
                )
            
            # Calculate cost via service
            result = self.calculation_service.calculate_cost(user_id, formula_name)
            
            if result.success:
                data = result.data
                return self._format_success(data, result.source)
            else:
                # Translate common Chinese error messages to English
                err = result.error_message or ''
                if '不存在' in err or 'not found' in err.lower():
                    return self._error(
                        f"I couldn't find a formula named '{formula_name}' in our database. "
                        "Would you like me to list the available formulas, or add this as a private formula?"
                    )
                return self._error(
                    f"I was unable to calculate the cost for '{formula_name}'. "
                    "Please check the formula name and try again."
                )
                
        except Exception as e:
            logger.error(f"FormulaCostSkill error: {e}")
            return self._error("An unexpected error occurred while calculating the formula cost. Please try again.")
    
    def _format_success(self, data: Dict, source: str) -> Dict:
        """Format successful result as natural language with clean data"""
        formula_name = data['formula_name']
        total_cost = data['total_cost']
        cost_per_kg = round(total_cost / 1000, 4)
        animal_type = data.get('animal_type', '')
        stage = data.get('stage_type', '')
        
        # Build ingredient breakdown — only include meaningful fields
        details = []
        for d in data.get('details', []):
            item = {
                'name': d['name'],
                'ratio': d['ratio'],
                'price': d['price'],
                'cost': d['cost'],
            }
            # Only include ingredient_code if it's non-empty
            if d.get('ingredient_code'):
                item['ingredient_code'] = d['ingredient_code']
            # Only include price_source if meaningful (not 'default' for empty codes)
            if d.get('price_source') and d['price_source'] != 'default':
                item['price_source'] = d['price_source']
            details.append(item)
        
        # Build price_sources — remove empty keys and default-only entries
        raw_sources = data.get('price_sources', {})
        price_sources = {k: v for k, v in raw_sources.items() if k and v and v != 'default'}
        
        # Build natural language summary
        animal_info = f" for {animal_type}" if animal_type else ""
        stage_info = f" ({stage} stage)" if stage else ""
        summary = (
            f"The estimated cost for {formula_name}{animal_info}{stage_info} is "
            f"${total_cost:.2f}/ton (${cost_per_kg:.4f}/kg)."
        )
        
        missing = data.get('missing_prices', [])
        if missing:
            summary += f" Note: default prices were used for: {', '.join(missing)}."
        
        return self._success({
            'summary': summary,
            'formula_name': formula_name,
            'animal_type': animal_type or None,
            'stage': stage or None,
            'cost_per_ton': total_cost,
            'cost_per_kg': cost_per_kg,
            'currency': data.get('currency', 'USD'),
            'details': details[:15],  # Limit details
            'price_sources': price_sources if price_sources else None,
            'source': source,
        })
    
    def _extract_formula_name(self, message: str) -> Optional[str]:
        """Extract formula name from message"""
        # Match: cost for xxx / price for xxx
        match = re.search(r'(?:cost|price)\s+for\s+(.+)', message, re.IGNORECASE)
        if match:
            name = match.group(1).strip().rstrip('?.!')
            if len(name) < 50:
                return name

        # Match: calculate xxx cost / xxx cost / xxx price
        match = re.search(r'(?:calculate\s+)?(.+?)\s+(?:cost|price)', message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) < 50:
                return name

        # Match: how much is xxx / how much does xxx cost
        match = re.search(r'how\s+much\s+(?:is|does\s+)?(.+?)(?:\s+cost)?(?:\s*$|\?)', message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) < 50:
                return name

        # Match: xxx成本 (Chinese)
        match = re.search(r'(.+?)成本', message)
        if match:
            name = match.group(1).strip()
            if len(name) < 50:
                return name

        # Match: xxx多少钱 (Chinese)
        match = re.search(r'(.+?)(多少钱|多少钱一吨)', message)
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
