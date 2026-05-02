"""Telegram Bot API helper for webhook responses."""
import httpx
import logging
from .config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger("webhook.telegram_api")

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def approve_pre_checkout(pre_checkout_id: str, error_message: str = ""):
    """Approve a pre-checkout query."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{API_BASE}/answerPreCheckoutQuery", json={
            "pre_checkout_query_id": pre_checkout_id,
            "ok": not bool(error_message),
            **(({"error_message": error_message} if error_message else {})),
        })
        if resp.status_code != 200:
            logger.error(f"Failed to answer pre_checkout: {resp.text}")
        return resp.json()


async def decline_pre_checkout(pre_checkout_id: str, error_message: str):
    """Decline a pre-checkout query."""
    return await approve_pre_checkout(pre_checkout_id, error_message)


async def send_message(chat_id: int, text: str, parse_mode: str = None):
    """Send a text message to a chat."""
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{API_BASE}/sendMessage", json=payload)
        if resp.status_code != 200:
            logger.error(f"Failed to send message: {resp.text}")
        return resp.json()


async def send_invoice(chat_id: int, title: str, description: str,
                       payload: str, prices: list, provider_token: str = "",
                       currency: str = "XTR", photo_url: str = None):
    """Send a Telegram Stars invoice.
    
    prices: list of {"label": str, "amount": int} (amount in Stars/cents)
    For Telegram Stars: currency="XTR", provider_token=""
    """
    invoice_payload = {
        "chat_id": chat_id,
        "title": title,
        "description": description,
        "payload": payload,
        "provider_token": provider_token,
        "currency": currency,
        "prices": prices,
    }
    if photo_url:
        invoice_payload["photo_url"] = photo_url
        invoice_payload["photo_width"] = 600
        invoice_payload["photo_height"] = 300

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(f"{API_BASE}/sendInvoice", json=invoice_payload)
        if resp.status_code != 200:
            logger.error(f"Failed to send invoice: {resp.text}")
        return resp.json()
