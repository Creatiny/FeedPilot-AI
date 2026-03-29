"""
FeedSales AI - Nutrition Analysis Skill

Analyze formula nutrition composition and compare with NRC standards
Target market: North America
"""

import logging
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class NutritionAnalysisSkill:
    """Nutrition analysis skill"""
    
    def __init__(self, formula_repo=None, price_repo=None):
        """
        Initialize skill
        
        Args:
            formula_repo: Formula repository
            price_repo: Price repository (for ingredient nutrition data)
        """
        self.formula_repo = formula_repo
        self.price_repo = price_repo
    
    # NRC nutrition standards (minimum requirements)
    NRC_STANDARDS = {
        'Swine': {
            'Nursery': {'crude_protein': 18.0, 'lysine': 1.2, 'calcium': 0.8, 'phosphorus': 0.6},
            'Growing': {'crude_protein': 15.0, 'lysine': 0.9, 'calcium': 0.65, 'phosphorus': 0.45},
            'Finishing': {'crude_protein': 13.0, 'lysine': 0.7, 'calcium': 0.55, 'phosphorus': 0.35},
        },
        'Beef Cattle': {
            'Starter': {'crude_protein': 16.0, 'calcium': 0.7, 'phosphorus': 0.5},
            'Growing': {'crude_protein': 14.0, 'calcium': 0.65, 'phosphorus': 0.45},
            'Finishing': {'crude_protein': 12.0, 'calcium': 0.6, 'phosphorus': 0.4},
        },
        'Dairy Cattle': {
            'Calf': {'crude_protein': 20.0, 'calcium': 0.8, 'phosphorus': 0.55},
            'Heifer': {'crude_protein': 16.0, 'calcium': 0.7, 'phosphorus': 0.45},
            'Lactating': {'crude_protein': 17.0, 'calcium': 0.8, 'phosphorus': 0.5},
        },
        'Broiler': {
            'Starter': {'crude_protein': 23.0, 'calcium': 1.0, 'phosphorus': 0.7},
            'Grower': {'crude_protein': 21.0, 'calcium': 0.95, 'phosphorus': 0.65},
            'Finisher': {'crude_protein': 19.0, 'calcium': 0.9, 'phosphorus': 0.6},
        },
        'Layer': {
            'Starter': {'crude_protein': 20.0, 'calcium': 1.0, 'phosphorus': 0.6},
            'Grower': {'crude_protein': 17.0, 'calcium': 0.9, 'phosphorus': 0.55},
            'Laying': {'crude_protein': 16.5, 'calcium': 3.5, 'phosphorus': 0.5},
        },
    }
    
    # Ingredient nutrition composition (per kg, typical values)
    INGREDIENT_NUTRITION = {
        'Corn, grain': {'crude_protein': 8.5, 'lysine': 0.25, 'calcium': 0.02, 'phosphorus': 0.27},
        'Soybean meal, 48%': {'crude_protein': 48.0, 'lysine': 3.0, 'calcium': 0.3, 'phosphorus': 0.6},
        'Fish meal, 65%': {'crude_protein': 65.0, 'lysine': 5.0, 'calcium': 4.0, 'phosphorus': 2.5},
        'Wheat middlings': {'crude_protein': 16.0, 'lysine': 0.5, 'calcium': 0.1, 'phosphorus': 0.5},
        'Alfalfa hay, early bloom': {'crude_protein': 18.0, 'lysine': 0.7, 'calcium': 1.5, 'phosphorus': 0.25},
        'Corn silage': {'crude_protein': 8.0, 'lysine': 0.2, 'calcium': 0.25, 'phosphorus': 0.22},
        'Premix, swine': {'crude_protein': 0, 'lysine': 0, 'calcium': 20.0, 'phosphorus': 10.0},  # Mineral premix
        'Premix, beef': {'crude_protein': 0, 'lysine': 0, 'calcium': 18.0, 'phosphorus': 9.0},
        'Premix, dairy': {'crude_protein': 0, 'lysine': 0, 'calcium': 20.0, 'phosphorus': 10.0},
        'Premix, broiler': {'crude_protein': 0, 'lysine': 0, 'calcium': 20.0, 'phosphorus': 10.0},
        'Premix, layer': {'crude_protein': 0, 'lysine': 0, 'calcium': 25.0, 'phosphorus': 8.0},
        'Dicalcium phosphate': {'crude_protein': 0, 'lysine': 0, 'calcium': 22.0, 'phosphorus': 18.5},
        'Limestone, ag': {'crude_protein': 0, 'lysine': 0, 'calcium': 38.0, 'phosphorus': 0},
        'Salt, white': {'crude_protein': 0, 'lysine': 0, 'calcium': 0, 'phosphorus': 0},
        'L-Lysine HCl': {'crude_protein': 0, 'lysine': 78.0, 'calcium': 0, 'phosphorus': 0},
    }
    
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
            logger.info(f"Executing nutrition analysis (user: {user_id})")
            
            # Extract formula name from message
            formula_name = self._extract_formula_name(message)
            
            if not formula_name:
                return self._error("Formula name not found, please specify the formula")
            
            # Get formula from repository
            formula = self.formula_repo.get_formula(user_id, formula_name)
            
            if not formula:
                return self._error(f"Formula '{formula_name}' not found")
            
            # Calculate nutrition composition
            nutrition_result = self._calculate_nutrition(formula)
            
            # Compare with NRC standards
            comparison = self._compare_with_nrc(formula, nutrition_result)
            
            logger.info(f"Nutrition analysis completed: {formula_name}")
            return self._success({
                'formula_name': formula_name,
                'nutrition_composition': nutrition_result,
                'nrc_comparison': comparison,
                'recommendations': self._generate_recommendations(comparison)
            })
            
        except Exception as e:
            logger.error(f"Nutrition analysis failed: {e}")
            return self._error(f"Analysis failed: {str(e)}")
    
    def _extract_formula_name(self, message: str) -> Optional[str]:
        """Extract formula name from message"""
        # Match: analyze nutrition of xxx
        match = re.search(r'analyze\s+(.*?)\s+(?:nutrition|formula)', message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Match: xxx formula nutrition
        match = re.search(r'(.*?)\s+formula\s+nutrition', message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Match: nutrition analysis for xxx
        match = re.search(r'nutrition\s+analysis\s+for\s+(.+)', message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def _calculate_nutrition(self, formula: Dict) -> Dict:
        """Calculate nutrition composition from formula ingredients"""
        ingredients = formula.get('ingredients', [])
        
        total_nutrition = {
            'crude_protein': 0.0,
            'lysine': 0.0,
            'calcium': 0.0,
            'phosphorus': 0.0,
        }
        
        ingredient_details = []
        
        for ingredient in ingredients:
            name = ingredient.get('name')
            ratio = ingredient.get('ratio', 0)  # percentage
            
            # Get ingredient nutrition data
            nutrition = self.INGREDIENT_NUTRITION.get(name, {})
            
            # Calculate contribution (ratio% of 100kg formula)
            contribution = {}
            for nutrient, value in nutrition.items():
                if nutrient in total_nutrition:
                    contrib = value * ratio / 100.0
                    total_nutrition[nutrient] += contrib
                    contribution[nutrient] = round(contrib, 2)
            
            ingredient_details.append({
                'name': name,
                'ratio': ratio,
                'nutrition': nutrition,
                'contribution': contribution
            })
        
        # Round totals
        for nutrient in total_nutrition:
            total_nutrition[nutrient] = round(total_nutrition[nutrient], 2)
        
        return {
            'total': total_nutrition,
            'ingredient_details': ingredient_details
        }
    
    def _compare_with_nrc(self, formula: Dict, nutrition_result: Dict) -> Dict:
        """Compare with NRC standards"""
        animal_type = formula.get('animal_type', 'Swine')
        stage = formula.get('stage_type', 'Nursery')
        
        # Get NRC standard
        nrc_standard = self.NRC_STANDARDS.get(animal_type, {}).get(stage, {})
        
        if not nrc_standard:
            return {
                'status': 'no_standard',
                'message': f"No NRC standard found for {animal_type} {stage}"
            }
        
        total = nutrition_result['total']
        
        comparison = {}
        for nutrient, standard_value in nrc_standard.items():
            actual_value = total.get(nutrient, 0)
            difference = actual_value - standard_value
            percentage = (actual_value / standard_value * 100) if standard_value > 0 else 0
            
            comparison[nutrient] = {
                'actual': actual_value,
                'standard': standard_value,
                'difference': round(difference, 2),
                'percentage': round(percentage, 1),
                'status': 'met' if actual_value >= standard_value else 'deficient'
            }
        
        return {
            'animal_type': animal_type,
            'stage': stage,
            'comparison': comparison,
            'overall_status': 'pass' if all(c['status'] == 'met' for c in comparison.values()) else 'fail'
        }
    
    def _generate_recommendations(self, comparison: Dict) -> List[str]:
        """Generate recommendations based on comparison"""
        if comparison.get('status') == 'no_standard':
            return ["Unable to generate recommendations without NRC standard"]
        
        recommendations = []
        comp_data = comparison.get('comparison', {})
        
        for nutrient, data in comp_data.items():
            if data['status'] == 'deficient':
                deficit = data['standard'] - data['actual']
                recommendations.append(
                    f"Increase {nutrient} by {round(deficit, 2)}% to meet NRC standard ({data['standard']}%)"
                )
        
        if not recommendations:
            recommendations.append("Formula meets all NRC nutrition standards")
        
        return recommendations
    
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
def create_skill(formula_repo, price_repo=None):
    """Create skill instance"""
    return NutritionAnalysisSkill(formula_repo, price_repo)