#!/usr/bin/env python3
"""
Nutrition Analysis Skill - OpenClaw Execution Wrapper

Analyzes formula nutrition using v1.7 FormulaService.
"""

import sys
import os
import json
import argparse
import asyncio

# Auto-detect project root from this file location
from pathlib import Path
WORKSPACE = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, WORKSPACE)

from src.database.pool import DatabasePool
from src.services.formula_service import FormulaService
from skills.nutrition_analysis_skill.skill import NutritionAnalysisSkill


def main():
    parser = argparse.ArgumentParser(description='Nutrition Analysis Skill')
    parser.add_argument('--user-id', required=True, help='User ID')
    parser.add_argument('--message', required=True, help='User message')
    parser.add_argument('--db-path', default=f'{WORKSPACE}/data/feed_sales.db', help='Database path')

    args = parser.parse_args()

    try:
        # Initialize database pool
        db_pool = DatabasePool(args.db_path)

        # Initialize service
        formula_service = FormulaService(db_pool)

        # Create skill
        skill = NutritionAnalysisSkill(formula_service)

        # Execute
        result = asyncio.run(skill.execute(args.user_id, args.message))

        # Output JSON
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
