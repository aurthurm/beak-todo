"""Beak Flow FastAPI application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.routes import ai, categories, todos
from src.api.schemas import HealthResponse
from src.config import get_ai_config, get_config_path
from src.db.connection import ensure_db

app = FastAPI(title="Beak Flow", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8787",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.on_event("startup")
def startup():
    ensure_db()


@app.get("/api/health", response_model=HealthResponse)
def health():
    ai_cfg = get_ai_config()
    return HealthResponse(
        status="ok",
        ai_enabled=ai_cfg.enabled,
        config_path=str(get_config_path()),
    )


_ui_dist = Path(__file__).resolve().parents[2] / "ui" / "dist"
if _ui_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_ui_dist), html=True), name="ui")
