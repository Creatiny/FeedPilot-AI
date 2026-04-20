"""
FeedSales AI - Nutrition Analysis Skill

Analyze formula nutrition content and compare to NRC standards
Uses FormulaService (v1.7 architecture: Skill → Service → Repository)

Requires FormulaService to be injected at initialization.
"""

import logging
import re
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# NRC Standard Reference Values
NRC_STANDARDS = {
    'Swine': {
        'Nursery': {'protein': 18.0, 'calcium': 0.70, 'phosphorus': 0.55, 'lysine': 1.2},
        'Growing': {'protein': 16.0, 'calcium': 0.60, 'phosphorus': 0.50, 'lysine': 0.9},
        'Finishing': {'protein': 14.0, 'calcium': 0.50, 'phosphorus': 0.40, 'lysine': 0.7},
        'Gestating': {'protein': 13.0, 'calcium': 0.75, 'phosphorus': 0.60, 'lysine': 0.6},
        'Lactating': {'protein': 17.0, 'calcium': 0.85, 'phosphorus': 0.70, 'lysine': 0.9},
    },
    'Broiler': {
        'Starter': {'protein': 22.0, 'calcium': 1.00, 'phosphorus': 0.45, 'lysine': 1.3},
        'Grower': {'protein': 20.0, 'calcium': 0.90, 'phosphorus': 0.40, 'lysine': 1.1},
        'Finisher': {'protein': 18.0, 'calcium': 0.80, 'phosphorus': 0.35, 'lysine': 0.9},
    },
    'Layer': {
        'Starter': {'protein': 20.0, 'calcium': 1.00, 'phosphorus': 0.50, 'lysine': 1.0},
        'Grower': {'protein': 16.0, 'calcium': 0.90, 'phosphorus': 0.40, 'lysine': 0.7},
        'Laying': {'protein': 17.0, 'calcium': 3.50, 'phosphorus': 0.35, 'lysine': 0.8},
    },
    'Beef Cattle': {
        'Starter': {'protein': 16.0, 'calcium': 0.60, 'phosphorus': 0.40, 'lysine': 0.8},
        'Growing': {'protein': 14.0, 'calcium': 0.50, 'phosphorus': 0.35, 'lysine': 0.6},
        'Finishing': {'protein': 12.0, 'calcium': 0.40, 'phosphorus': 0.30, 'lysine': 0.5},
    },
}

# Ingredient nutrition reference
INGREDIENT_NUTRITION = {
    'Corn': {'protein': 8.5, 'calcium': 0.02, 'phosphorus': 0.28, 'lysine': 0.25},
    'Soybean meal': {'protein': 48.0, 'calcium': 0.30, 'phosphorus': 0.65, 'lysine': 3.0},
    'Fish meal': {'protein': 65.0, 'calcium': 5.0, 'phosphorus': 2.8, 'lysine': 5.0},
    'Wheat': {'protein': 12.0, 'calcium': 0.05, 'phosphorus': 0.35, 'lysine': 0.35},
    'DDGS': {'protein': 28.0, 'calcium': 0.10, 'phosphorus': 0.80, 'lysine': 0.9},
    'Alfalfa': {'protein': 17.0, 'calcium': 1.40, 'phosphorus': 0.25, 'lysine': 0.8},
    'Premix': {'protein': 0, 'calcium': 20.0, 'phosphorus': 10.0, 'lysine': 2.0},
    'Limestone': {'protein': 0, 'calcium': 38.0, 'phosphorus': 0, 'lysine': 0},
    'Dicalcium phosphate': {'protein': 0, 'calcium': 18.0, 'phosphorus': 21.0, 'lysine': 0},
}


