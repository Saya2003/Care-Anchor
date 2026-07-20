"""API routes for managing chat sessions"""
from __future__ import annotations

from uuid import UUID
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from backend.db.sqlite import get_db

router = APIRouter()


class SessionInfo(BaseModel):
    session_id: str
    session_name: str
    message_count: int
    created_at: str
    updated_at: str
    last_message_preview: str | None = None


class UpdateSessionName(BaseModel):
    session_name: str


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions():
    """Get all chat sessions for the current user"""
    db = await get_db()
    
    # Get all sessions with message counts
    cursor = await db.execute("""
        SELECT 
            cp.session_id,
            COALESCE(cp.session_name, 'New Conversation') as session_name,
            cp.created_at,
            cp.updated_at,
            COUNT(cl.id) as message_count,
            (SELECT content FROM chat_logs 
             WHERE session_id = cp.session_id 
             ORDER BY created_at DESC LIMIT 1) as last_message
        FROM clinical_profiles cp
        LEFT JOIN chat_logs cl ON cp.session_id = cl.session_id
        GROUP BY cp.session_id
        ORDER BY cp.updated_at DESC
    """)
    
    rows = await cursor.fetchall()
    
    sessions = []
    for row in rows:
        last_message = row["last_message"]
        preview = None
        if last_message:
            # Create preview (first 100 chars)
            preview = last_message[:100] + "..." if len(last_message) > 100 else last_message
        
        sessions.append(SessionInfo(
            session_id=row["session_id"],
            session_name=row["session_name"],
            message_count=row["message_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_message_preview=preview
        ))
    
    return sessions


@router.put("/sessions/{session_id}/name")
async def update_session_name(session_id: UUID, data: UpdateSessionName):
    """Update the name of a chat session"""
    db = await get_db()
    
    # Check if session exists
    cursor = await db.execute(
        "SELECT session_id FROM clinical_profiles WHERE session_id = ?",
        (str(session_id),)
    )
    row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session name
    await db.execute(
        "UPDATE clinical_profiles SET session_name = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
        (data.session_name, str(session_id))
    )
    await db.commit()
    
    return {"success": True, "session_id": str(session_id), "session_name": data.session_name}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: UUID):
    """Delete a chat session and all associated data"""
    db = await get_db()
    
    # Check if session exists
    cursor = await db.execute(
        "SELECT session_id FROM clinical_profiles WHERE session_id = ?",
        (str(session_id),)
    )
    row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete session (CASCADE will delete chat_logs and safety_events)
    await db.execute(
        "DELETE FROM clinical_profiles WHERE session_id = ?",
        (str(session_id),)
    )
    await db.commit()
    
    return {"success": True, "session_id": str(session_id)}


class BulkDeleteRequest(BaseModel):
    session_ids: list[str]


