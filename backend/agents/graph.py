from __future__ import annotations

from typing import AsyncIterator, Literal
from uuid import UUID

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from backend.agents.clinical_responder import generate_response
from backend.agents.memory_refiner import refine
from backend.agents.tools import check_safety_thresholds, update_clinical_profile
from backend.core.interrupt import interrupt_controller
from backend.core.memory_store import memory_store


class AgentState(TypedDict):
    session_id: UUID
    user_message: str
    chat_history: list[dict]
    profile_context: str
    extracted_clinical_data: dict
    safety_check: dict
    interrupt_triggered: bool
    safety_severity: str
    response_text: str


# ─── Orchestration nodes (non-streaming) ──────────────────────────────


async def extract_clinical_data(state: AgentState) -> dict:
    extracted = await refine(state["profile_context"], state["user_message"])
    return {"extracted_clinical_data": extracted}


async def apply_memory_update(state: AgentState) -> dict:
    data = state.get("extracted_clinical_data", {})
    if not data:
        return {}
    non_empty = {k: v for k, v in data.items() if v}
    if non_empty:
        await update_clinical_profile(state["session_id"], non_empty)
    return {}


async def run_safety_check(state: AgentState) -> dict:
    data = state.get("extracted_clinical_data", {})
    vitals = data.get("vitals", {})
    check = await check_safety_thresholds(vitals, state["user_message"])
    triggered = check["breached"]
    sev = check.get("severity", "info")

    if triggered:
        try:
            await memory_store.insert_safety_event(
                session_id=state["session_id"],
                severity=sev,
                alerts=check.get("alerts", []),
                risk_score=check.get("risk_score", 0.0),
            )
        except Exception:
            pass
        interrupt_controller.start_interrupt(
            session_id=str(state["session_id"]),
            severity=sev,
            alerts=check.get("alerts", []),
            risk_score=check.get("risk_score", 0.0),
        )

    return {"safety_check": check, "interrupt_triggered": triggered, "safety_severity": sev}


# ─── Responder nodes (accumulated — used by the full graph) ────────────


async def respond_normal(state: AgentState) -> dict:
    tokens: list[str] = []
    async for token in generate_response(
        profile_context=state["profile_context"],
        chat_history=state["chat_history"],
        user_message=state["user_message"],
    ):
        tokens.append(token)
    response_text = "".join(tokens)
    await memory_store.append_chat(state["session_id"], "user", state["user_message"])
    await memory_store.append_chat(state["session_id"], "assistant", response_text)
    return {"response_text": response_text}


async def respond_interrupt(state: AgentState) -> dict:
    alerts = state["safety_check"].get("alerts", [])
    sev = state.get("safety_severity", "critical")
    tokens: list[str] = []
    async for token in generate_response(
        profile_context=state["profile_context"],
        chat_history=state["chat_history"],
        user_message=state["user_message"],
        safety_interrupt=True,
        safety_alerts=alerts,
        safety_severity=sev,
    ):
        tokens.append(token)
    response_text = "".join(tokens)
    await memory_store.append_chat(state["session_id"], "user", state["user_message"])
    await memory_store.append_chat(state["session_id"], "assistant", response_text)

    if interrupt_controller.should_notify(str(state["session_id"])):
        await _fire_alert_webhook(state["session_id"], alerts, state["user_message"], sev)
        interrupt_controller.mark_notified(str(state["session_id"]))

    return {"response_text": response_text}


async def _fire_alert_webhook(
    session_id: UUID, alerts: list[str], message: str, severity: str = "critical"
) -> None:
    from backend.config import settings

    if not settings.alert_webhook_url:
        return
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                settings.alert_webhook_url,
                json={
                    "session_id": str(session_id),
                    "severity": severity,
                    "alerts": alerts,
                    "message": message,
                },
            )
    except Exception:
        pass


# ─── Full graph (orchestration + respond, no token streaming) ─────────


