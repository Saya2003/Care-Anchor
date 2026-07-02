from __future__ import annotations

from typing import Any

from backend.core.memory_store import ClinicalProfile, memory_store
from backend.core.safety import evaluate_safety


async def update_clinical_profile(session_id: UUID, updates: dict) -> ClinicalProfile:
    profile = await memory_store.get_profile(session_id)
    for key, value in updates.items():
        existing = profile.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            deep = _deep_merge(existing, value)
            if deep != existing:
                profile[key] = deep
        elif value is not None and value != existing:
            profile[key] = value
    await memory_store.save_profile(session_id, profile)
    return profile


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _deep_merge(merged[k], v)
        elif v is not None and v != merged.get(k):
            merged[k] = v
    return merged


async def check_safety_thresholds(vitals: dict, message: str) -> dict:
    from backend.core.safety import SafetyVerdict

    verdict: SafetyVerdict = evaluate_safety(vitals, message)
    return {
        "breached": verdict.severity.value != "info",
        "severity": verdict.severity.value,
        "alerts": verdict.alerts,
        "risk_score": verdict.risk_score,
    }