@router.post("/sessions/bulk-delete")
async def bulk_delete_sessions(data: BulkDeleteRequest):
    """Delete multiple chat sessions at once"""
    db = await get_db()
    
    if not data.session_ids:
        raise HTTPException(status_code=400, detail="No session IDs provided")
    
    deleted_count = 0
    failed_ids = []
    
    for session_id in data.session_ids:
        try:
            # Check if session exists
            cursor = await db.execute(
                "SELECT session_id FROM clinical_profiles WHERE session_id = ?",
                (session_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                # Delete session (CASCADE will delete associated data)
                await db.execute(
                    "DELETE FROM clinical_profiles WHERE session_id = ?",
                    (session_id,)
                )
                deleted_count += 1
            else:
                failed_ids.append(session_id)
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            failed_ids.append(session_id)
    
    await db.commit()
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "failed_ids": failed_ids,
        "total_requested": len(data.session_ids)
    }


@router.get("/export/test-pdf")
async def test_pdf_export():
    """Test PDF export functionality"""
    try:
        # Create a simple test PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph("CareAnchor Test Export", styles['Title']))
        story.append(Paragraph("This is a test PDF to verify export functionality works.", styles['Normal']))
        story.append(Paragraph(f"Generated at: {datetime.now()}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=test_export.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test export failed: {str(e)}")


@router.get("/export/all-data")
async def export_all_data():
    """Export all user data as PDF"""
    db = await get_db()
    
    try:
        # Get all sessions with messages
        cursor = await db.execute("""
            SELECT 
                cp.session_id,
                cp.session_name,
                cp.created_at,
                cp.profile
            FROM clinical_profiles cp
            ORDER BY cp.created_at DESC
        """)
        sessions = await cursor.fetchall()
        
        if not sessions:
            raise HTTPException(status_code=404, detail="No data found to export")
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            topMargin=0.75*inch, 
            bottomMargin=0.75*inch,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch
        )
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#0ea5e9'),
            spaceAfter=6,
            alignment=1,  # Center
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=24,
            alignment=1,  # Center
        )
        
        session_title_style = ParagraphStyle(
            'SessionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=4,
            spaceBefore=12,
        )
        
        message_style = ParagraphStyle(
            'Message',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=8,
        )
        
        # Title page
        story.append(Paragraph("CareAnchor", title_style))
        story.append(Paragraph("My Health Data Export", subtitle_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Summary
        total_messages = 0
        for session in sessions:
            msg_cursor = await db.execute(
                "SELECT COUNT(*) as count FROM chat_logs WHERE session_id = ?",
                (session["session_id"],)
            )
            count_row = await msg_cursor.fetchone()
            total_messages += count_row["count"] if count_row else 0
        
        summary_data = [
            ["Total Conversations:", str(len(sessions))],
            ["Total Messages:", str(total_messages)],
            ["Export Date:", datetime.now().strftime('%B %d, %Y')],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Process each session
        for idx, session in enumerate(sessions):
            session_id = session["session_id"]
            session_name = session["session_name"]  
            created_at = session["created_at"]
            
            # Add page break before each new session (except first)
            if idx > 0:
                story.append(Spacer(1, 0.3*inch))
            
            # Session header
            story.append(Paragraph(f"Conversation: {session_name}", session_title_style))
            story.append(Paragraph(
                f"<i>Started: {created_at}</i>", 
                ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#64748b'))
            ))
            story.append(Spacer(1, 0.15*inch))
            
            # Get messages for this session
            msg_cursor = await db.execute("""
                SELECT role, content, created_at
                FROM chat_logs
                WHERE session_id = ?
                ORDER BY created_at ASC
            """, (session_id,))
            messages = await msg_cursor.fetchall()
            
            if messages:
                # Display messages as conversation
                for msg in messages:
                    role = msg["role"]
                    content = msg["content"]
                    timestamp_str = msg["created_at"]
                    
                    # Parse timestamp and format
                    try:
                        if isinstance(timestamp_str, str):
                            timestamp = datetime.fromisoformat(timestamp_str).strftime("%I:%M %p")
                        else:
                            timestamp = timestamp_str.strftime("%I:%M %p")
                    except:
                        timestamp = "Unknown time"
                    
                    # Role label with timestamp
                    if role == "user":
                        role_style = ParagraphStyle(
                            'UserRole',
                            parent=styles['Normal'],
                            fontSize=9,
                            textColor=colors.HexColor('#0ea5e9'),
                            fontName='Helvetica-Bold',
                        )
                        story.append(Paragraph(f"You • {timestamp}", role_style))
                    else:
                        role_style = ParagraphStyle(
                            'AssistantRole',
                            parent=styles['Normal'],
                            fontSize=9,
                            textColor=colors.HexColor('#64748b'),
                            fontName='Helvetica-Bold',
                        )
                        story.append(Paragraph(f"CareAnchor • {timestamp}", role_style))
                    
                    # Message content
                    story.append(Paragraph(content, message_style))
                    story.append(Spacer(1, 0.1*inch))
            else:
                story.append(Paragraph("<i>No messages in this conversation.</i>", styles['Italic']))
            
            # Add separator between conversations
            if idx < len(sessions) - 1:
                story.append(Spacer(1, 0.2*inch))
                story.append(Table([[""]], colWidths=[6.5*inch], style=TableStyle([
                    ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e2e8f0'))
                ])))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Return PDF as download
        filename = f"careanchor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"[ERROR] Export failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
