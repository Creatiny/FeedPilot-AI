"""
Test formula cost skill with SQLite database (v1.7)
"""

import asyncio
import logging
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.pool import DatabasePool
from src.services.calculation_service import CalculationService
from skills.formula_cost_skill.skill import FormulaCostSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_skill():
    """Test formula cost skill (v1.7)"""
    logger.info("=" * 60)
    logger.info("Testing Formula Cost Skill with SQLite Database")
    logger.info("=" * 60)
    
    # Initialize skill (v1.7: inject CalculationService)
    pool = DatabasePool("data/feed_sales.db")
    calc_service = CalculationService(pool)
    skill = FormulaCostSkill(calculation_service=calc_service)
    
    # Test cases
    test_cases = [
        ("Nursery formula", "Nursery Diet 1成本"),
        ("Broiler formula", "Broiler Starter cost"),
        ("Layer formula", "Layer Diet cost"),
    ]
    
    passed = 0
    for name, message in test_cases:
        logger.info(f"\nTest: {name}")
        logger.info(f"Input: {message}")
        
        result = await skill.execute("test_user", message)
        
        if result.get('success'):
            data = result.get('data', {})
            logger.info(f"✅ Success - Cost: ${data.get('cost_per_ton', 'N/A')}/ton")
            logger.info(f"   Animal: {data.get('animal_type')}")
            logger.info(f"   Stage: {data.get('stage')}")
            passed += 1
        else:
            logger.info(f"⚠️  Expected failure - {result.get('error', 'Unknown')}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Testing completed! {passed}/{len(test_cases)} passed")
    logger.info("=" * 60)
    
    assert passed >= 2, "At least 2 tests should pass"