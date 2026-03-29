"""
FeedSales AI - Formula Cost Skill

Calculate feed formula cost using CalculationService (v1.7)
"""

import logging
import sqlite3
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FormulaCostSkill:
    """Formula cost calculation skill"""
    
    def __init__(self, db_path: str = "data/feed_sales.db", calc_service=None):
        """
        Initialize skill
        
        Args:
            db_path: SQLite database path (fallback for legacy mode)
            calc_service: CalculationService instance (preferred)
        """
        self.db_path = db_path
        self.calc_service = calc_service
    
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
            logger.info(f"Executing formula cost calculation (user: {user_id})")
            
            # Extract formula name from message
            formula_name = self._extract_formula_name(message)
            if not formula_name:
                return self._error("Formula name not found, please specify the formula")
            
            # Use CalculationService if available (v1.7+)
            if self.calc_service:
                return self._execute_with_service(user_id, formula_name)
            
            # Fallback to legacy mode
            return self._execute_legacy(user_id, formula_name)
            
        except Exception as e:
            logger.error(f"Formula cost calculation failed: {e}")
            return self._error(f"Calculation failed: {str(e)}")
    
    def _execute_with_service(self, user_id: str, formula_name: str) -> Dict[str, Any]:
        """Execute using CalculationService (v1.7+)"""
        result = self.calc_service.calculate_cost(user_id, formula_name)
        
        if result.success:
            return {
                'success': True,
                'data': result.data
            }
        else:
            return {
                'success': False,
                'error': result.error_message,
                'error_code': result.error_code
            }
    
    def _execute_legacy(self, user_id: str, formula_name: str) -> Dict[str, Any]:
        """Execute using legacy direct DB access"""
        # Get formula data from database
        formula = self._get_formula(formula_name)
        if not formula:
            return self._error(f"Formula not found: {formula_name}")
        
        # Calculate cost
        cost_data = self._calculate_cost(formula)
        
        logger.info(f"Formula cost calculation completed: {formula_name}")
        return self._success(cost_data)
    
    def _get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _extract_formula_name(self, message: str) -> Optional[str]:
        """Extract formula name from message"""
        import re
        
        # Match Chinese: 计算xxx的成本
        match = re.search(r'计算(.+?)(的成本|成本)', message)
        if match:
            return match.group(1).strip()
        
        # Match: xxx成本
        match = re.search(r'(.+?)成本', message)
        if match:
            name = match.group(1).strip()
            if len(name) < 20:  # 避免匹配太长的
                return name
        
        # Match Chinese: xxx多少钱
        match = re.search(r'(.+?)(多少钱|多少钱一吨)', message)
        if match:
            return match.group(1).strip()
        
        # Match Chinese: xxx配方
        match = re.search(r'(.+?)配方', message)
        if match:
            return match.group(1).strip()
        
        # Match: calculate cost of xxx
        match = re.search(r'calculate (.*?) cost', message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            name = name.replace('formula', '').strip()
            return name
        
        # Match: xxx formula
        match = re.search(r'(.*?) formula', message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Match: xxx cost
        match = re.search(r'(.*?) cost', message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if 'how much' in name.lower():
                return None
            return name
        
        return None
    
    def _get_formula(self, formula_name: str) -> Optional[Dict]:
        """Get formula from database"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        # Get formula
        cursor.execute('''
            SELECT * FROM formulas 
            WHERE name LIKE ?
        ''', (f'%{formula_name}%',))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        formula = dict(row)
        
        # Get ingredients
        cursor.execute('''
            SELECT ingredient_name, ratio FROM formula_ingredients
            WHERE formula_id = ?
        ''', (formula['id'],))
        
        formula['ingredients'] = [
            {'name': row['ingredient_name'], 'ratio': row['ratio']}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return formula
    
    def _calculate_cost(self, formula: Dict) -> Dict[str, Any]:
        """Calculate formula cost"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        ingredients = formula.get('ingredients', [])
        total_cost = 0.0
        cost_details = []
        
        for ingredient in ingredients:
            ingredient_name = ingredient.get('name')
            ratio = ingredient.get('ratio', 0)
            
            # Get price from database
            cursor.execute('''
                SELECT price, unit FROM ingredient_prices
                WHERE ingredient_name = ?
                ORDER BY price_date DESC LIMIT 1
            ''', (ingredient_name,))
            
            price_row = cursor.fetchone()
            if price_row:
                price = price_row['price']
            else:
                # Use default price
                price = self._get_default_price(ingredient_name)
            
            # Calculate cost
            cost = price * ratio / 100.0
            total_cost += cost
            
            cost_details.append({
                'name': ingredient_name,
                'ratio': ratio,
                'price': price,
                'cost': cost
            })
        
        conn.close()
        
        return {
            'formula_name': formula.get('name'),
            'animal_type': formula.get('animal_type'),
            'stage': formula.get('stage_type'),
            'cost_per_ton': round(total_cost, 2),
            'cost_per_kg': round(total_cost / 1000, 2),
            'ingredients': cost_details,
            'currency': 'USD'
        }
    
    def _get_default_price(self, ingredient_name: str) -> float:
        """Get default price"""
        default_prices = {
            'Corn, grain': 180.00,
            'Soybean meal, 48%': 350.00,
            'Fish meal, 65%': 1800.00,
            'Premix, swine': 450.00,
            'Dicalcium phosphate': 650.00,
            'Limestone, ag': 120.00,
            'Salt, white': 150.00,
            'L-Lysine HCl': 1200.00,
        }
        return default_prices.get(ingredient_name, 300.00)
    
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
def create_skill(db_path: str = "data/feed_sales.db"):
    """Create skill instance"""
    return FormulaCostSkill(db_path)
