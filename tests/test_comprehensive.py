#!/usr/bin/env python3
"""
FeedSales AI v1.7 - Comprehensive Test Suite
105 natural language test cases covering all features
"""

import asyncio
import json
import sys
from datetime import datetime

sys.path.insert(0, str(__file__).replace('/tests/test_comprehensive.py', ''))

from skills.formula_cost_skill.skill import FormulaCostSkill
from skills.price_lookup_skill.skill import PriceLookupSkill
from skills.customer_record_skill.skill import CustomerRecordSkill
from skills.nutrition_analysis_skill.skill import NutritionAnalysisSkill


# ============================================================================
# 105 Natural Language Test Prompts
# ============================================================================

TEST_PROMPTS = {
    # -------------------------------------------------------------------------
    # 1. FORMULA COST CALCULATION (38 tests)
    # -------------------------------------------------------------------------
    "formula_cost": [
        # Swine (8)
        "How much does nursery pig feed cost per ton?",
        "What's the cost for starter feed for baby pigs?",
        "Nursery Diet 1 price",
        "Calculate growing pig diet price",
        "Finishing pig feed, how much?",
        "Sow feed during pregnancy cost",
        "Lactating sow diet price per ton",
        "Show me all pig feed options with prices",
        
        # Beef Cattle (3)
        "Beef cattle starter feed cost",
        "Price for finishing beef cattle diet",
        "Growing beef cattle feed, what's the cost?",
        
        # Dairy Cattle (3)
        "Dairy calf starter diet price",
        "Heifer grower feed cost per ton",
        "Lactating cow feed, how much?",
        
        # Broiler (3)
        "Broiler starter feed cost",
        "Broiler grower diet price",
        "Finishing broiler feed per ton",
        
        # Layer (3)
        "Layer starter feed price",
        "Growing layer diet cost",
        "Laying hen feed, how much per ton?",
        
        # Turkey (3)
        "Turkey starter diet cost",
        "Turkey grower feed price",
        "Finishing turkey feed per ton",
        
        # Sheep (4)
        "Lamb starter feed cost",
        "Finishing lamb diet price",
        "Pregnant ewe feed, how much?",
        "Lactating ewe diet per ton",
        
        # Goat (3)
        "Goat kid starter feed price",
        "Pregnant goat diet cost",
        "Lactating goat feed per ton",
        
        # Duck (3)
        "Duck starter feed cost",
        "Duck grower diet price",
        "Duck breeder feed per ton",
        
        # Pet & Aquatic (5)
        "Adult cat food price",
        "Adult dog food cost per ton",
        "Trout starter feed for fry",
        "Trout grower diet for fingerlings",
        "Catfish grower feed price",
    ],
    
    # -------------------------------------------------------------------------
    # 2. INGREDIENT PRICE QUERY (21 tests)
    # -------------------------------------------------------------------------
    "ingredient_price": [
        # Grains
        "What's corn price today?",
        "Current wheat price per ton",
        "How much is rice for feed?",
        
        # Protein Sources
        "Soybean meal price today",
        "Fish meal cost per ton",
        "DDGS price for feed",
        "Canola meal price",
        
        # Additives & Minerals
        "Dicalcium phosphate price",
        "Limestone for feed, how much?",
        "Salt price per ton",
        "L-Lysine price today",
        "Premix for swine price",
        
        # Forage
        "Alfalfa hay price",
        "Corn silage price",
        
        # Specialty
        "Molasses for feed price",
        "Show me all ingredient prices today",
        
        # Additional coverage
        "Barley feed grain price",
        "Cottonseed meal cost",
        "Grass hay cost per ton",
        "Straw bedding price",
        "DL-Methionine cost",
    ],
    
    # -------------------------------------------------------------------------
    # 3. NUTRITION ANALYSIS (10 tests)
    # -------------------------------------------------------------------------
    "nutrition": [
        "What's the protein content in Nursery Diet 1?",
        "Calcium level in broiler starter feed",
        "Phosphorus content for grower pigs",
        "Compare protein between nursery and finisher diets",
        "Does Layer Diet meet NRC standards?",
        "Lysine content in sow lactation feed",
        "Energy level in beef cattle finisher",
        "Nutrient profile for trout grower",
        "Which formula has highest protein?",
        "Analyze nutrition for all swine formulas",
    ],
    
    # -------------------------------------------------------------------------
    # 4. CUSTOMER MANAGEMENT (8 tests)
    # -------------------------------------------------------------------------
    "customer": [
        "Add new customer: John Smith, phone 555-1234, pig farmer",
        "Register client Mary Jones, raises beef cattle, Texas",
        "Find customer John",
        "Show all my customers",
        "Update John Smith's phone to 555-9999",
        "Which customers raise pigs?",
        "Delete customer Mary Jones",
        "How many customers do I have?",
    ],
    
    # -------------------------------------------------------------------------
    # 5. SMART REMINDERS (6 tests)
    # -------------------------------------------------------------------------
    "reminder": [
        "Remind me to check corn price tomorrow morning",
        "Alert me when soybean meal drops below $300",
        "Weekly feed cost report, every Monday 8am",
        "Notify when nursery feed cost exceeds $280",
        "Remind customer John's delivery date next week",
        "Show all my active reminders",
    ],
    
    # -------------------------------------------------------------------------
    # 6. LANGUAGE MODES (12 tests)
    # -------------------------------------------------------------------------
    "language_chinese": [
        "保育料1号多少钱一吨",
        "玉米今天价格",
        "添加客户张三，养猪的",
        "所有配方成本对比",
    ],
    
    "language_mixed": [
        "Nursery Diet 1 成本是多少",
        "Soybean meal 今天价格",
        "Beef Cattle Finisher 配方成本",
        "查询 Corn 价格",
    ],
    
    "language_english": [
        "cost of Nursery Diet 1",
        "today's corn price",
        "add new customer John Smith",
        "show formula cost comparison",
    ],
    
    # -------------------------------------------------------------------------
    # 7. ERROR HANDLING (10 tests)
    # -------------------------------------------------------------------------
    "error_handling": [
        "Cost of Unknown Formula XYZ",
        "Price of imaginary ingredient supergrain",
        "Calculate cost",  # no formula
        "Add customer",  # no details
        "Remind me",  # no time/task
        "Show customer Nonexistent Person",
        "Delete formula Nursery Diet 1",  # permission denied
        "Update price corn to $0",  # invalid price
        "Feed cost for dinosaur",  # invalid animal
        "What's the price?",  # no ingredient
    ],
}


