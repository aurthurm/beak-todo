"""Beak Flow FastAPI application."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import ai, categories, integrations_github, reports, tags, todos
from src.api.schemas import HealthResponse
from src.api.static_paths import resolve_static_dir
from src.config import get_ai_config, get_config_path
from src.db.connection import ensure_db

log = logging.getLogger("beak-flow")


@asynccontextmanager
async def lifespan(application: FastAPI):
    ensure_db()
    if resolve_static_dir() is None:
        log.warning(
            "UI static files not found. Run `beak-flow build-ui` to enable the web UI."
        )
    yield


app = FastAPI(title="Beak Flow", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8787",
        "http://127.0.0.1:8787",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(integrations_github.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
def health():
    ai_cfg = get_ai_config()
    return HealthResponse(
        status="ok",
        ai_enabled=ai_cfg.enabled,
        config_path=str(get_config_path()),
    )


_ui_dist = resolve_static_dir()
if _ui_dist is not None:
    app.mount("/", StaticFiles(directory=str(_ui_dist), html=True), name="ui")
