"""
Rollback script for Enhanced Chat and Memory migration.
Removes the tables and columns added by the migration.

WARNING: This will delete all enhanced memory data (summaries, threads, versions, etc.)
         Chat logs and clinical profiles will be preserved.

Run this script to rollback:
    python -m backend.db.rollback_enhanced_memory
"""
import asyncio
import os
import aiosqlite
from datetime import datetime


async def backup_database(db_path: str) -> str:
    """Create a backup of the database before rollback."""
    backup_path = f"{db_path}.rollback_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async with aiosqlite.connect(db_path) as source:
        async with aiosqlite.connect(backup_path) as backup:
            await source.backup(backup)
    
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path


async def rollback_database(db_path: str):
    """Remove enhanced memory features from database."""
    print(f"[ROLLBACK] Starting rollback for: {db_path}")
    
    # Create backup first
    await backup_database(db_path)
    
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys=OFF")
        
        print("[ROLLBACK] Dropping enhanced memory tables...")
        
        # Drop new tables
        await db.executescript("""
            DROP TABLE IF EXISTS memory_redactions;
            DROP TABLE IF EXISTS clinical_trends;
            DROP TABLE IF EXISTS profile_versions;
            DROP TABLE IF EXISTS conversation_threads;
            DROP TABLE IF EXISTS message_metadata;
            DROP TABLE IF EXISTS memory_summaries;
        """)
        print("  ✅ Dropped all enhanced memory tables")
        
        print("[ROLLBACK] Dropping enhanced memory indexes...")
        
        # Drop indexes for columns we'll remove
        await db.executescript("""
            DROP INDEX IF EXISTS idx_chat_logs_importance;
            DROP INDEX IF EXISTS idx_chat_logs_thread;
        """)
        print("  ✅ Dropped enhanced memory indexes")
        
        print("[ROLLBACK] Note: SQLite does not support dropping columns directly")
        print("           Columns added to clinical_profiles and chat_logs will remain")
        print("           but can be safely ignored. They contain default values only.")
        
        await db.execute("PRAGMA foreign_keys=ON")
        await db.commit()
        
        print("[ROLLBACK] ✅ Rollback completed successfully!")


async def verify_rollback(db_path: str):
    """Verify that rollback was successful."""
    print("\n[VERIFICATION] Checking rollback results...")
    
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in await cursor.fetchall()]
        await cursor.close()
        
        removed_tables = [
            "memory_summaries",
            "message_metadata",
            "conversation_threads",
            "profile_versions",
            "clinical_trends",
            "memory_redactions"
        ]
        
        print("\n[VERIFICATION] Table removal check:")
        for table in removed_tables:
            status = "✅" if table not in tables else "❌"
            state = "removed" if table not in tables else "still exists"
            print(f"  {status} {table} ({state})")
        
        # Core tables should still exist
        print("\n[VERIFICATION] Core tables preserved:")
        core_tables = ["clinical_profiles", "chat_logs", "safety_events"]
        for table in core_tables:
            status = "✅" if table in tables else "❌"
            print(f"  {status} {table}")


async def main():
    """Main rollback entry point."""
    db_path = os.path.join(os.getcwd(), "careanchor.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print("=" * 60)
    print("Enhanced Chat and Memory - Database Rollback")
    print("=" * 60)
    print("\n⚠️  WARNING: This will remove all enhanced memory features:")
    print("   - Memory summaries")
    print("   - Conversation threads")
    print("   - Profile versions")
    print("   - Clinical trends")
    print("   - Memory redactions")
    print("\n   Core chat logs and clinical profiles will be preserved.")
    print("=" * 60)
    
    response = input("\nAre you sure you want to proceed? (yes/no): ")
    if response.lower() != "yes":
        print("Rollback cancelled.")
        return
    
    try:
        await rollback_database(db_path)
        await verify_rollback(db_path)
        
        print("\n" + "=" * 60)
        print("✅ Rollback completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        print("   Please restore from backup and contact support.")
        raise


if __name__ == "__main__":
    asyncio.run(main())
