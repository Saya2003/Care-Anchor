"""
Simple script to apply the enhanced memory schema to the SQLite database.
Run this from the project root: python apply_schema.py
"""
import asyncio
import os
import aiosqlite
from datetime import datetime


async def apply_schema():
    """Apply the enhanced memory schema to the database."""
    db_path = os.path.join(os.getcwd(), "careanchor.db")
    
    print(f"Applying enhanced memory schema to: {db_path}")
    
    # Create backup
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        async with aiosqlite.connect(db_path) as source:
            async with aiosqlite.connect(backup_path) as backup:
                await source.backup(backup)
        print(f"✅ Backup created: {backup_path}")
    
    # Apply schema
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys=ON")
        
        # Read and execute the schema file
        with open("backend/db/enhanced_memory_schema.sql", "r") as f:
            schema_sql = f.read()
        
        await db.executescript(schema_sql)
        await db.commit()
        
        print("✅ Schema applied successfully!")
        
        # Verify tables
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in await cursor.fetchall()]
        await cursor.close()
        
        print(f"\n✅ Database now has {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")


if __name__ == "__main__":
    asyncio.run(apply_schema())
