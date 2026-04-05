#!/usr/bin/env python3
"""
Formula Cost Skill - OpenClaw Execution Wrapper

计算饲料配方成本
"""

import sys
import os
import json
import argparse
import asyncio

# Add src to path
sys.path.insert(0, '/root/.openclaw/workspace/feed-ai-assistant/src')

from database.pool import DatabasePool
from services.calculation_service import CalculationService
from skills.formula_cost_skill.skill import FormulaCostSkill


def main():
    parser = argparse.ArgumentParser(description='Formula Cost Skill')
    parser.add_argument('--user-id', required=True, help='User ID')
    parser.add_argument('--message', required=True, help='User message')
    parser.add_argument('--db-path', default='/root/.openclaw/workspace/feed-ai-assistant/data/feed_sales.db', help='Database path')
    
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