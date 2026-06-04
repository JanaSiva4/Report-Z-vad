import asyncio
import logging
import os

emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST", "")
if emulator_host in {"127.0.0.1:9", "localhost:9"}:
    os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
if os.getenv("FIRESTORE_COLLECTION", "").startswith("tickets_test_"):
    os.environ["LOCAL_TEST_MODE"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers.api import router as api_router
from app.services.secret_manager import resolve_value
from app.services.unify import sync_unify_events


logger = logging.getLogger(__name__)


app = FastAPI(title="Maintenance Helpdesk CZLC4")

if os.getenv("CORS_ALLOWED_ORIGIN"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("CORS_ALLOWED_ORIGIN")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def no_cache_for_frontend(request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


app.include_router(api_router)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")


async def _unify_poll_loop() -> None:
    interval = max(int(settings.unify_poll_seconds or 60), 30)
    while True:
        try:
            await asyncio.to_thread(sync_unify_events)
        except Exception:
            logger.exception("Uniify sync selhal.")
        await asyncio.sleep(interval)


@app.on_event("startup")
async def start_unify_polling():
    unify_url = resolve_value(settings.unify_api_url, settings.unify_api_url_secret_name)
    unify_token = resolve_value(settings.unify_api_token, settings.unify_api_token_secret_name)
    if unify_url.strip() and unify_token.strip():
        app.state.unify_poll_task = asyncio.create_task(_unify_poll_loop())
