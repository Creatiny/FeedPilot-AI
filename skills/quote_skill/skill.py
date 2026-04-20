"""
FeedSales AI - Quote Generation Skill

Generate quotes for feed formulas with profit margin.
Uses CalculationService (v1.7 architecture: Skill → Service → Repository)

Requires CalculationService to be injected at initialization.
"""

import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class QuoteSkill:
    """Quote generation skill"""

    def __init__(self, calculation_service=None):
        """
        Initialize skill

        Args:
            calculation_service: CalculationService instance (required)
        """
        self.calculation_service = calculation_service

    async def execute(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Execute skill - generate quote

        Args:
            user_id: User ID
            message: Message containing formula name, customer name, and optional margin

        Returns:
            Dict with quote data
        """
        try:
            logger.info(f"QuoteSkill.execute: {message[:50]}...")

            if not self.calculation_service:
                return self._error("Calculation service is not available. Please try again later.")

            # Parse message
            formula_name, customer_name, margin = self._parse_quote_request(message)

            if not formula_name:
                return self._error(
                    "I couldn't identify a formula name. "
                    "Try: 'quote for Nursery Diet 1 to Smith Farm'"
                )

            if not customer_name:
                return self._error(
                    "I couldn't identify a customer name. "
                    "Try: 'quote for Nursery Diet 1 to Smith Farm'"
                )

            if margin is not None and (margin < 0 or margin > 100):
                return self._error("Margin must be between 0 and 100%")

            # Generate quote
            result = self.calculation_service.generate_quote(
                user_id, formula_name, customer_name, margin or 0.0
            )

            if result.success:
                return self._format_quote(result.data)
            else:
                return self._error(f"Failed to generate quote: {result.error_message}")

        except Exception as e:
            logger.error(f"QuoteSkill error: {e}")
            return self._error(f"An unexpected error occurred: {str(e)}")

    def _parse_quote_request(self, message: str) -> tuple:
        """Parse quote request message into formula name, customer name, and margin"""
        # Pattern: quote for [formula] to [customer] with [X]% margin
        match = re.search(
            r'(?:quote|offer|price)\s+(?:for|of)\s+(.+?)\s+(?:to|for)\s+([A-Za-z][A-Za-z\s]+?)(?:\s+with\s+(\d+(?:\.\d+)?)\s*%?\s*margin)?$',
            message, re.IGNORECASE
        )
        if match:
            formula = match.group(1).strip()
            customer = match.group(2).strip()
            margin = float(match.group(3)) if match.group(3) else None
            return formula, customer, margin

        # Pattern: [formula] quote to [customer]
        match = re.search(
            r'^(.+?)\s+(?:quote|offer)\s+(?:to|for)\s+([A-Za-z][A-Za-z\s]+?)(?:\s+with\s+(\d+(?:\.\d+)?)\s*%?\s*margin)?$',
            message, re.IGNORECASE
        )
        if match:
            formula = match.group(1).strip()
            customer = match.group(2).strip()
            margin = float(match.group(3)) if match.group(3) else None
            return formula, customer, margin

        # Pattern: quote [formula] for [customer]
        match = re.search(
            r'(?:quote|offer)\s+(.+?)\s+(?:for|to)\s+([A-Za-z][A-Za-z\s]+?)(?:\s+with\s+(\d+(?:\.\d+)?)\s*%?\s*margin)?$',
            message, re.IGNORECASE
        )
        if match:
            formula = match.group(1).strip()
            customer = match.group(2).strip()
            margin = float(match.group(3)) if match.group(3) else None
            return formula, customer, margin

        return None, None, None

    def _format_quote(self, quote: Dict) -> Dict:
        """Format quote as natural language response"""
        customer = quote['customer']
        formula = quote['formula']
        base = quote['base_cost_per_ton']
        margin = quote['margin_percent']
        margin_amt = quote['margin_amount']
        price = quote['quote_price_per_ton']

        summary = f"QUOTE #{quote['quote_number']}\n"
        summary += f"Date: {quote['quote_date']} | Valid for {quote['validity_days']} days\n"
        summary += f"\n"
        summary += f"TO: {customer['name']}\n"
        if customer.get('phone'):
            summary += f"Phone: {customer['phone']}\n"
        if customer.get('address'):
            summary += f"Address: {customer['address']}\n"
        summary += f"\n"
        summary += f"Formula: {formula['name']}\n"
        if formula.get('animal_type'):
            summary += f"Type: {formula['animal_type']} ({formula.get('stage_type', '')})"

        summary += f"\n"
        summary += f"{'='*40}\n"
        summary += f"Base Cost:        ${base:.2f}/ton\n"
        if margin > 0:
            summary += f"Margin ({margin}%):  +${margin_amt:.2f}/ton\n"
            summary += f"{'='*40}\n"
        summary += f"QUOTE PRICE:      ${price:.2f}/ton\n"
        summary += f"{'='*40}\n"

        if margin > 0:
            summary += f"\nMargin Breakdown:\n"
            summary += f"  Cost: ${base:.2f}/ton\n"
            summary += f"  + Margin ({margin}%): ${margin_amt:.2f}/ton\n"
            summary += f"  = Quote: ${price:.2f}/ton\n"

        summary += f"\nNote: {quote['notes']}"

        return self._success({
            'quote_number': quote['quote_number'],
            'quote_date': quote['quote_date'],
            'customer': customer,
            'formula': formula,
            'base_cost_per_ton': base,
            'margin_percent': margin,
            'margin_amount': margin_amt,
            'quote_price_per_ton': price,
            'currency': quote['currency'],
            'unit': quote['unit'],
            'ingredients': quote['ingredients'][:10],
            'formula_source': quote.get('formula_source'),
            'validity_days': quote['validity_days'],
            'summary': summary,
        })

    def _success(self, data: Dict) -> Dict:
        return {'success': True, 'data': data}

    def _error(self, msg: str) -> Dict:
        return {'success': False, 'error': msg}


def create_skill(calculation_service):
    """Factory function - requires CalculationService"""
    return QuoteSkill(calculation_service)
