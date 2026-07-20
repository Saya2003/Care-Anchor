from __future__ import annotations

import json
from uuid import UUID

import aiosqlite

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        # Use persistent database file instead of in-memory
        import os
        db_path = os.path.join(os.getcwd(), "careanchor.db")
        _db = await aiosqlite.connect(db_path)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        await ensure_schema(_db)
        print(f"[DB] Connected to persistent database: {db_path}")
    
    # Check if connection is still alive, reconnect if needed
    try:
        await _db.execute("SELECT 1")
    except:
        print("[DB] Connection lost, reconnecting...")
        import os
        db_path = os.path.join(os.getcwd(), "careanchor.db")
        _db = await aiosqlite.connect(db_path)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
    
    return _db


async def ensure_schema(db: aiosqlite.Connection | None = None) -> None:
    if db is None:
        db = await get_db()
    await db.executescript("""
        -- Core tables (existing)
        CREATE TABLE IF NOT EXISTS clinical_profiles (
            session_id TEXT PRIMARY KEY,
            profile TEXT NOT NULL DEFAULT '{}',
            session_name TEXT DEFAULT 'New Conversation',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            retention_extended_until TIMESTAMP,
            archived_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            importance_score REAL DEFAULT 0.5,
            thread_id TEXT,
            is_archived INTEGER DEFAULT 0
        );

        CREATE INDEX IF NOT EXISTS idx_chat_logs_session_id ON chat_logs(session_id);
        CREATE INDEX IF NOT EXISTS idx_chat_logs_importance ON chat_logs(importance_score DESC);
        CREATE INDEX IF NOT EXISTS idx_chat_logs_thread ON chat_logs(thread_id);

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

        -- Memory summarization tables
        CREATE TABLE IF NOT EXISTS memory_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
            summary_text TEXT NOT NULL,
            message_ids TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            token_count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_memory_summaries_session ON memory_summaries(session_id);

        -- Message metadata for embeddings and importance
        CREATE TABLE IF NOT EXISTS message_metadata (
            message_id INTEGER PRIMARY KEY REFERENCES chat_logs(id) ON DELETE CASCADE,
            importance_score REAL NOT NULL DEFAULT 0.5,
            thread_id TEXT,
            is_archived INTEGER DEFAULT 0,
            embedding BLOB
        );

        CREATE INDEX IF NOT EXISTS idx_message_metadata_thread ON message_metadata(thread_id);
        CREATE INDEX IF NOT EXISTS idx_message_metadata_importance ON message_metadata(importance_score DESC);

        -- Conversation threading
        CREATE TABLE IF NOT EXISTS conversation_threads (
            thread_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
            thread_label TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_conversation_threads_session ON conversation_threads(session_id);

        -- Profile versioning
        CREATE TABLE IF NOT EXISTS profile_versions (
            version_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
            profile_snapshot TEXT NOT NULL,
            trigger_type TEXT NOT NULL,
            user_id TEXT,
            diff_from_previous TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_profile_versions_session ON profile_versions(session_id, created_at DESC);

        -- Clinical trends
        CREATE TABLE IF NOT EXISTS clinical_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
            vital_type TEXT NOT NULL,
            trend_direction TEXT NOT NULL,
            rate_of_change REAL,
            data_points INTEGER NOT NULL,
            first_measurement TIMESTAMP NOT NULL,
            last_measurement TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_clinical_trends_session ON clinical_trends(session_id);
        CREATE INDEX IF NOT EXISTS idx_clinical_trends_vital ON clinical_trends(session_id, vital_type);

        -- Memory redactions
        CREATE TABLE IF NOT EXISTS memory_redactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
            message_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
            redacted_by TEXT,
            redacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            undone_at TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_memory_redactions_message ON memory_redactions(message_id);
    """)
    await db.commit()


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None