class ComprehensiveTestRunner:
    """Run all 105 test cases"""
    
    def __init__(self, user_id: str = "test_user"):
        self.user_id = user_id
        self.results = []
        self.skills = {
            'formula_cost': FormulaCostSkill(),
            'price_lookup': PriceLookupSkill(),
            'customer': CustomerRecordSkill(),
            'nutrition': NutritionAnalysisSkill(),
        }
    
    async def run_category(self, category: str, prompts: list) -> dict:
        """Run tests for a category"""
        skill = self._get_skill_for_category(category)
        
        results = []
        for prompt in prompts:
            try:
                if skill:
                    result = await skill.execute(self.user_id, prompt)
                else:
                    result = {'success': False, 'error': 'Skill not implemented'}
                
                results.append({
                    'prompt': prompt,
                    'success': result.get('success', False),
                    'error': result.get('error', ''),
                    'data': result.get('data', {}),
                })
            except Exception as e:
                results.append({
                    'prompt': prompt,
                    'success': False,
                    'error': str(e),
                })
        
        passed = sum(1 for r in results if r['success'])
        return {
            'category': category,
            'total': len(prompts),
            'passed': passed,
            'failed': len(prompts) - passed,
            'success_rate': round(passed / len(prompts) * 100, 1),
            'results': results,
        }
    
    def _get_skill_for_category(self, category: str):
        """Map category to skill"""
        mapping = {
            'formula_cost': 'formula_cost',
            'ingredient_price': 'price_lookup',
            'nutrition': 'nutrition',
            'customer': 'customer',
            'language_chinese': 'formula_cost',
            'language_mixed': 'formula_cost',
            'language_english': 'formula_cost',
            'error_handling': 'formula_cost',
            'reminder': None,  # Not implemented yet
        }
        return self.skills.get(mapping.get(category))
    
    async def run_all(self) -> dict:
        """Run all test categories"""
        print("\n" + "=" * 70)
        print("FeedSales AI v1.7 - Comprehensive Test Suite")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 70)
        
        all_results = {}
        total_passed = 0
        total_tests = 0
        
        for category, prompts in TEST_PROMPTS.items():
            print(f"\n[{category}] Running {len(prompts)} tests...")
            category_result = await self.run_category(category, prompts)
            all_results[category] = category_result
            
            total_passed += category_result['passed']
            total_tests += category_result['total']
            
            status = "✅" if category_result['success_rate'] >= 80 else "⚠️"
            print(f"  {status} {category_result['passed']}/{category_result['total']} passed ({category_result['success_rate']}%)")
            
            # Show failed tests
            if category_result['failed'] > 0:
                for r in category_result['results']:
                    if not r['success']:
                        print(f"    ❌ \"{r['prompt'][:50]}...\" - {r['error'][:50]}")
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total: {total_tests} tests")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Overall Success Rate: {round(total_passed / total_tests * 100, 1)}%")
        
        return {
            'summary': {
                'total_tests': total_tests,
                'total_passed': total_passed,
                'overall_rate': round(total_passed / total_tests * 100, 1),
            },
            'categories': all_results,
        }


async def main():
    """Main entry point"""
    runner = ComprehensiveTestRunner(user_id="7972653610")
    results = await runner.run_all()
    
    # Save results to JSON
    output_file = "tests/test_results_comprehensive.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())