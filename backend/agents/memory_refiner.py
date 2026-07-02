from __future__ import annotations

from backend.config import settings
from backend.core.qwen_client import structured_extract

EXTRACTION_PROMPT = """You are a clinical data extraction specialist. Extract structured clinical information from the patient's message.

Return ONLY a JSON object. Use the following schema — set fields to null or empty arrays when no new information is present:

{
  "vitals": {
    "systolic_bp": number | null,
    "diastolic_bp": number | null,
    "heart_rate": number | null,
    "sp_o2": number | null,
    "temperature": number | null,
    "respiratory_rate": number | null
  },
  "symptoms": [
    { "description": string, "severity": "mild" | "moderate" | "severe", "onset": string | null }
  ],
  "medications": [
    { "name": string, "dosage": string | null, "frequency": string | null }
  ],
  "care_plan": {
    "follow_up": string | null,
    "restrictions": string[],
    "next_appointment": string | null
  }
}

Rules:
- Extract ONLY clinically relevant information. Ignore greetings, pleasantries, small talk, or casual conversation.
- Infer symptom severity from word choice: "agonizing" → "severe", "sore" → "mild", "unbearable" → "severe".
- Do NOT fabricate vitals or values the patient hasn't stated.
- If the message contains no clinical data at all, return {"vitals": {}, "symptoms": [], "medications": [], "care_plan": {}}."""


async def refine(session_context: str, user_message: str) -> dict:
    result = await structured_extract(
        model=settings.qwen_plus_model,
        system_prompt=EXTRACTION_PROMPT,
        user_content=(
            f"## Existing Profile\n{session_context}\n\n"
            f"## Patient's New Message\n{user_message}"
        ),
        json_schema={"type": "json_object"},
    )
    return result
