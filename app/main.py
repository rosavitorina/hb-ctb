import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.middleware.auth_rate_limit import AuthRateLimitMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.quotes import router as quotes_router
from app.services.auth_service import backfill_default_roles, bootstrap_admins

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(auth_router)
app.include_router(quotes_router)
app.add_middleware(AuthRateLimitMiddleware)


@app.on_event("startup")
def startup() -> None:
    try:
        backfill_default_roles()
        bootstrap_admins()
    except Exception:
        logger.exception("Admin bootstrap is unavailable")


@app.get("/health")
def health():
    return {"status": "ok"}


frontend_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")