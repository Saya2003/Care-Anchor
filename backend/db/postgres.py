from __future__ import annotations

from asyncpg import Pool, create_pool

from backend.config import settings

_pool: Pool | None = None


async def get_pool() -> Pool:
    global _pool
    if _pool is None:
        dsn = settings.database_url.replace("+asyncpg", "")
        _pool = await create_pool(dsn, min_size=2, max_size=10)
    return _pool


async def ensure_schema() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS clinical_profiles (
                session_id UUID PRIMARY KEY,
                profile JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            CREATE TABLE IF NOT EXISTS chat_logs (
                id BIGSERIAL PRIMARY KEY,
                session_id UUID NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            CREATE INDEX IF NOT EXISTS idx_chat_logs_session_id ON chat_logs(session_id);
            CREATE INDEX IF NOT EXISTS idx_chat_logs_created_at ON chat_logs(created_at);

            CREATE TABLE IF NOT EXISTS safety_events (
                id BIGSERIAL PRIMARY KEY,
                session_id UUID NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
                severity TEXT NOT NULL,
                alerts JSONB NOT NULL DEFAULT '[]'::jsonb,
                risk_score REAL NOT NULL DEFAULT 0.0,
                state TEXT NOT NULL DEFAULT 'pending_acknowledgment',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );

            CREATE INDEX IF NOT EXISTS idx_safety_events_session_id ON safety_events(session_id);
            CREATE INDEX IF NOT EXISTS idx_safety_events_created_at ON safety_events(created_at);
        """)
