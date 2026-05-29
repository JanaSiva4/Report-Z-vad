import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.api import router as api_router


app = FastAPI(title="Maintenance Helpdesk CZLC4")

if os.getenv("CORS_ALLOWED_ORIGIN"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("CORS_ALLOWED_ORIGIN")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


app.include_router(api_router)

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
