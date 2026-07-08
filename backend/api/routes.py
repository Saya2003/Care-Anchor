from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter

from backend.agents.graph import full_graph_executor
from backend.api.models import ChatRequest, ChatResponse, SessionResponse
from backend.core.memory_store import memory_store
from backend.db.sqlite import ensure_schema

router = APIRouter(prefix="/api")


@router.on_event("startup")
async def startup() -> None:
    await ensure_schema()


@router.post("/sessions", response_model=SessionResponse)
async def create_session() -> SessionResponse:
    session_id = uuid4()
    profile = await memory_store.get_profile(session_id)
    return SessionResponse(
        session_id=session_id,
        profile=dict(profile),
        chat_history=[],
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID) -> SessionResponse:
    profile = await memory_store.get_profile(session_id)
    chats = await memory_store.get_recent_chats(session_id)
    return SessionResponse(
        session_id=session_id,
        profile=dict(profile),
        chat_history=chats,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    profile = await memory_store.get_profile(req.session_id)
    chats = await memory_store.get_recent_chats(req.session_id)

    state = {
        "session_id": req.session_id,
        "user_message": req.message,
        "chat_history": chats,
        "profile_context": str(dict(profile)),
        "extracted_clinical_data": {},
        "safety_check": {"breached": False, "alerts": []},
        "interrupt_triggered": False,
        "response_text": "",
    }

    async for update in full_graph_executor.astream(state, stream_mode="values"):
        state.update(update)

    return ChatResponse(
        session_id=req.session_id,
        response=state.get("response_text", ""),
        extracted_clinical_data=state.get("extracted_clinical_data", {}),
        safety_check=state.get("safety_check", {"breached": False, "alerts": []}),
        interrupt_triggered=state.get("interrupt_triggered", False),
    )
