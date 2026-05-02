"""FeedPilot AI — Payment Webhook Server (FastAPI)."""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import HOST, PORT
from . import database as db
from .telegram_handler import router as telegram_router
from .gumroad_handler import router as gumroad_router

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("webhook")

# App
app = FastAPI(
    title="FeedPilot Webhook Server",
    version="1.0.0",
)

# Include routers
app.include_router(telegram_router)
app.include_router(gumroad_router)


@app.on_event("startup")
async def startup():
    """Run DB migrations on startup."""
    logger.info("Starting webhook server...")
    db.migrate()
    logger.info("DB migration complete")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "feedpilot-webhook"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler — always return 200 to webhook callers."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    # Webhook callers (Telegram/Gumroad) retry on non-200, so we return 200
    # and log the error instead of failing the webhook delivery
    return JSONResponse(status_code=200, content={"ok": True, "error": "internal"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
