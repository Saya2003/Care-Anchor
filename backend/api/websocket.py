from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.agents.graph import run_agent
from backend.core.memory_store import memory_store
from backend.db.sqlite import ensure_schema

router = APIRouter()


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: UUID) -> None:
    print(f"[WS] WebSocket connection accepted for session {session_id}")
    await websocket.accept()
    await ensure_schema()

    try:
        print(f"[WS] Fetching profile and chat history...")
        profile = await memory_store.get_profile(session_id)
        chats = await memory_store.get_recent_chats(session_id)
        
        print(f"[WS] Sending session_init with {len(chats)} messages")
        await websocket.send_json({
            "type": "session_init",
            "profile": dict(profile),
            "chat_history": chats,
        })

        while True:
            print(f"[WS] Waiting for message...")
            raw = await websocket.receive_text()
            print(f"[WS] Received raw message: {raw[:100]}...")
            
            payload = json.loads(raw)
            user_message = payload.get("message", "").strip()
            attachments = payload.get("attachments", [])
            
            print(f"[WS] Parsed user message: {user_message}")
            print(f"[WS] Attachments: {len(attachments)} files")
            
            if not user_message and not attachments:
                print(f"[WS] Empty message, skipping")
                continue

            # Process attachments if present
            attachment_context = ""
            if attachments:
                attachment_context = await process_attachments(attachments)
                print(f"[WS] Processed attachments, context length: {len(attachment_context)}")

            # Combine message with attachment context
            full_message = user_message
            if attachment_context:
                full_message = f"{user_message}\n\n[Attached files analysis]:\n{attachment_context}"

            print(f"[WS] Starting agent run...")
            async for event in run_agent(
                session_id=session_id,
                user_message=full_message,
                chat_history=chats,
                profile_context=str(dict(profile)),
            ):
                print(f"[WS] Agent event: {event.get('type', 'unknown')}")
                await websocket.send_json(event)

            print(f"[WS] Agent run complete, refreshing data...")
            profile = await memory_store.get_profile(session_id)
            chats = await memory_store.get_recent_chats(session_id)

    except WebSocketDisconnect:
        print(f"[WS] WebSocket disconnected for session {session_id}")
    except Exception as exc:
        print(f"[WS ERROR] Exception in websocket_chat: {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"type": "error", "detail": str(exc)})
        except Exception:
            pass


async def process_attachments(attachments: list[dict]) -> str:
    """Process attached files and return extracted text/analysis."""
    import base64
    from io import BytesIO
    
    results = []
    
    for attachment in attachments:
        file_name = attachment.get("name", "unknown")
        file_type = attachment.get("type", "")
        data_url = attachment.get("dataUrl", "")
        
        try:
            # Extract base64 data
            if "," in data_url:
                base64_data = data_url.split(",", 1)[1]
            else:
                base64_data = data_url
            
            file_bytes = base64.b64decode(base64_data)
            
            # Process based on file type
            if file_type.startswith("image/"):
                # For images, use vision model to analyze
                result = await analyze_image(file_bytes, file_type)
                results.append(f"**{file_name}** (Image):\n{result}")
            
            elif file_type == "application/pdf":
                # Extract text from PDF
                result = await extract_pdf_text(file_bytes)
                results.append(f"**{file_name}** (PDF):\n{result}")
            
            elif file_type == "text/plain":
                # Plain text file
                text = file_bytes.decode("utf-8")
                results.append(f"**{file_name}** (Text):\n{text[:2000]}")
            
            elif "word" in file_type or file_type.endswith("document"):
                # Word documents
                result = await extract_docx_text(file_bytes)
                results.append(f"**{file_name}** (Document):\n{result}")
                
        except Exception as e:
            results.append(f"**{file_name}**: Error processing file - {str(e)}")
    
    return "\n\n".join(results)


async def analyze_image(image_bytes: bytes, mime_type: str) -> str:
    """Analyze image using vision model."""
    import base64
    from backend.core.qwen_client import vision_analyze
    
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        result = await vision_analyze(
            image_data=f"data:{mime_type};base64,{base64_image}",
            prompt="Analyze this image in detail. If it contains medical information (prescriptions, medical reports, lab results, vitals), extract all relevant clinical data. If it's a general image, describe what you see."
        )
        return result
    except Exception as e:
        return f"Could not analyze image: {str(e)}"


async def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF file."""
    try:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return "PDF processing unavailable. Install pypdf2: pip install pypdf2"
        
        from io import BytesIO
        
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        
        text_parts = []
        for page in reader.pages[:10]:  # Limit to first 10 pages
            text_parts.append(page.extract_text())
        
        full_text = "\n".join(text_parts)
        return full_text[:5000] if full_text.strip() else "PDF appears to be empty or contains only images"
    except Exception as e:
        return f"Could not extract PDF text: {str(e)}"


async def extract_docx_text(docx_bytes: bytes) -> str:
    """Extract text from Word document."""
    try:
        try:
            import docx
        except ImportError:
            return "Word document processing unavailable. Install python-docx: pip install python-docx"
        
        from io import BytesIO
        
        doc_file = BytesIO(docx_bytes)
        doc = docx.Document(doc_file)
        
        text_parts = [para.text for para in doc.paragraphs]
        full_text = "\n".join(text_parts)
        return full_text[:5000] if full_text.strip() else "Document appears to be empty"
    except Exception as e:
        return f"Could not extract document text: {str(e)}"
