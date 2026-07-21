"""API routes for managing emergency contacts"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from backend.db.sqlite import get_db

router = APIRouter()


class EmergencyContactCreate(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    relationship: str
    is_primary: bool = False
    notes: Optional[str] = None


class EmergencyContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    relationship: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class EmergencyContact(BaseModel):
    id: int
    user_id: str
    name: str
    phone: str
    email: Optional[str] = None
    relationship: str
    is_primary: bool
    notes: Optional[str] = None
    created_at: str
    updated_at: str


@router.get("/emergency-contacts", response_model=List[EmergencyContact])
async def get_emergency_contacts(user_id: str):
    """Get all emergency contacts for a user"""
    db = await get_db()
    
    cursor = await db.execute("""
        SELECT id, user_id, name, phone, email, relationship, is_primary, notes, 
               created_at, updated_at
        FROM emergency_contacts 
        WHERE user_id = ?
        ORDER BY is_primary DESC, name ASC
    """, (user_id,))
    
    contacts = []
    async for row in cursor:
        contacts.append(EmergencyContact(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            phone=row["phone"],
            email=row["email"],
            relationship=row["relationship"],
            is_primary=bool(row["is_primary"]),
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        ))
    
    return contacts


@router.post("/emergency-contacts", response_model=EmergencyContact)
async def create_emergency_contact(user_id: str, contact: EmergencyContactCreate):
    """Create a new emergency contact"""
    db = await get_db()
    
    # If setting as primary, unset other primary contacts
    if contact.is_primary:
        await db.execute("""
            UPDATE emergency_contacts 
            SET is_primary = 0, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = ? AND is_primary = 1
        """, (user_id,))
    
    # Insert new contact
    cursor = await db.execute("""
        INSERT INTO emergency_contacts 
        (user_id, name, phone, email, relationship, is_primary, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        contact.name,
        contact.phone,
        contact.email,
        contact.relationship,
        1 if contact.is_primary else 0,
        contact.notes
    ))
    
    contact_id = cursor.lastrowid
    await db.commit()
    
    # Return the created contact
    cursor = await db.execute("""
        SELECT id, user_id, name, phone, email, relationship, is_primary, notes,
               created_at, updated_at
        FROM emergency_contacts 
        WHERE id = ?
    """, (contact_id,))
    
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found after creation")
    
    return EmergencyContact(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        phone=row["phone"],
        email=row["email"],
        relationship=row["relationship"],
        is_primary=bool(row["is_primary"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )


@router.put("/emergency-contacts/{contact_id}", response_model=EmergencyContact)
async def update_emergency_contact(contact_id: int, user_id: str, updates: EmergencyContactUpdate):
    """Update an existing emergency contact"""
    db = await get_db()
    
    # Verify contact exists and belongs to user
    cursor = await db.execute("""
        SELECT id FROM emergency_contacts 
        WHERE id = ? AND user_id = ?
    """, (contact_id, user_id))
    
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # If setting as primary, unset other primary contacts
    if updates.is_primary:
        await db.execute("""
            UPDATE emergency_contacts 
            SET is_primary = 0, updated_at = CURRENT_TIMESTAMP 
            WHERE user_id = ? AND is_primary = 1 AND id != ?
        """, (user_id, contact_id))
    
    # Build update query dynamically
    update_fields = []
    values = []
    
    if updates.name is not None:
        update_fields.append("name = ?")
        values.append(updates.name)
    if updates.phone is not None:
        update_fields.append("phone = ?")
        values.append(updates.phone)
    if updates.email is not None:
        update_fields.append("email = ?")
        values.append(updates.email)
    if updates.relationship is not None:
        update_fields.append("relationship = ?")
        values.append(updates.relationship)
    if updates.is_primary is not None:
        update_fields.append("is_primary = ?")
        values.append(1 if updates.is_primary else 0)
    if updates.notes is not None:
        update_fields.append("notes = ?")
        values.append(updates.notes)
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    values.extend([contact_id, user_id])
    
    await db.execute(f"""
        UPDATE emergency_contacts 
        SET {', '.join(update_fields)}
        WHERE id = ? AND user_id = ?
    """, values)
    
    await db.commit()
    
    # Return updated contact
    cursor = await db.execute("""
        SELECT id, user_id, name, phone, email, relationship, is_primary, notes,
               created_at, updated_at
        FROM emergency_contacts 
        WHERE id = ?
    """, (contact_id,))
    
    row = await cursor.fetchone()
    return EmergencyContact(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        phone=row["phone"],
        email=row["email"],
        relationship=row["relationship"],
        is_primary=bool(row["is_primary"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )


@router.delete("/emergency-contacts/{contact_id}")
async def delete_emergency_contact(contact_id: int, user_id: str):
    """Delete an emergency contact"""
    db = await get_db()
    
    # Verify contact exists and belongs to user
    cursor = await db.execute("""
        SELECT id FROM emergency_contacts 
        WHERE id = ? AND user_id = ?
    """, (contact_id, user_id))
    
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Delete the contact
    await db.execute("""
        DELETE FROM emergency_contacts 
        WHERE id = ? AND user_id = ?
    """, (contact_id, user_id))
    
    await db.commit()
    
    return {"success": True, "message": "Contact deleted successfully"}


@router.get("/emergency-contacts/primary", response_model=Optional[EmergencyContact])
async def get_primary_emergency_contact(user_id: str):
    """Get the primary emergency contact for a user"""
    db = await get_db()
    
    cursor = await db.execute("""
        SELECT id, user_id, name, phone, email, relationship, is_primary, notes,
               created_at, updated_at
        FROM emergency_contacts 
        WHERE user_id = ? AND is_primary = 1
        LIMIT 1
    """, (user_id,))
    
    row = await cursor.fetchone()
    if not row:
        return None
    
    return EmergencyContact(
        id=row["id"],
        user_id=row["user_id"],
        name=row["name"],
        phone=row["phone"],
        email=row["email"],
        relationship=row["relationship"],
        is_primary=bool(row["is_primary"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )