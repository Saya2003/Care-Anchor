from __future__ import annotations

import os
import platform
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as rest_router
from backend.api.sessions import router as sessions_router
from backend.api.websocket import router as ws_router
from backend.api.profile import router as profile_router
from backend.api.analytics import router as analytics_router
from backend.api.predictions import router as predictions_router
from backend.config import settings
from backend.db.sqlite import close_db, ensure_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database
    await ensure_schema()
    print("[SUCCESS]: CareAnchor Backend initialized with Codex and GPT-5.6 models.")
    print(f"[AI]: OpenRouter Base URL: {settings.openrouter_base_url}")
    yield
    await close_db()


app = FastAPI(
    title="CareAnchor API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rest_router)
app.include_router(sessions_router)
app.include_router(ws_router)
app.include_router(profile_router)
app.include_router(analytics_router)
app.include_router(predictions_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ai/runtime")
async def ai_runtime_trace():
    """Runtime verification endpoint for AI model integration proof."""
    import httpx

    openrouter_ok = False
    openrouter_latency_ms = None

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            start = datetime.now(timezone.utc)
            resp = await client.get(
                f"{settings.openrouter_base_url}/models",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
            )
            elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            openrouter_latency_ms = round(elapsed, 1)
            openrouter_ok = resp.status_code == 200
    except Exception:
        openrouter_ok = False

    return {
        "service": "careanchor-api",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime": {
            "python": platform.python_version(),
            "hostname": platform.node(),
            "platform": platform.platform(),
        },
        "ai_integration": {
            "provider": "OpenRouter",
            "openrouter_endpoint": settings.openrouter_base_url,
            "openrouter_reachable": openrouter_ok,
            "openrouter_latency_ms": openrouter_latency_ms,
            "extraction_model": settings.extraction_model,
            "response_model": settings.response_model,
        },
        "config": {
            "postgres_configured": bool(settings.database_url),
            "alert_webhook_configured": bool(settings.alert_webhook_url),
            "cors_origins": settings.cors_origins,
        },
    }
