from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from backend.agents.graph import AgentState, decide_route


# ─── decide_route ─────────────────────────────────────────────────────


class TestDecideRoute:
    def test_normal_when_not_triggered(self):
        state: AgentState = {
            "session_id": uuid4(),
            "user_message": "hello",
            "chat_history": [],
            "profile_context": "",
            "extracted_clinical_data": {},
            "safety_check": {"breached": False, "alerts": []},
            "interrupt_triggered": False,
            "safety_severity": "info",
            "response_text": "",
        }
        assert decide_route(state) == "respond_normal"

    def test_interrupt_when_triggered(self):
        state: AgentState = {
            "session_id": uuid4(),
            "user_message": "hello",
            "chat_history": [],
            "profile_context": "",
            "extracted_clinical_data": {},
            "safety_check": {"breached": True, "alerts": ["chest pain"]},
            "interrupt_triggered": True,
            "safety_severity": "critical",
            "response_text": "",
        }
        assert decide_route(state) == "respond_interrupt"


# ─── run_safety_check ────────────────────────────────────────────────


class TestRunSafetyCheck:
    @pytest.mark.asyncio
    async def test_no_vitals_no_breach(self):
        from backend.agents.graph import run_safety_check

        state: AgentState = {
            "session_id": uuid4(),
            "user_message": "I feel fine",
            "chat_history": [],
            "profile_context": "",
            "extracted_clinical_data": {},
            "safety_check": {"breached": False, "alerts": []},
            "interrupt_triggered": False,
            "safety_severity": "info",
            "response_text": "",
        }
        result = await run_safety_check(state)
        assert result["interrupt_triggered"] is False
        assert result["safety_check"]["breached"] is False

    @pytest.mark.asyncio
    async def test_critical_vitals_triggers_interrupt(self):
        from backend.agents.graph import run_safety_check

        state: AgentState = {
            "session_id": uuid4(),
            "user_message": "I feel fine",
            "chat_history": [],
            "profile_context": "",
            "extracted_clinical_data": {"vitals": {"systolic_bp": 185}},
            "safety_check": {"breached": False, "alerts": []},
            "interrupt_triggered": False,
            "safety_severity": "info",
            "response_text": "",
        }
        with patch("backend.agents.graph.memory_store") as mock_store:
            mock_store.insert_safety_event = AsyncMock()
            result = await run_safety_check(state)
        assert result["interrupt_triggered"] is True
        assert result["safety_severity"] == "critical"

    @pytest.mark.asyncio
    async def test_warn_vitals_triggers_interrupt(self):
        from backend.agents.graph import run_safety_check

        state: AgentState = {
            "session_id": uuid4(),
            "user_message": "I feel fine",
            "chat_history": [],
            "profile_context": "",
            "extracted_clinical_data": {"vitals": {"systolic_bp": 165}},
            "safety_check": {"breached": False, "alerts": []},
            "interrupt_triggered": False,
            "safety_severity": "info",
            "response_text": "",
        }
        with patch("backend.agents.graph.memory_store") as mock_store:
            mock_store.insert_safety_event = AsyncMock()
            result = await run_safety_check(state)
        assert result["interrupt_triggered"] is True
        assert result["safety_severity"] == "warn"

    @pytest.mark.asyncio
    async def test_symptom_message_triggers_interrupt(self):
        from backend.agents.graph import run_safety_check

        state: AgentState = {
            "session_id": uuid4(),
            "user_message": "I can't breathe",
            "chat_history": [],
            "profile_context": "",
            "extracted_clinical_data": {},
            "safety_check": {"breached": False, "alerts": []},
            "interrupt_triggered": False,
            "safety_severity": "info",
            "response_text": "",
        }
        with patch("backend.agents.graph.memory_store") as mock_store:
            mock_store.insert_safety_event = AsyncMock()
            result = await run_safety_check(state)
        assert result["interrupt_triggered"] is True
        assert result["safety_severity"] == "critical"


# ─── apply_memory_update ─────────────────────────────────────────────


class TestApplyMemoryUpdate:
    @pytest.mark.asyncio
    async def test_empty_data_returns_empty(self):
        from backend.agents.graph import apply_memory_update

        state: AgentState = {
            "session_id": uuid4(),
            "user_message": "hello",
            "chat_history": [],
            "profile_context": "",
            "extracted_clinical_data": {},
            "safety_check": {"breached": False, "alerts": []},
            "interrupt_triggered": False,
            "safety_severity": "info",
            "response_text": "",
        }
        result = await apply_memory_update(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_non_empty_data_calls_update(self):
        from backend.agents.graph import apply_memory_update

        state: AgentState = {
            "session_id": uuid4(),
            "user_message": "hello",
            "chat_history": [],
            "profile_context": "",
            "extracted_clinical_data": {"vitals": {"hr": 72}},
            "safety_check": {"breached": False, "alerts": []},
            "interrupt_triggered": False,
            "safety_severity": "info",
            "response_text": "",
        }
        with patch("backend.agents.graph.update_clinical_profile", new_callable=AsyncMock) as mock_update:
            result = await apply_memory_update(state)
            mock_update.assert_called_once()
            assert result == {}

    @pytest.mark.asyncio
    async def test_empty_values_not_updated(self):
        from backend.agents.graph import apply_memory_update

        state: AgentState = {
            "session_id": uuid4(),
            "user_message": "hello",
            "chat_history": [],
            "profile_context": "",
            "extracted_clinical_data": {"vitals": {}, "medications": []},
            "safety_check": {"breached": False, "alerts": []},
            "interrupt_triggered": False,
            "safety_severity": "info",
            "response_text": "",
        }
        with patch("backend.agents.graph.update_clinical_profile", new_callable=AsyncMock) as mock_update:
            result = await apply_memory_update(state)
            mock_update.assert_not_called()
            assert result == {}
