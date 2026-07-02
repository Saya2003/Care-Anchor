from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum

from backend.config import settings

logger = logging.getLogger(__name__)


class InterruptState(str, Enum):
    NORMAL = "normal"
    PENDING_ACKNOWLEDGMENT = "pending_acknowledgment"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


@dataclass
class InterruptEvent:
    session_id: str
    severity: str
    alerts: list[str]
    risk_score: float
    timestamp: float = field(default_factory=time.time)
    state: InterruptState = InterruptState.PENDING_ACKNOWLEDGMENT
    last_notified: float = 0.0
    acknowledged_at: float | None = None
    acknowledged_by: str | None = None


class InterruptController:
    def __init__(self) -> None:
        self._events: dict[str, InterruptEvent] = {}

    def get_active_event(self, session_id: str) -> InterruptEvent | None:
        event = self._events.get(session_id)
        if event is None:
            return None
        if event.state in (InterruptState.RESOLVED, InterruptState.ACKNOWLEDGED):
            return None
        return event

    def start_interrupt(self, session_id: str, severity: str, alerts: list[str], risk_score: float) -> InterruptEvent:
        existing = self._events.get(session_id)
        if existing and existing.state not in (InterruptState.RESOLVED, InterruptState.ACKNOWLEDGED):
            existing.alerts = alerts
            existing.severity = severity
            existing.risk_score = risk_score
            return existing
        event = InterruptEvent(
            session_id=session_id,
            severity=severity,
            alerts=alerts,
            risk_score=risk_score,
            state=InterruptState.PENDING_ACKNOWLEDGMENT,
        )
        self._events[session_id] = event
        return event

    def acknowledge(self, session_id: str, acknowledged_by: str = "clinician") -> InterruptEvent | None:
        event = self._events.get(session_id)
        if event is None:
            return None
        event.state = InterruptState.ACKNOWLEDGED
        event.acknowledged_at = time.time()
        event.acknowledged_by = acknowledged_by
        return event

    def escalate(self, session_id: str) -> InterruptEvent | None:
        event = self._events.get(session_id)
        if event is None:
            return None
        event.state = InterruptState.ESCALATED
        return event

    def resolve(self, session_id: str) -> InterruptEvent | None:
        event = self._events.get(session_id)
        if event is None:
            return None
        event.state = InterruptState.RESOLVED
        return event

    def should_notify(self, session_id: str) -> bool:
        event = self._events.get(session_id)
        if event is None:
            return True
        if event.state == InterruptState.ESCALATED:
            return False
        if event.state == InterruptState.PENDING_ACKNOWLEDGMENT:
            elapsed = time.time() - event.last_notified
            return elapsed >= settings.escalation_cooldown_seconds
        return True

    def mark_notified(self, session_id: str) -> None:
        event = self._events.get(session_id)
        if event:
            event.last_notified = time.time()

    def has_unresolved(self, session_id: str) -> bool:
        event = self._events.get(session_id)
        if event is None:
            return False
        return event.state not in (InterruptState.RESOLVED, InterruptState.ACKNOWLEDGED, InterruptState.NORMAL)

    def get_state(self, session_id: str) -> InterruptState:
        event = self._events.get(session_id)
        return event.state if event else InterruptState.NORMAL


interrupt_controller = InterruptController()
