from __future__ import annotations

from typing import AsyncIterator

from backend.config import settings
from backend.core.ai_client import stream_chat

RESPONDER_PROMPT = """You are CareAnchor, an autonomous post-discharge clinical assistant helping patients recover at home.

Style & boundaries:
- Be warm, clear, and concise (2-3 paragraphs max).
- Reference the patient's clinical profile naturally in your response.
- Never diagnose or prescribe — always recommend consulting their doctor.
- If an emergency is detected, urge immediate medical attention.

The patient's clinical profile is in the system context. Use it to personalise your response."""

SAFETY_OVERRIDE_WARN = """CLINICAL WARNING - ELEVATED VITAL SIGNS

The following observations were noted:
{alerts}

Your response MUST:
1. Acknowledge the specific readings that are elevated
2. Recommend monitoring the situation closely and rechecking in 1-2 hours
3. Advise the patient to contact their doctor if symptoms worsen
4. Provide routine care suggestions ONLY if explicitly safe (e.g., hydration, rest)
5. Do NOT escalate to emergency services unless the patient reports additional critical symptoms"""

SAFETY_OVERRIDE_CRITICAL = """SAFETY INTERRUPT - CRITICAL THRESHOLD BREACHED

The following alerts were triggered:
{alerts}

Your response MUST:
1. Acknowledge the specific risk immediately
2. Advise the patient to seek emergency medical attention right now
3. Disable ANY routine advice, self-care suggestions, or normal conversation
4. Recommend calling emergency services or going to the nearest emergency department
5. Do NOT minimise the situation - be direct and clear"""


async def generate_response(
    profile_context: str,
    chat_history: list[dict],
    user_message: str,
    safety_interrupt: bool = False,
    safety_alerts: list[str] | None = None,
    safety_severity: str = "critical",
) -> AsyncIterator[str]:
    system_parts = [RESPONDER_PROMPT]

    if safety_interrupt and safety_alerts:
        override = (
            SAFETY_OVERRIDE_CRITICAL
            if safety_severity == "critical"
            else SAFETY_OVERRIDE_WARN
        )
        system_parts.append(
            override.format(alerts="\n".join(f"- {a}" for a in safety_alerts))
        )

    if profile_context:
        system_parts.append(f"## Patient Clinical Profile\n{profile_context}")

    messages = [{"role": "system", "content": "\n\n".join(system_parts)}]

    for entry in chat_history[-6:]:
        messages.append({"role": entry["role"], "content": entry["content"]})

    messages.append({"role": "user", "content": user_message})

    async for token in stream_chat(
        model=settings.response_model,
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
    ):
        yield token
