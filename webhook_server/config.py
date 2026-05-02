"""Webhook server configuration."""
import os

# Database
DB_PATH = os.environ.get(
    "FEEDPILOT_DB",
    "/tmp/feedpilot-ai/data/feed_sales.db",
)

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")

# Gumroad
GUMROAD_WEBHOOK_SECRET = os.environ.get("GUMROAD_WEBHOOK_SECRET", "")

# Server
HOST = os.environ.get("WEBHOOK_HOST", "127.0.0.1")
PORT = int(os.environ.get("WEBHOOK_PORT", "8080"))

# Subscription plans (must match subscription_plans table)
PLAN_IDS = {
    "free": 1,
    "starter": 2,
    "pro": 3,
}

# Subscription duration in days
SUBSCRIPTION_DAYS = {
    "starter_monthly": 30,
    "starter_yearly": 365,
    "pro_monthly": 30,
    "pro_yearly": 365,
}
