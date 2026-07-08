from __future__ import annotations

import copy
import json
from uuid import UUID

from backend.db.sqlite import get_db

DEFAULT_PROFILE: dict = {
    "demographics": {},
    "vitals": {},
    "medications": [],
    "symptoms": [],
    "care_plan": {},
}


class ClinicalProfile(dict):
    @classmethod
    def new(cls, session_id: UUID) -> ClinicalProfile:
        p = cls(copy.deepcopy(DEFAULT_PROFILE))
        p["session_id"] = str(session_id)
        return p


class MemoryStore:
    async def get_profile(self, session_id: UUID) -> ClinicalProfile:
        db = await get_db()
        cursor = await db.execute(
            "SELECT profile FROM clinical_profiles WHERE session_id = ?",
            (str(session_id),),
        )
        row = await cursor.fetchone()
        if row:
            return ClinicalProfile(json.loads(row["profile"]))
        return ClinicalProfile.new(session_id)

    async def save_profile(self, session_id: UUID, profile: ClinicalProfile) -> None:
        db = await get_db()
        await db.execute(
            """
            INSERT INTO clinical_profiles (session_id, profile)
            VALUES (?, ?)
            ON CONFLICT (session_id)
            DO UPDATE SET profile = ?, updated_at = CURRENT_TIMESTAMP
            """,
            (str(session_id), json.dumps(dict(profile)), json.dumps(dict(profile))),
        )
        await db.commit()

    async def append_chat(self, session_id: UUID, role: str, content: str) -> None:
        db = await get_db()
        await db.execute(
            "INSERT INTO chat_logs (session_id, role, content) VALUES (?, ?, ?)",
            (str(session_id), role, content),
        )
        await db.commit()

    async def get_recent_chats(self, session_id: UUID, limit: int = 20) -> list[dict]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT role, content FROM chat_logs WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (str(session_id), limit),
        )
        rows = await cursor.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    async def insert_safety_event(
        self, session_id: UUID, severity: str, alerts: list[str], risk_score: float, state: str = "pending_acknowledgment"
    ) -> None:
        db = await get_db()
        await db.execute(
            "INSERT INTO safety_events (session_id, severity, alerts, risk_score, state) VALUES (?, ?, ?, ?, ?)",
            (str(session_id), severity, json.dumps(alerts), risk_score, state),
        )
        await db.commit()

    async def get_recent_safety_events(self, session_id: UUID, limit: int = 10) -> list[dict]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT severity, alerts, risk_score, state, created_at FROM safety_events WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
            (str(session_id), limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "severity": r["severity"],
                "alerts": json.loads(r["alerts"]),
                "risk_score": float(r["risk_score"]),
                "state": r["state"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    async def persist_interrupt_state(self, session_id: UUID, state: str) -> None:
        db = await get_db()
        cursor = await db.execute(
            "SELECT id FROM safety_events WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (str(session_id),),
        )
        latest = await cursor.fetchone()
        if latest is not None:
            await db.execute("UPDATE safety_events SET state = ? WHERE id = ?", (state, latest["id"]))
            await db.commit()


memory_store = MemoryStore()
