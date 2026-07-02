from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    # FastAPI
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: list[str] = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    )

    # Qwen Cloud (Alibaba Cloud Model Studio)
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY", "")
    qwen_plus_model: str = os.getenv("QWEN_PLUS_MODEL", "qwen-plus")
    qwen_max_model: str = os.getenv("QWEN_MAX_MODEL", "qwen-max")
    dashscope_base_url: str = os.getenv(
        "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # PostgreSQL
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/careanchor",
    )

    # Safety thresholds — warn (elevated, non-emergency)
    systolic_bp_warn_max: int = int(os.getenv("SYSTOLIC_BP_WARN_MAX", "160"))
    diastolic_bp_warn_max: int = int(os.getenv("DIASTOLIC_BP_WARN_MAX", "100"))
    heart_rate_warn_max: int = int(os.getenv("HEART_RATE_WARN_MAX", "110"))
    heart_rate_warn_min: int = int(os.getenv("HEART_RATE_WARN_MIN", "50"))
    sp_o2_warn_min: int = int(os.getenv("SP_O2_WARN_MIN", "94"))
    temperature_warn_max: float = float(os.getenv("TEMPERATURE_WARN_MAX", "38.0"))

    # Safety thresholds — critical (emergency)
    systolic_bp_crit_max: int = int(os.getenv("SYSTOLIC_BP_CRIT_MAX", "180"))
    diastolic_bp_crit_max: int = int(os.getenv("DIASTOLIC_BP_CRIT_MAX", "120"))
    heart_rate_crit_max: int = int(os.getenv("HEART_RATE_CRIT_MAX", "140"))
    heart_rate_crit_min: int = int(os.getenv("HEART_RATE_CRIT_MIN", "40"))
    sp_o2_crit_min: int = int(os.getenv("SP_O2_CRIT_MIN", "90"))
    temperature_crit_max: float = float(os.getenv("TEMPERATURE_CRIT_MAX", "39.5"))

    # Escalation
    alert_webhook_url: str = os.getenv("ALERT_WEBHOOK_URL", "")
    escalation_cooldown_seconds: int = int(os.getenv("ESCALATION_COOLDOWN_SECONDS", "300"))

    # Paths
    project_root: Path = Path(__file__).resolve().parent.parent


settings = Settings()
