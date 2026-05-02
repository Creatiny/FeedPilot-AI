"""Telegram Stars payment webhook handler."""
import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, HTTPException

from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET
from . import database as db

logger = logging.getLogger("webhook.telegram")
router = APIRouter()

# Plan pricing (Stars)
PLAN_PRICING = {
    "starter_monthly": {"plan": "starter", "stars": 700, "label": "Starter Monthly", "days": 30},
    "starter_yearly":  {"plan": "starter", "stars": 7000, "label": "Starter Yearly", "days": 365},
    "pro_monthly":     {"plan": "pro", "stars": 2100, "label": "Pro Monthly", "days": 30},
    "pro_yearly":      {"plan": "pro", "stars": 21000, "label": "Pro Yearly", "days": 365},
}


def verify_telegram_secret(request: Request) -> bool:
    """Verify X-Telegram-Bot-Api-Secret-Token header."""
    if not TELEGRAM_WEBHOOK_SECRET:
        return True  # Skip if not configured
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return hmac.compare_digest(secret, TELEGRAM_WEBHOOK_SECRET)


@router.post("/webhook/telegram")
async def handle_telegram_webhook(request: Request):
    """Handle Telegram webhook (start, pre_checkout + successful_payment)."""
    if not verify_telegram_secret(request):
        raise HTTPException(status_code=403, detail="Invalid secret token")

    data = await request.json()
    logger.info(f"Telegram webhook: {list(data.keys())}")

    # Handle /start command with plan parameter (deep link from main bot)
    if "message" in data and "text" in data["message"]:
        text = data["message"]["text"]
        if text.startswith("/start "):
            return await _handle_start_command(data["message"])

    # Handle pre_checkout_query
    if "pre_checkout_query" in data:
        return await _handle_pre_checkout(data["pre_checkout_query"])

    # Handle successful_payment (via message)
    if "message" in data and "successful_payment" in data["message"]:
        return await _handle_successful_payment(data["message"])

    # Ignore other update types
    return {"ok": True}


async def _handle_start_command(message: dict):
    """Handle /start <plan_key> deep link — send Invoice."""
    from .telegram_api import send_invoice, send_message

    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    plan_key = text.replace("/start ", "").strip()

    if plan_key not in PLAN_PRICING:
        await send_message(chat_id,
            "🐔 Welcome to FeedPilot AI Payment!\n\n"
            "Please use the link from the main bot to subscribe.\n"
            "Or visit: feedpilot.gumroad.com")
        return {"ok": True}

    plan = PLAN_PRICING[plan_key]

    # Send invoice
    result = await send_invoice(
        chat_id=chat_id,
        title=f"FeedPilot AI — {plan['label']}",
        description=(
            f"🐔 {plan['label']} Subscription\n\n"
            f"✓ Unlimited feed formula queries\n"
            f"✓ All formulas (Nursery, Breeder, Broiler, Layer...)\n"
            f"✓ Customer CRM management\n"
            f"✓ AI nutrition analysis\n"
            f"✓ Price trend alerts\n\n"
            f"Valid for {plan['days']} days"
        ),
        payload=f"{plan_key}:{chat_id}",
        prices=[{"label": plan["label"], "amount": plan["stars"]}],
        currency="XTR",
        provider_token="",  # Empty for Telegram Stars
    )

    logger.info(f"Sent invoice to {chat_id}: {plan_key} ({plan['stars']} Stars)")
    return {"ok": True}


async def _handle_pre_checkout(pre_checkout: dict):
    """Approve or reject pre-checkout query."""
    from .telegram_api import approve_pre_checkout, decline_pre_checkout

    payload = pre_checkout.get("invoice_payload", "")
    # Payload format: "plan_key:chat_id"
    parts = payload.split(":")
    if len(parts) != 2:
        await decline_pre_checkout(pre_checkout["id"], "Invalid payload")
        return {"ok": True}

    plan_key, chat_id = parts
    if plan_key not in PLAN_PRICING:
        await decline_pre_checkout(pre_checkout["id"], "Invalid plan")
        return {"ok": True}

    await approve_pre_checkout(pre_checkout["id"])
    logger.info(f"Approved pre_checkout: {plan_key}, {pre_checkout.get('total_amount', 0)} stars")
    return {"ok": True}


async def _handle_successful_payment(message: dict):
    """Process successful Stars payment."""
    from .telegram_api import send_message

    payment = message["successful_payment"]
    chat_id = message["chat"]["id"]
    user_id = f"telegram:{chat_id}"

    payload = payment.get("invoice_payload", "")
    parts = payload.split(":")
    if len(parts) != 2:
        logger.error(f"Invalid payload: {payload}")
        return {"ok": True}

    plan_key, _ = parts
    stars_amount = payment.get("total_amount", 0)
    payment_id = payment.get("telegram_payment_charge_id", "")

    if not payment_id:
        logger.error("No payment_charge_id")
        return {"ok": True}

    # Map plan key to DB plan
    if "starter" in plan_key:
        db_plan = "starter"
    elif "pro" in plan_key:
        db_plan = "pro"
    else:
        db_plan = "free"

    try:
        expires_at = db.activate_subscription(
            user_id=user_id,
            plan_key=db_plan,
            payment_id=payment_id,
            payment_method="telegram_stars",
            amount=stars_amount,
            currency="XTR",
            raw_data=payment,
        )

        # Notify user
        plan_display = db_plan.capitalize()
        await send_message(
            chat_id,
            f"✅ {plan_display} subscription activated!\n"
            f"Valid until: {expires_at[:10]}\n"
            f"Stars spent: {stars_amount} ⭐\n\n"
            f"Return to @feedpilot_bot to start using Pro features!"
        )
    except Exception as e:
        logger.error(f"Failed to activate subscription: {e}")
        await send_message(chat_id, "⚠️ Payment received but activation failed. Please contact support.")

    return {"ok": True}
