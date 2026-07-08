from __future__ import annotations

import time
from unittest.mock import patch

import pytest
from backend.core.interrupt import InterruptController, InterruptEvent, InterruptState


@pytest.fixture
def ctrl():
    return InterruptController()


# ─── State machine ────────────────────────────────────────────────────


class TestInterruptStateEnum:
    def test_all_states_exist(self):
        assert InterruptState.NORMAL == "normal"
        assert InterruptState.PENDING_ACKNOWLEDGMENT == "pending_acknowledgment"
        assert InterruptState.ACKNOWLEDGED == "acknowledged"
        assert InterruptState.ESCALATED == "escalated"
        assert InterruptState.RESOLVED == "resolved"


class TestStartInterrupt:
    def test_creates_new_event(self, ctrl):
        event = ctrl.start_interrupt("s1", "critical", ["alert1"], 8.0)
        assert event.session_id == "s1"
        assert event.severity == "critical"
        assert event.alerts == ["alert1"]
        assert event.risk_score == 8.0
        assert event.state == InterruptState.PENDING_ACKNOWLEDGMENT

    def test_updates_existing_unresolved_event(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["old"], 3.0)
        event = ctrl.start_interrupt("s1", "critical", ["new"], 8.0)
        assert event.alerts == ["new"]
        assert event.severity == "critical"
        assert event.risk_score == 8.0

    def test_creates_new_if_resolved(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["old"], 3.0)
        ctrl.resolve("s1")
        event = ctrl.start_interrupt("s1", "critical", ["new"], 8.0)
        assert event.alerts == ["new"]

    def test_creates_new_if_acknowledged(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["old"], 3.0)
        ctrl.acknowledge("s1")
        event = ctrl.start_interrupt("s1", "critical", ["new"], 8.0)
        assert event.alerts == ["new"]


class TestGetActiveEvent:
    def test_returns_none_for_unknown_session(self, ctrl):
        assert ctrl.get_active_event("unknown") is None

    def test_returns_event_for_pending(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        assert ctrl.get_active_event("s1") is not None

    def test_returns_none_for_resolved(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.resolve("s1")
        assert ctrl.get_active_event("s1") is None

    def test_returns_none_for_acknowledged(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.acknowledge("s1")
        assert ctrl.get_active_event("s1") is None


class TestAcknowledge:
    def test_sets_acknowledged_state(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        event = ctrl.acknowledge("s1")
        assert event.state == InterruptState.ACKNOWLEDGED
        assert event.acknowledged_by == "clinician"
        assert event.acknowledged_at is not None

    def test_custom_acknowledger(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        event = ctrl.acknowledge("s1", acknowledged_by="nurse_jane")
        assert event.acknowledged_by == "nurse_jane"

    def test_returns_none_for_unknown(self, ctrl):
        assert ctrl.acknowledge("unknown") is None


class TestEscalate:
    def test_sets_escalated_state(self, ctrl):
        ctrl.start_interrupt("s1", "critical", ["a"], 8.0)
        event = ctrl.escalate("s1")
        assert event.state == InterruptState.ESCALATED

    def test_returns_none_for_unknown(self, ctrl):
        assert ctrl.escalate("unknown") is None


class TestResolve:
    def test_sets_resolved_state(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        event = ctrl.resolve("s1")
        assert event.state == InterruptState.RESOLVED

    def test_returns_none_for_unknown(self, ctrl):
        assert ctrl.resolve("unknown") is None


# ─── Rate limiting ────────────────────────────────────────────────────


class TestShouldNotify:
    def test_always_notify_if_no_event(self, ctrl):
        assert ctrl.should_notify("unknown") is True

    def test_notify_if_pending_first_time(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        assert ctrl.should_notify("s1") is True

    def test_no_notify_if_escalated(self, ctrl):
        ctrl.start_interrupt("s1", "critical", ["a"], 8.0)
        ctrl.escalate("s1")
        assert ctrl.should_notify("s1") is False

    def test_notify_after_cooldown(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.mark_notified("s1")
        # Just notified — should not notify
        assert ctrl.should_notify("s1") is False
        # Simulate time passing by manipulating last_notified
        ctrl._events["s1"].last_notified = time.time() - 1000
        assert ctrl.should_notify("s1") is True

    def test_notify_if_acknowledged(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.acknowledge("s1")
        assert ctrl.should_notify("s1") is True

    def test_notify_if_resolved(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.resolve("s1")
        assert ctrl.should_notify("s1") is True


class TestMarkNotified:
    def test_updates_last_notified(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        assert ctrl._events["s1"].last_notified == 0.0
        ctrl.mark_notified("s1")
        assert ctrl._events["s1"].last_notified > 0.0

    def test_no_error_for_unknown(self, ctrl):
        ctrl.mark_notified("unknown")


# ─── has_unresolved / get_state ──────────────────────────────────────


class TestHasUnresolved:
    def test_false_for_unknown(self, ctrl):
        assert ctrl.has_unresolved("unknown") is False

    def test_true_for_pending(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        assert ctrl.has_unresolved("s1") is True

    def test_false_for_resolved(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.resolve("s1")
        assert ctrl.has_unresolved("s1") is False

    def test_false_for_acknowledged(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.acknowledge("s1")
        assert ctrl.has_unresolved("s1") is False

    def test_true_for_escalated(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.escalate("s1")
        assert ctrl.has_unresolved("s1") is True


class TestGetState:
    def test_normal_for_unknown(self, ctrl):
        assert ctrl.get_state("unknown") == InterruptState.NORMAL

    def test_pending_for_active(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        assert ctrl.get_state("s1") == InterruptState.PENDING_ACKNOWLEDGMENT

    def test_acknowledged(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.acknowledge("s1")
        assert ctrl.get_state("s1") == InterruptState.ACKNOWLEDGED

    def test_escalated(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.escalate("s1")
        assert ctrl.get_state("s1") == InterruptState.ESCALATED

    def test_resolved(self, ctrl):
        ctrl.start_interrupt("s1", "warn", ["a"], 3.0)
        ctrl.resolve("s1")
        assert ctrl.get_state("s1") == InterruptState.RESOLVED
