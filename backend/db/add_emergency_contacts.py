"""
Database migration: Add emergency contacts feature
This migration adds the emergency_contacts table for storing user emergency contact information.
"""

import asyncio
import aiosqlite
from backend.db.sqlite import get_db


async def add_emergency_contacts_table():
    """Add emergency contacts table to the database"""
    db = await get_db()
    
    await db.executescript("""
        -- Emergency contacts table
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            relationship TEXT NOT NULL,
            is_primary INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_emergency_contacts_user_id ON emergency_contacts(user_id);
        CREATE INDEX IF NOT EXISTS idx_emergency_contacts_primary ON emergency_contacts(user_id, is_primary);
    """)
    
    await db.commit()
    print("✅ Emergency contacts table created successfully")


async def rollback_emergency_contacts_table():
    """Remove emergency contacts table"""
    db = await get_db()
    
    await db.executescript("""
        DROP TABLE IF EXISTS emergency_contacts;
    """)
    
    await db.commit()
    print("✅ Emergency contacts table removed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback_emergency_contacts_table())
    else:
        asyncio.run(add_emergency_contacts_table())