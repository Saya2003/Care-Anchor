from __future__ import annotations

import json
from uuid import UUID

import aiosqlite

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(":memory:")
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        await ensure_schema(_db)
    return _db


async def ensure_schema(db: aiosqlite.Connection | None = None) -> None:
    if db is None:
        db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS clinical_profiles (
            session_id TEXT PRIMARY KEY,
            profile TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_chat_logs_session_id ON chat_logs(session_id);

        CREATE TABLE IF NOT EXISTS safety_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
            severity TEXT NOT NULL,
            alerts TEXT NOT NULL DEFAULT '[]',
            risk_score REAL NOT NULL DEFAULT 0.0,
            state TEXT NOT NULL DEFAULT 'pending_acknowledgment',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_safety_events_session_id ON safety_events(session_id);
    """)
    await db.commit()


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None