def decide_route(state: AgentState) -> Literal["respond_normal", "respond_interrupt"]:
    if state["interrupt_triggered"]:
        return "respond_interrupt"
    return "respond_normal"


full_graph = StateGraph(AgentState)
for name in (
    "extract_clinical_data",
    "apply_memory_update",
    "run_safety_check",
    "respond_normal",
    "respond_interrupt",
):
    full_graph.add_node(name, locals()[name])

full_graph.set_entry_point("extract_clinical_data")
full_graph.add_edge("extract_clinical_data", "apply_memory_update")
full_graph.add_edge("apply_memory_update", "run_safety_check")
full_graph.add_conditional_edges(
    "run_safety_check",
    decide_route,
    {"respond_normal": "respond_normal", "respond_interrupt": "respond_interrupt"},
)
full_graph.add_edge("respond_normal", END)
full_graph.add_edge("respond_interrupt", END)

full_graph_executor = full_graph.compile()


# ─── Orchestration-only graph (for WebSocket token streaming) ─────────

orchestration_graph = StateGraph(AgentState)
for name in ("extract_clinical_data", "apply_memory_update", "run_safety_check"):
    orchestration_graph.add_node(name, locals()[name])

orchestration_graph.set_entry_point("extract_clinical_data")
orchestration_graph.add_edge("extract_clinical_data", "apply_memory_update")
orchestration_graph.add_edge("apply_memory_update", "run_safety_check")
orchestration_graph.add_edge("run_safety_check", END)

orchestration_executor = orchestration_graph.compile()


# ─── Public API ───────────────────────────────────────────────────────


async def run_agent(
    session_id: UUID,
    user_message: str,
    chat_history: list[dict],
    profile_context: str,
) -> AsyncIterator[dict]:
    """Two-phase execution for WebSocket consumers.

    Phase 1 — orchestration graph: extract → memory → safety
    Phase 2 — token-level streaming from the clinical responder
    """
    state: AgentState = {
        "session_id": session_id,
        "user_message": user_message,
        "chat_history": chat_history,
        "profile_context": profile_context,
        "extracted_clinical_data": {},
        "safety_check": {"breached": False, "alerts": []},
        "interrupt_triggered": False,
        "safety_severity": "info",
        "response_text": "",
    }

    # Phase 1
    async for update in orchestration_executor.astream(state, stream_mode="values"):
        state.update(update)

    yield {"type": "node_end", "node": "run_safety_check"}
    yield {
        "type": "safety_result",
        "extracted_clinical_data": state.get("extracted_clinical_data", {}),
        "safety_check": state.get("safety_check", {"breached": False, "alerts": []}),
        "interrupt_triggered": state.get("interrupt_triggered", False),
    }

    # Phase 2
    safety_interrupt = state["interrupt_triggered"]
    safety_severity = state.get("safety_severity", "info")
    safety_alerts = state.get("safety_check", {}).get("alerts", [])

    tokens: list[str] = []
    yield {"type": "node_start", "node": "respond"}
    async for token in generate_response(
        profile_context=profile_context,
        chat_history=chat_history,
        user_message=user_message,
        safety_interrupt=safety_interrupt,
        safety_alerts=safety_alerts,
        safety_severity=safety_severity,
    ):
        tokens.append(token)
        yield {"type": "token", "content": token}

    response_text = "".join(tokens)
    await memory_store.append_chat(session_id, "user", user_message)
    if response_text:
        await memory_store.append_chat(session_id, "assistant", response_text)

    if safety_interrupt and interrupt_controller.should_notify(str(session_id)):
        await _fire_alert_webhook(
            session_id, safety_alerts, user_message, safety_severity
        )
        interrupt_controller.mark_notified(str(session_id))

    yield {
        "type": "done",
        "data": {
            "response": response_text,
            "extracted_clinical_data": state.get("extracted_clinical_data", {}),
            "safety_check": state.get("safety_check", {"breached": False, "alerts": []}),
            "interrupt_triggered": safety_interrupt,
        },
    }
