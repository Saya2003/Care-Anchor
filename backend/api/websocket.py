from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.agents.graph import run_agent
from backend.core.memory_store import memory_store
from backend.db.postgres import ensure_schema

router = APIRouter()


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: UUID) -> None:
    await websocket.accept()
    await ensure_schema()

    try:
        profile = await memory_store.get_profile(session_id)
        chats = await memory_store.get_recent_chats(session_id)

        await websocket.send_json({
            "type": "session_init",
            "profile": dict(profile),
            "chat_history": chats,
        })

        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            user_message = payload.get("message", "").strip()
            if not user_message:
                continue

            async for event in run_agent(
                session_id=session_id,
                user_message=user_message,
                chat_history=chats,
                profile_context=str(dict(profile)),
            ):
                await websocket.send_json(event)

            profile = await memory_store.get_profile(session_id)
            chats = await memory_store.get_recent_chats(session_id)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "detail": str(exc)})
        except Exception:
            pass
