from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from backend.agents.clinical_responder import (
    RESPONDER_PROMPT,
    SAFETY_OVERRIDE_CRITICAL,
    SAFETY_OVERRIDE_WARN,
    generate_response,
)


class TestPromptTemplates:
    def test_responder_prompt_mentions_careanchor(self):
        assert "CareAnchor" in RESPONDER_PROMPT

    def test_responder_prompt_no_diagnose(self):
        assert "Never diagnose" in RESPONDER_PROMPT

    def test_warn_override_mentions_monitoring(self):
        assert "monitoring" in SAFETY_OVERRIDE_WARN.lower()

    def test_critical_override_mentions_emergency(self):
        assert "emergency" in SAFETY_OVERRIDE_CRITICAL.lower()

    def test_warn_override_mentions_doctor(self):
        assert "doctor" in SAFETY_OVERRIDE_WARN.lower()

    def test_critical_override_mentions_emergency_services(self):
        assert "emergency services" in SAFETY_OVERRIDE_CRITICAL.lower()

    def test_critical_override_mentions_disabling_routine(self):
        assert "Disable ANY routine advice" in SAFETY_OVERRIDE_CRITICAL

    def test_warn_override_allows_routine_care(self):
        assert "routine care suggestions" in SAFETY_OVERRIDE_WARN.lower()

    def test_alerts_formatting_in_warn(self):
        formatted = SAFETY_OVERRIDE_WARN.format(alerts="- Alert A\n- Alert B")
        assert "- Alert A" in formatted
        assert "- Alert B" in formatted

    def test_alerts_formatting_in_critical(self):
        formatted = SAFETY_OVERRIDE_CRITICAL.format(alerts="- Alert A\n- Alert B")
        assert "- Alert A" in formatted
        assert "- Alert B" in formatted


def _make_async_generator(items):
    """Create an async generator that yields items."""
    async def gen():
        for item in items:
            yield item
    return gen()


class TestGenerateResponse:
    @pytest.mark.asyncio
    async def test_normal_mode_uses_responder_prompt(self):
        with patch("backend.agents.clinical_responder.stream_chat") as mock_stream:
            mock_stream.return_value = _make_async_generator(["Hello"])
            messages = []
            async for token in generate_response(
                profile_context="",
                chat_history=[],
                user_message="hi",
            ):
                messages.append(token)
            call_args = mock_stream.call_args
            system_msg = call_args[1]["messages"][0]
            assert "CareAnchor" in system_msg["content"]

    @pytest.mark.asyncio
    async def test_critical_mode_uses_critical_override(self):
        with patch("backend.agents.clinical_responder.stream_chat") as mock_stream:
            mock_stream.return_value = _make_async_generator(["Hello"])
            async for token in generate_response(
                profile_context="",
                chat_history=[],
                user_message="I can't breathe",
                safety_interrupt=True,
                safety_alerts=["breathing difficulty"],
                safety_severity="critical",
            ):
                pass
            call_args = mock_stream.call_args
            system_content = call_args[1]["messages"][0]["content"]
            assert "CRITICAL THRESHOLD BREACHED" in system_content

    @pytest.mark.asyncio
    async def test_warn_mode_uses_warn_override(self):
        with patch("backend.agents.clinical_responder.stream_chat") as mock_stream:
            mock_stream.return_value = _make_async_generator(["Hello"])
            async for token in generate_response(
                profile_context="",
                chat_history=[],
                user_message="I feel dizzy",
                safety_interrupt=True,
                safety_alerts=["dizziness reported"],
                safety_severity="warn",
            ):
                pass
            call_args = mock_stream.call_args
            system_content = call_args[1]["messages"][0]["content"]
            assert "CLINICAL WARNING" in system_content

    @pytest.mark.asyncio
    async def test_profile_context_added(self):
        with patch("backend.agents.clinical_responder.stream_chat") as mock_stream:
            mock_stream.return_value = _make_async_generator(["Hello"])
            async for token in generate_response(
                profile_context="Patient: John, Age: 65",
                chat_history=[],
                user_message="hi",
            ):
                pass
            call_args = mock_stream.call_args
            system_content = call_args[1]["messages"][0]["content"]
            assert "Patient: John" in system_content

    @pytest.mark.asyncio
    async def test_chat_history_included(self):
        with patch("backend.agents.clinical_responder.stream_chat") as mock_stream:
            mock_stream.return_value = _make_async_generator(["Hello"])
            history = [
                {"role": "user", "content": "previous msg"},
                {"role": "assistant", "content": "previous response"},
            ]
            async for token in generate_response(
                profile_context="",
                chat_history=history,
                user_message="current msg",
            ):
                pass
            call_args = mock_stream.call_args
            msgs = call_args[1]["messages"]
            assert len(msgs) == 4  # system + 2 history + user

    @pytest.mark.asyncio
    async def test_chat_history_limited_to_six(self):
        with patch("backend.agents.clinical_responder.stream_chat") as mock_stream:
            mock_stream.return_value = _make_async_generator(["Hello"])
            history = [{"role": "user", "content": f"msg {i}"} for i in range(10)]
            async for token in generate_response(
                profile_context="",
                chat_history=history,
                user_message="current",
            ):
                pass
            call_args = mock_stream.call_args
            msgs = call_args[1]["messages"]
            assert len(msgs) == 8  # system + 6 history + user

    @pytest.mark.asyncio
    async def test_model_settings_correct(self):
        with patch("backend.agents.clinical_responder.stream_chat") as mock_stream:
            mock_stream.return_value = _make_async_generator(["Hello"])
            async for token in generate_response(
                profile_context="",
                chat_history=[],
                user_message="hi",
            ):
                pass
            call_args = mock_stream.call_args
            assert call_args[1]["model"] == settings.response_model
            assert call_args[1]["temperature"] == 0.7
            assert call_args[1]["max_tokens"] == 2048