class NutritionAnalysisSkill:
    """Nutrition analysis skill - uses FormulaService"""
    
    FORMULA_KEYWORDS = [
        # Numbered diets first (longest match priority)
        "Nursery Diet 3", "Nursery Diet 2", "Nursery Diet 1",
        "Grower Diet 2", "Grower Diet 1",
        # Full names longest-first
        "Gestating Sow Diet", "Lactating Sow Diet",
        "Lactating Cow Diet", "Dairy Calf Starter", "Dairy Heifer Grower",
        "Beef Cattle Starter", "Beef Cattle Grower", "Beef Cattle Finisher",
        "Broiler Starter", "Broiler Grower", "Broiler Finisher",
        "Layer Starter", "Layer Grower", "Layer Diet",
        "Turkey Starter", "Turkey Grower", "Turkey Finisher",
        "Lamb Starter", "Lamb Finisher", "Ewe Gestating", "Ewe Lactating",
        "Goat Kid Starter", "Goat Doe Gestating", "Goat Doe Lactating",
        "Duck Starter", "Duck Grower", "Duck Breeder",
        "Cat Food Adult", "Dog Food Adult",
        "Trout Starter", "Trout Grower",
        "Catfish Grower",
        # Shorter names last
        "Finisher Diet",
    ]
    
    def __init__(self, formula_service=None):
        """
        Initialize skill
        
        Args:
            formula_service: FormulaService instance (required)
        """
        self.formula_service = formula_service
    
    async def execute(self, user_id: str, message: str) -> Dict[str, Any]:
        """Execute skill"""
        try:
            logger.info(f"NutritionAnalysisSkill.execute: {message[:50]}...")
            
            if not self.formula_service:
                return self._error("FormulaService not initialized")
            
            formula_name = self._find_formula(message)
            
            if formula_name:
                return self._analyze_formula(user_id, formula_name)
            elif 'all' in message.lower() or 'list' in message.lower():
                return self._list_formulas(user_id)
            else:
                return self._error("Formula name not found. Try: 'analyze Nursery Diet 1 nutrition'")
                
        except Exception as e:
            logger.error(f"NutritionAnalysisSkill error: {e}")
            return self._error(f"Analysis failed: {str(e)}")
    
    def _find_formula(self, message: str) -> Optional[str]:
        msg = message.lower()

        # Match keywords longest-first to avoid partial matches
        # (e.g. "Gestating Sow Diet" before "Gestating")
        for keyword in self.FORMULA_KEYWORDS:
            if keyword.lower() in msg:
                return keyword

        # Fallback: regex for numbered diets like "Nursery Diet 1"
        import re
        match = re.search(r'(Nursery Diet \d|Grower Diet \d)', message, re.IGNORECASE)
        if match:
            return match.group(1)

        return None
    
    def _analyze_formula(self, user_id: str, formula_name: str) -> Dict:
        # Get formula from service
        result = self.formula_service.get_formula(user_id, formula_name)
        
        if not result.success:
            return self._error(result.error_message)
        
        formula = result.data
        
        # Get ingredients from formula data
        ingredients = formula.get('ingredients', [])
        
        # Calculate nutrition
        nutrition = {'protein': 0, 'calcium': 0, 'phosphorus': 0, 'lysine': 0}
        
        for ing in ingredients:
            name = ing.get('name', '')
            ratio = ing.get('ratio', 0)
            ing_nutrition = self._get_ingredient_nutrition(name)
            
            for key in nutrition:
                nutrition[key] += (ing_nutrition.get(key, 0) * ratio / 100)
        
        # Get NRC standard
        nrc = self._get_nrc_standard(formula.get('animal_type'), formula.get('stage_type'))
        
        # Compare
        comparison = {}
        for key in nutrition:
            if nrc and key in nrc:
                actual = round(nutrition[key], 2)
                standard = nrc[key]
                status = '✓ Meets' if actual >= standard * 0.95 else '⚠ Below'
                comparison[key] = {'actual': actual, 'standard': standard, 'status': status}
        
        return self._success({
            'formula': formula.get('name'),
            'animal_type': formula.get('animal_type'),
            'stage': formula.get('stage_type'),
            'nutrition': {k: round(v, 2) for k, v in nutrition.items()},
            'nrc_comparison': comparison,
            'ingredients_count': len(ingredients),
            'source': result.source,
        })
    
    def _get_ingredient_nutrition(self, ingredient_name: str) -> Dict:
        name_lower = ingredient_name.lower().split(',')[0].strip()
        for key, values in INGREDIENT_NUTRITION.items():
            if key.lower() in name_lower or name_lower in key.lower():
                return values
        return {'protein': 10, 'calcium': 0.1, 'phosphorus': 0.3, 'lysine': 0.5}
    
    def _get_nrc_standard(self, animal_type: str, stage: str) -> Optional[Dict]:
        animal_map = {'Swine': 'Swine', 'Broiler': 'Broiler', 'Layer': 'Layer', 'Beef Cattle': 'Beef Cattle'}
        stage_map = {'Nursery': 'Nursery', 'Growing': 'Growing', 'Finishing': 'Finishing',
                     'Starter': 'Starter', 'Grower': 'Grower', 'Finisher': 'Finisher',
                     'Laying': 'Laying', 'Gestating': 'Gestating', 'Lactating': 'Lactating'}
        
        animal = animal_map.get(animal_type)
        stage_key = stage_map.get(stage)
        
        if animal and stage_key:
            return NRC_STANDARDS.get(animal, {}).get(stage_key)
        return None
    
    def _list_formulas(self, user_id: str) -> Dict:
        result = self.formula_service.list_formulas(user_id)
        
        if result.success:
            formulas = result.data.get('formulas', [])
            return self._success({
                'message': f'{len(formulas)} formulas available',
                'formulas': [{'name': f.get('name'), 'animal': f.get('animal_type'), 'stage': f.get('stage_type')} for f in formulas],
            })
        else:
            return self._error(result.error_message)
    
    def _success(self, data: Dict) -> Dict:
        return {'success': True, 'data': data}
    
    def _error(self, msg: str) -> Dict:
        return {'success': False, 'error': msg}


def create_skill(formula_service):
    """Factory function - requires FormulaService"""
    return NutritionAnalysisSkill(formula_service)