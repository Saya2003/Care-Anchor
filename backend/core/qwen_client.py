from __future__ import annotations

import json
from typing import AsyncIterator

from openai import AsyncOpenAI

from backend.config import settings

# Async AI client for LangGraph nodes. Supports Alibaba Cloud Qwen and OpenRouter.
# Now configured to use Qwen 2.5 models on Alibaba Cloud by default for hackathon.

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        # Temporarily prefer OpenRouter (working) while fixing DashScope API key
        api_key = settings.openrouter_api_key or settings.dashscope_api_key
        base_url = settings.openrouter_base_url if settings.openrouter_api_key else settings.dashscope_base_url
        
        _client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    return _client


async def stream_chat(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_format: dict | None = None,
) -> AsyncIterator[str]:
    client = get_client()
    
    print(f"[DEBUG] Starting stream_chat with model: {model}")
    print(f"[DEBUG] API Base URL: {client.base_url}")
    print(f"[DEBUG] Number of messages: {len(messages)}")
    
    kwargs = dict(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    
    # Only add stream_options for providers that support it (not OpenRouter)
    if not settings.openrouter_api_key:
        kwargs["stream_options"] = {"include_usage": True}
    
    if response_format:
        kwargs["response_format"] = response_format

    try:
        print(f"[DEBUG] Calling API with kwargs: {list(kwargs.keys())}")
        stream = await client.chat.completions.create(**kwargs)
        print(f"[DEBUG] Stream created successfully, starting to read chunks...")
        
        token_count = 0
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                token_count += 1
                yield delta.content
        
        print(f"[DEBUG] Stream completed. Total tokens yielded: {token_count}")
        
    except Exception as e:
        # Log the error with full details
        print(f"[ERROR] Exception in stream_chat: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        yield f"[Error: {str(e)}]"


async def structured_extract(
    model: str,
    system_prompt: str,
    user_content: str,
    json_schema: dict,
) -> dict:
    client = get_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


async def vision_analyze(image_data: str, prompt: str) -> str:
    """Analyze an image using a vision-capable model."""
    client = get_client()
    
    # Use a vision-capable model - prefer OpenRouter's GPT-4o-mini for now
    vision_model = "gpt-4o-mini" if settings.openrouter_api_key else "qwen-vl-plus"
    
    try:
        response = await client.chat.completions.create(
            model=vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data}},
                    ],
                }
            ],
            max_tokens=1000,
        )
        return response.choices[0].message.content or "Could not analyze image"
    except Exception as e:
        print(f"[ERROR] Vision analysis failed: {str(e)}")
        return f"Image analysis unavailable: {str(e)}"
