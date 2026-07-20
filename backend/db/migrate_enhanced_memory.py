"""
Migration script for Enhanced Chat and Memory feature.
Adds new tables and columns to support memory summarization, importance scoring,
semantic search, conversation threading, versioning, and trend detection.

Run this script to migrate an existing database:
    python -m backend.db.migrate_enhanced_memory
"""
import asyncio
import os
import aiosqlite
from datetime import datetime


async def backup_database(db_path: str) -> str:
    """Create a backup of the database before migration."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Read original database
    async with aiosqlite.connect(db_path) as source:
        # Write to backup
        async with aiosqlite.connect(backup_path) as backup:
            await source.backup(backup)
    
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path


async def check_column_exists(db: aiosqlite.Connection, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor = await db.execute(f"PRAGMA table_info({table})")
    columns = await cursor.fetchall()
    await cursor.close()
    return any(col[1] == column for col in columns)


async def migrate_database(db_path: str):
    """Apply migration to add enhanced memory features."""
    print(f"[MIGRATION] Starting migration for: {db_path}")
    
    # Create backup first
    await backup_database(db_path)
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys=OFF")
        
        print("[MIGRATION] Adding new columns to existing tables...")
        
        # Add columns to clinical_profiles if they don't exist
        if not await check_column_exists(db, "clinical_profiles", "retention_extended_until"):
            await db.execute("ALTER TABLE clinical_profiles ADD COLUMN retention_extended_until TIMESTAMP")
            print("  ✅ Added retention_extended_until to clinical_profiles")
        
        if not await check_column_exists(db, "clinical_profiles", "archived_at"):
            await db.execute("ALTER TABLE clinical_profiles ADD COLUMN archived_at TIMESTAMP")
            print("  ✅ Added archived_at to clinical_profiles")
        
        # Add columns to chat_logs if they don't exist
        if not await check_column_exists(db, "chat_logs", "importance_score"):
            await db.execute("ALTER TABLE chat_logs ADD COLUMN importance_score REAL DEFAULT 0.5")
            print("  ✅ Added importance_score to chat_logs")
        
        if not await check_column_exists(db, "chat_logs", "thread_id"):
            await db.execute("ALTER TABLE chat_logs ADD COLUMN thread_id TEXT")
            print("  ✅ Added thread_id to chat_logs")
        
        if not await check_column_exists(db, "chat_logs", "is_archived"):
            await db.execute("ALTER TABLE chat_logs ADD COLUMN is_archived INTEGER DEFAULT 0")
            print("  ✅ Added is_archived to chat_logs")
        
        print("[MIGRATION] Creating new tables...")
        
        # Create new tables
        await db.executescript("""
            -- Memory summaries
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

            -- Message metadata
            CREATE TABLE IF NOT EXISTS message_metadata (
                message_id INTEGER PRIMARY KEY REFERENCES chat_logs(id) ON DELETE CASCADE,
                importance_score REAL NOT NULL DEFAULT 0.5,
                thread_id TEXT,
                is_archived INTEGER DEFAULT 0,
                embedding BLOB
            );

            -- Conversation threads
            CREATE TABLE IF NOT EXISTS conversation_threads (
                thread_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
                thread_label TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Profile versions
            CREATE TABLE IF NOT EXISTS profile_versions (
                version_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
                profile_snapshot TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                user_id TEXT,
                diff_from_previous TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

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

            -- Memory redactions
            CREATE TABLE IF NOT EXISTS memory_redactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES clinical_profiles(session_id) ON DELETE CASCADE,
                message_id INTEGER NOT NULL REFERENCES chat_logs(id) ON DELETE CASCADE,
                redacted_by TEXT,
                redacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                undone_at TIMESTAMP
            );
        """)
        print("  ✅ Created all new tables")
        
        print("[MIGRATION] Creating indexes...")
        
        # Create indexes
        await db.executescript("""
            CREATE INDEX IF NOT EXISTS idx_chat_logs_importance ON chat_logs(importance_score DESC);
            CREATE INDEX IF NOT EXISTS idx_chat_logs_thread ON chat_logs(thread_id);
            CREATE INDEX IF NOT EXISTS idx_memory_summaries_session ON memory_summaries(session_id);
            CREATE INDEX IF NOT EXISTS idx_message_metadata_thread ON message_metadata(thread_id);
            CREATE INDEX IF NOT EXISTS idx_message_metadata_importance ON message_metadata(importance_score DESC);
            CREATE INDEX IF NOT EXISTS idx_conversation_threads_session ON conversation_threads(session_id);
            CREATE INDEX IF NOT EXISTS idx_profile_versions_session ON profile_versions(session_id, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_clinical_trends_session ON clinical_trends(session_id);
            CREATE INDEX IF NOT EXISTS idx_clinical_trends_vital ON clinical_trends(session_id, vital_type);
            CREATE INDEX IF NOT EXISTS idx_memory_redactions_message ON memory_redactions(message_id);
        """)
        print("  ✅ Created all indexes")
        
        await db.execute("PRAGMA foreign_keys=ON")
        await db.commit()
        
        print("[MIGRATION] ✅ Migration completed successfully!")
        print("[MIGRATION] Database schema updated with enhanced memory features")


async def verify_migration(db_path: str):
    """Verify that migration was successful."""
    print("\n[VERIFICATION] Checking migration results...")
    
    async with aiosqlite.connect(db_path) as db:
        # Check for new tables
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in await cursor.fetchall()]
        await cursor.close()
        
        expected_tables = [
            "clinical_profiles",
            "chat_logs",
            "safety_events",
            "memory_summaries",
            "message_metadata",
            "conversation_threads",
            "profile_versions",
            "clinical_trends",
            "memory_redactions"
        ]
        
        print("\n[VERIFICATION] Table check:")
        for table in expected_tables:
            status = "✅" if table in tables else "❌"
            print(f"  {status} {table}")
        
        # Check for new columns
        print("\n[VERIFICATION] Column check (clinical_profiles):")
        for column in ["retention_extended_until", "archived_at"]:
            exists = await check_column_exists(db, "clinical_profiles", column)
            status = "✅" if exists else "❌"
            print(f"  {status} {column}")
        
        print("\n[VERIFICATION] Column check (chat_logs):")
        for column in ["importance_score", "thread_id", "is_archived"]:
            exists = await check_column_exists(db, "chat_logs", column)
            status = "✅" if exists else "❌"
            print(f"  {status} {column}")
        
        # Check for indexes
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in await cursor.fetchall()]
        await cursor.close()
        
        print("\n[VERIFICATION] Index check:")
        expected_indexes = [
            "idx_chat_logs_importance",
            "idx_chat_logs_thread",
            "idx_memory_summaries_session",
            "idx_message_metadata_thread",
            "idx_conversation_threads_session",
            "idx_profile_versions_session",
            "idx_clinical_trends_session"
        ]
        
        for index in expected_indexes:
            status = "✅" if index in indexes else "❌"
            print(f"  {status} {index}")


async def main():
    """Main migration entry point."""
    db_path = os.path.join(os.getcwd(), "careanchor.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("   The database will be created automatically when you run the application.")
        return
    
    print("=" * 60)
    print("Enhanced Chat and Memory - Database Migration")
    print("=" * 60)
    
    try:
        await migrate_database(db_path)
        await verify_migration(db_path)
        
        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("   Please restore from backup and contact support.")
        raise


if __name__ == "__main__":
    asyncio.run(main())
