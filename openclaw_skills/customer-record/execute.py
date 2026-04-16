#!/usr/bin/env python3
"""
Customer Record Skill - OpenClaw Execution Wrapper

Manages customer records using v1.7 CustomerService.
"""

import sys
import os
import json
import argparse
import asyncio

# Correct workspace path
WORKSPACE = "/home/kenny/.openclaw/workspace-feedsales"
sys.path.insert(0, WORKSPACE)

from src.database.pool import DatabasePool
from src.services.customer_service import CustomerService
from skills.customer_record_skill.skill import CustomerRecordSkill


def main():
    parser = argparse.ArgumentParser(description='Customer Record Skill')
    parser.add_argument('--user-id', required=True, help='User ID')
    parser.add_argument('--message', required=True, help='User message')
    parser.add_argument('--db-path', default='/home/kenny/.openclaw/workspace-feedsales/data/feed_sales.db', help='Database path')

    args = parser.parse_args()

    try:
        # Initialize database pool
        db_pool = DatabasePool(args.db_path)

        # Initialize service
        customer_service = CustomerService(db_pool)

        # Create skill
        skill = CustomerRecordSkill(customer_service)

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
