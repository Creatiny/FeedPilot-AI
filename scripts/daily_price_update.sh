#!/bin/bash
# FeedSales AI - Daily Price Update Cron Job
# Run this script daily to update ingredient prices

# Navigate to project directory (auto-detect from script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Activate virtual environment if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run price update script
python3 scripts/update_prices.py >> logs/price_update.log 2>&1

# Log completion
echo "Price update completed at $(date)" >> logs/price_update.log
