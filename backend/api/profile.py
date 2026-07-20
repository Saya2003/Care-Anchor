"""API routes for clinical profile and activity"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json

from backend.db.sqlite import get_db

router = APIRouter()


class ClinicalProfileResponse(BaseModel):
    session_id: str
    profile: dict
    last_updated: str


class ActivityItem(BaseModel):
    session_id: str
    session_name: str
    timestamp: str
    message_preview: str
    message_count: int


@router.get("/profile/latest")
async def get_latest_profile():
    """Get the most recently updated clinical profile"""
    db = await get_db()
    
    cursor = await db.execute("""
        SELECT session_id, profile, updated_at
        FROM clinical_profiles
        WHERE profile != '{}'
        ORDER BY updated_at DESC
        LIMIT 1
    """)
    row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="No clinical profile found")
    
    profile_data = json.loads(row["profile"]) if row["profile"] else {}
    
    return {
        "session_id": row["session_id"],
        "profile": profile_data,
        "last_updated": row["updated_at"]
    }


@router.get("/activity/recent")
async def get_recent_activity(limit: int = 10):
    """Get recent activity (recent check-ins/messages)"""
    db = await get_db()
    
    # Get sessions with recent messages
    cursor = await db.execute("""
        SELECT 
            cp.session_id,
            cp.session_name,
            cp.updated_at,
            (SELECT content FROM chat_logs 
             WHERE session_id = cp.session_id 
             ORDER BY created_at DESC LIMIT 1) as last_message,
            (SELECT COUNT(*) FROM chat_logs 
             WHERE session_id = cp.session_id) as message_count
        FROM clinical_profiles cp
        WHERE EXISTS (SELECT 1 FROM chat_logs WHERE session_id = cp.session_id)
        ORDER BY cp.updated_at DESC
        LIMIT ?
    """, (limit,))
    
    rows = await cursor.fetchall()
    
    activities = []
    for row in rows:
        last_message = row["last_message"] or ""
        preview = last_message[:100] + "..." if len(last_message) > 100 else last_message
        
        activities.append({
            "session_id": row["session_id"],
            "session_name": row["session_name"],
            "timestamp": row["updated_at"],
            "message_preview": preview,
            "message_count": row["message_count"]
        })
    
    return activities
