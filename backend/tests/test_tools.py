from __future__ import annotations

import pytest
from backend.agents.tools import _deep_merge


# ─── _deep_merge ──────────────────────────────────────────────────────


class TestDeepMerge:
    def test_flat_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"vitals": {"hr": 72, "bp": 120}}
        override = {"vitals": {"hr": 80}}
        result = _deep_merge(base, override)
        assert result == {"vitals": {"hr": 80, "bp": 120}}

    def test_deep_nested_merge(self):
        base = {"a": {"b": {"c": 1, "d": 2}}}
        override = {"a": {"b": {"c": 10}}}
        result = _deep_merge(base, override)
        assert result == {"a": {"b": {"c": 10, "d": 2}}}

    def test_none_values_not_added(self):
        base = {"a": 1}
        override = {"a": None}
        result = _deep_merge(base, override)
        assert result == {"a": 1}

    def test_new_keys_added(self):
        base = {"a": 1}
        override = {"b": 2}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 2}

    def test_empty_base(self):
        result = _deep_merge({}, {"a": 1})
        assert result == {"a": 1}

    def test_empty_override(self):
        result = _deep_merge({"a": 1}, {})
        assert result == {"a": 1}

    def test_both_empty(self):
        result = _deep_merge({}, {})
        assert result == {}

    def test_non_dict_override_replaces(self):
        base = {"a": {"b": 1}}
        override = {"a": [1, 2, 3]}
        result = _deep_merge(base, override)
        assert result == {"a": [1, 2, 3]}

    def test_original_not_mutated(self):
        base = {"a": {"b": 1}}
        override = {"a": {"b": 2}}
        _deep_merge(base, override)
        assert base == {"a": {"b": 1}}


# ─── check_safety_thresholds (async) ─────────────────────────────────


class TestCheckSafetyThresholds:
    @pytest.mark.asyncio
    async def test_normal_returns_not_breached(self):
        from backend.agents.tools import check_safety_thresholds

        result = await check_safety_thresholds({"systolic_bp": 120}, "I feel fine")
        assert result["breached"] is False
        assert result["severity"] == "info"
        assert result["alerts"] == []

    @pytest.mark.asyncio
    async def test_warn_returns_breached(self):
        from backend.agents.tools import check_safety_thresholds

        result = await check_safety_thresholds({"systolic_bp": 165}, "I feel fine")
        assert result["breached"] is True
        assert result["severity"] == "warn"
        assert len(result["alerts"]) == 1

    @pytest.mark.asyncio
    async def test_critical_returns_breached(self):
        from backend.agents.tools import check_safety_thresholds

        result = await check_safety_thresholds({"systolic_bp": 185}, "I feel fine")
        assert result["breached"] is True
        assert result["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_symptom_only_breach(self):
        from backend.agents.tools import check_safety_thresholds

        result = await check_safety_thresholds({}, "I can't breathe")
        assert result["breached"] is True
        assert result["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_risk_score_populated(self):
        from backend.agents.tools import check_safety_thresholds

        result = await check_safety_thresholds({"systolic_bp": 185}, "severe chest pain")
        assert result["risk_score"] > 0
