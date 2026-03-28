"""
Test formula cost skill with SQLite database
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.formula_cost_skill.skill import FormulaCostSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_skill():
    """Test formula cost skill"""
    logger.info("=" * 60)
    logger.info("Testing Formula Cost Skill with SQLite Database")
    logger.info("=" * 60)
    
    # Initialize skill
    skill = FormulaCostSkill("data/feed_sales.db")
    
    # Test cases
    test_cases = [
        ("Nursery formula", "Calculate Nursery Diet 1 cost"),
        ("Broiler formula", "Calculate Broiler Starter cost"),
        ("Layer formula", "Calculate Layer Diet cost"),
        ("Non-existent formula", "Calculate XYZ formula cost"),
    ]
    
    for name, message in test_cases:
        logger.info(f"\nTest: {name}")
        logger.info(f"Input: {message}")
        
        result = await skill.execute("test_user", message)
        
        if result.get('success'):
            data = result.get('data', {})
            logger.info(f"✅ Success - Cost: ${data.get('cost_per_ton', 'N/A')}/ton")
            logger.info(f"   Animal: {data.get('animal_type')}")
            logger.info(f"   Stage: {data.get('stage')}")
        else:
            logger.info(f"⚠️  Expected failure - {result.get('error', 'Unknown')}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Testing completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_skill())
