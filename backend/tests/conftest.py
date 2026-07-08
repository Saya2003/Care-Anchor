from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mock_settings():
    """Override settings for tests."""
    with patch("backend.config.settings") as s:
        s.systolic_bp_warn_max = 160
        s.diastolic_bp_warn_max = 100
        s.heart_rate_warn_max = 110
        s.heart_rate_warn_min = 50
        s.sp_o2_warn_min = 94
        s.temperature_warn_max = 38.0
        s.systolic_bp_crit_max = 180
        s.diastolic_bp_crit_max = 120
        s.heart_rate_crit_max = 140
        s.heart_rate_crit_min = 40
        s.sp_o2_crit_min = 90
        s.temperature_crit_max = 39.5
        s.escalation_cooldown_seconds = 300
        s.alert_webhook_url = ""
        yield s


@pytest.fixture
def fresh_interrupt_controller():
    """Provide a fresh InterruptController instance for each test."""
    from backend.core.interrupt import InterruptController

    return InterruptController()
