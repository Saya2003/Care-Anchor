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
    # Alibaba Cloud ECS proof — prints verification logs visible in `docker compose logs api`
    if settings.dashscope_api_key:
        from alibaba_cloud_config import verify_alibaba_cloud_environment

        verify_alibaba_cloud_environment()
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


@app.get("/alibaba/runtime")
async def alibaba_runtime_trace():
    """Runtime verification endpoint for Alibaba Cloud ECS deployment proof."""
    import httpx

    dashscope_ok = False
    dashscope_latency_ms = None
    ecs_meta = {}

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            start = datetime.now(timezone.utc)
            resp = await client.get(
                f"{settings.dashscope_base_url}/models",
                headers={"Authorization": f"Bearer {settings.dashscope_api_key}"},
            )
            elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            dashscope_latency_ms = round(elapsed, 1)
            dashscope_ok = resp.status_code == 200
    except Exception:
        dashscope_ok = False

    # ECS instance metadata (Alibaba Cloud internal endpoint)
    for key in ("instance-id", "region-id", "zone-id", "image-id", "private-ipv4"):
        try:
            import httpx

            async with httpx.AsyncClient(timeout=2) as client:
                r = await client.get(
                    f"http://100.100.100.200/latest/meta-data/{key}"
                )
                if r.status_code == 200:
                    ecs_meta[key.replace("-", "_")] = r.text.strip()
        except Exception:
            pass

    return {
        "service": "careanchor-api",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime": {
            "python": platform.python_version(),
            "hostname": platform.node(),
            "platform": platform.platform(),
        },
        "alibaba_cloud": {
            "proof_file": "alibaba_cloud_config.py",
            "dashscope_endpoint": settings.dashscope_base_url,
            "dashscope_reachable": dashscope_ok,
            "dashscope_latency_ms": dashscope_latency_ms,
            "model_plus": settings.qwen_plus_model,
            "model_max": settings.qwen_max_model,
            "ecs_metadata": ecs_meta if ecs_meta else None,
        },
        "config": {
            "postgres_configured": bool(settings.database_url),
            "alert_webhook_configured": bool(settings.alert_webhook_url),
            "cors_origins": settings.cors_origins,
        },
    }
