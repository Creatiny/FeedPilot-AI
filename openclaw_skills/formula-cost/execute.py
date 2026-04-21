#!/usr/bin/env python3
"""
Formula Cost Skill - OpenClaw Execution Wrapper

Calculates feed formula cost using v1.7 Service layer.
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
from src.services.calculation_service import CalculationService
from skills.formula_cost_skill.skill import FormulaCostSkill


def main():
    parser = argparse.ArgumentParser(description='Formula Cost Skill')
    parser.add_argument('--user-id', required=True, help='User ID')
    parser.add_argument('--message', required=True, help='User message')
    parser.add_argument('--db-path', default=f'{WORKSPACE}/data/feed_sales.db', help='Database path')

    args = parser.parse_args()

    try:
        # Initialize database pool
        db_pool = DatabasePool(args.db_path)

        # Initialize services
        calculation_service = CalculationService(db_pool)

        # Create skill
        skill = FormulaCostSkill(calculation_service)

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
