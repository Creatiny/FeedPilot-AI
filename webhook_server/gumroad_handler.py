"""Gumroad webhook handler."""
import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, HTTPException
from urllib.parse import parse_qs

from . import database as db

logger = logging.getLogger("webhook.gumroad")
router = APIRouter()


@router.post("/webhook/gumroad")
async def handle_gumroad_webhook(request: Request):
    """Handle Gumroad Ping (x-www-form-urlencoded)."""
    body = await request.body()

    # Gumroad sends x-www-form-urlencoded, not JSON
    try:
        raw = parse_qs(body.decode("utf-8"))
        # parse_qs returns lists, take first value for each key
        data = {k: v[0] if len(v) == 1 else v for k, v in raw.items()}
    except Exception as e:
        logger.error(f"Failed to parse Gumroad ping: {e}")
        return {"ok": True}

    logger.info(f"Gumroad ping: sale_id={data.get('sale_id')}, email={data.get('email')}")

    sale_id = data.get("sale_id", "")
    email = data.get("email", "")
    product_name = data.get("product_name", "")
    price_cents = int(data.get("price", 0))
    amount = price_cents / 100.0  # Convert cents to USD

    if not sale_id or not email:
        logger.error(f"Missing sale_id or email: {data}")
        return {"ok": True}

    # Determine plan from product name or variants
    product_lower = product_name.lower()
    variants = data.get("variants", "")
    if isinstance(variants, str) and variants:
        product_lower = variants.lower()

    if "pro" in product_lower:
        plan_key = "pro"
    elif "starter" in product_lower:
        plan_key = "starter"
    else:
        plan_key = "starter"  # default

    # Check if this is a test purchase
    if data.get("test") == "true":
        logger.info(f"Gumroad test purchase, skipping activation")
        return {"ok": True}

    # Find or create user
    user_id = db.find_user_by_gumroad_email(email)
    if not user_id:
        # Create new user with gumroad email prefix
        user_id = f"gumroad:{email.split('@')[0]}"
        from .database import get_db
        with get_db() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO subscriptions (user_id, plan_id, gumroad_email, created_at, updated_at)
                VALUES (?, 1, ?, datetime('now'), datetime('now'))
            """, (user_id, email))

    db.set_gumroad_email(user_id, email)

    try:
        expires_at = db.activate_subscription(
            user_id=user_id,
            plan_key=plan_key,
            payment_id=f"gumroad_{sale_id}",
            payment_method="gumroad",
            amount=amount,
            currency="USD",
            raw_data=data,
        )
        logger.info(f"Gumroad sale activated: {email} → {plan_key}, expires {expires_at}")
    except Exception as e:
        logger.error(f"Failed to activate Gumroad subscription: {e}")

    return {"ok": True}
