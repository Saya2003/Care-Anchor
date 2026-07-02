from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: UUID
    message: str


class ChatResponse(BaseModel):
    session_id: UUID
    response: str
    extracted_clinical_data: dict
    safety_check: dict
    interrupt_triggered: bool


class SessionCreate(BaseModel):
    session_id: UUID | None = None


class SessionResponse(BaseModel):
    session_id: UUID
    profile: dict
    chat_history: list[dict]


class SafetyAlert(BaseModel):
    session_id: UUID
    alerts: list[str]
    message: str
