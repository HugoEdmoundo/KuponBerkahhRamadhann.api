from fastapi import APIRouter, Query, HTTPException
from ..database import get_db, get_active_periode, get_queue_settings, get_current_time, generate_referral_code
from ..websocket import manager, broadcast_websocket
from ..models.warga import WargaCreate, WargaUpdate, WargaResponse
import uuid
import json
from typing import Optional

router = APIRouter()

@router.get("/registrations", response_model=list[WargaResponse])
def get_registrations(periodeId: Optional[str] = Query(None, description="Filter by periode ID"), status: Optional[str] = Query(None, description="Filter by status")):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM warga WHERE 1=1"
    params = []
    
    if periodeId:
        query += " AND periode_id = ?"
        params.append(periodeId)
    
    if status:
        if status not in ['waiting', 'serving', 'served', 'pending']:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: waiting, serving, served, or pending")
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY queue_number"
    
    cursor.execute(query, params)
    registrations = cursor.fetchall()
    conn.close()
    return [WargaResponse(**dict(r)) for r in registrations]


@router.post("/registrations", response_model=WargaResponse, status_code=201)
def create_registration(data: WargaCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify periode exists
    cursor.execute("SELECT id FROM periodes WHERE id = ?", (data.periode_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Periode not found")
    
    cursor.execute("SELECT next_queue_counter FROM queue_settings WHERE periode_id = ?", (data.periode_id,))
    settings = cursor.fetchone()
    next_queue = settings["next_queue_counter"] if settings else 1
    
    referral_code = generate_referral_code()
    cursor.execute("SELECT id FROM warga WHERE referral_code = ?", (referral_code,))
    while cursor.fetchone():
        referral_code = generate_referral_code()
        cursor.execute("SELECT id FROM warga WHERE referral_code = ?", (referral_code,))
    
    registration_id = str(uuid.uuid4())
    now = get_current_time()
    
    cursor.execute('''
        INSERT INTO warga (id, name, kk_number, rt_rw, referral_code, queue_number, status, created_at, updated_at, periode_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (registration_id, data.name, data.kk_number, data.rt_rw, 
          referral_code, next_queue, "waiting", now, now, data.periode_id))
    
    if settings:
        cursor.execute("UPDATE queue_settings SET next_queue_counter = next_queue_counter + 1 WHERE periode_id = ?", (data.periode_id,))
    else:
        settings_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO queue_settings (id, current_queue_number, current_referral_code, next_queue_counter, periode_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (settings_id, 0, "", next_queue + 1, data.periode_id, now, now))
    
    conn.commit()
    conn.close()
    
    broadcast_websocket(json.dumps({
        "type": "registration_created",
        "data": {
            "id": registration_id,
            "name": data.name,
            "queue_number": next_queue,
            "referral_code": referral_code,
            "status": "waiting",
            "periode_id": data.periode_id
        }
    }))
    
    return WargaResponse(
        id=registration_id,
        name=data.name,
        kk_number=data.kk_number,
        rt_rw=data.rt_rw,
        referral_code=referral_code,
        queue_number=next_queue,
        status="waiting",
        created_at=now,
        updated_at=now,
        periode_id=data.periode_id
    )

@router.patch("/registrations/{registration_id}", response_model=WargaResponse)
def update_registration(registration_id: str, data: WargaUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM warga WHERE id = ?", (registration_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Registration not found")
    
    update_fields = []
    update_values = []
    
    if data.name is not None:
        update_fields.append("name = ?")
        update_values.append(data.name)
    
    if data.kk_number is not None:
        update_fields.append("kk_number = ?")
        update_values.append(data.kk_number)
    
    if data.rt_rw is not None:
        update_fields.append("rt_rw = ?")
        update_values.append(data.rt_rw)
    
    if data.status is not None:
        if data.status not in ['waiting', 'serving', 'served', 'pending']:
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid status. Must be: waiting, serving, served, or pending")
        update_fields.append("status = ?")
        update_values.append(data.status)
    
    if update_fields:
        update_fields.append("updated_at = ?")
        update_values.append(get_current_time())
        update_values.append(registration_id)
        
        query = f"UPDATE warga SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)
    
    cursor.execute("SELECT * FROM warga WHERE id = ?", (registration_id,))
    registration = cursor.fetchone()
    conn.commit()
    conn.close()
    
    return WargaResponse(**dict(registration))

@router.delete("/registrations/{registration_id}")
def delete_registration(registration_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM warga WHERE id = ?", (registration_id,))
    conn.commit()
    conn.close()
    return {"message": "Registration deleted successfully"}
