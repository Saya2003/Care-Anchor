from __future__ import annotations

import copy
import json
from uuid import UUID

from backend.db.postgres import get_pool

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
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT profile FROM clinical_profiles WHERE session_id = $1",
                session_id,
            )
            if row:
                return ClinicalProfile(json.loads(row["profile"]))
            return ClinicalProfile.new(session_id)

    async def save_profile(self, session_id: UUID, profile: ClinicalProfile) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO clinical_profiles (session_id, profile)
                VALUES ($1, $2::jsonb)
                ON CONFLICT (session_id)
                DO UPDATE SET profile = $2::jsonb, updated_at = now()
                """,
                session_id,
                json.dumps(dict(profile)),
            )

    async def append_chat(self, session_id: UUID, role: str, content: str) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO chat_logs (session_id, role, content)
                VALUES ($1, $2, $3)
                """,
                session_id,
                role,
                content,
            )

    async def get_recent_chats(
        self, session_id: UUID, limit: int = 20
    ) -> list[dict]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT role, content, created_at
                FROM chat_logs
                WHERE session_id = $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                session_id,
                limit,
            )
            return [
                {"role": r["role"], "content": r["content"]} for r in rows
            ]


    async def insert_safety_event(
        self, session_id: UUID, severity: str, alerts: list[str], risk_score: float, state: str = "pending_acknowledgment"
    ) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO safety_events (session_id, severity, alerts, risk_score, state)
                VALUES ($1, $2, $3::jsonb, $4, $5)
                """,
                session_id,
                severity,
                json.dumps(alerts),
                risk_score,
                state,
            )

    async def get_recent_safety_events(
        self, session_id: UUID, limit: int = 10
    ) -> list[dict]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT severity, alerts, risk_score, state, created_at
                FROM safety_events
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                session_id,
                limit,
            )
            return [
                {
                    "severity": r["severity"],
                    "alerts": json.loads(r["alerts"]),
                    "risk_score": float(r["risk_score"]),
                    "state": r["state"],
                    "created_at": r["created_at"].isoformat(),
                }
                for r in rows
            ]

    async def persist_interrupt_state(self, session_id: UUID, state: str) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            latest = await conn.fetchval(
                """
                SELECT id FROM safety_events
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                session_id,
            )
            if latest is not None:
                await conn.execute(
                    "UPDATE safety_events SET state = $1 WHERE id = $2",
                    state,
                    latest,
                )


memory_store = MemoryStore()
