from fastapi import APIRouter
from ..database import get_db, get_active_periode, get_queue_settings, get_current_time
from ..schemas.periode import PeriodeCreate, PeriodeUpdate, PeriodeResponse
import uuid

router = APIRouter()

@router.get("/periodes", response_model=list[PeriodeResponse])
def get_periodes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM periodes")
    periodes = cursor.fetchall()
    conn.close()
    return [PeriodeResponse(**dict(p)) for p in periodes]

@router.get("/periodes/active", response_model=PeriodeResponse)
def get_active_periode_endpoint():
    active_periode = get_active_periode()
    return PeriodeResponse(**active_periode) if active_periode else None

@router.post("/periodes", response_model=PeriodeResponse, status_code=201)
def create_periode(data: PeriodeCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE periodes SET is_active = 0")
    periode_id = str(uuid.uuid4())
    now = get_current_time()
    
    cursor.execute('''
        INSERT INTO periodes (id, name, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (periode_id, data.name, data.is_active, now, now))
    
    if data.is_active:
        cursor.execute("SELECT id FROM queue_settings WHERE periode_id = ?", (periode_id,))
        if not cursor.fetchone():
            settings_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO queue_settings (id, periode_id, current_queue_number, current_referral_code, next_queue_counter, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (settings_id, periode_id, 0, '', 1, now, now))
    
    conn.commit()
    conn.close()
    
    return PeriodeResponse(
        id=periode_id,
        name=data.name,
        is_active=data.is_active,
        created_at=now,
        updated_at=now
    )

@router.patch("/{periode_id}/activate", response_model=PeriodeResponse)
def activate_periode(periode_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE periodes SET is_active = 0")
    cursor.execute("UPDATE periodes SET is_active = 1 WHERE id = ?", (periode_id,))
    
    cursor.execute("SELECT id FROM queue_settings WHERE periode_id = ?", (periode_id,))
    if not cursor.fetchone():
        settings_id = str(uuid.uuid4())
        now = get_current_time()
        cursor.execute('''
            INSERT INTO queue_settings (id, periode_id, current_queue_number, current_referral_code, next_queue_counter, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (settings_id, periode_id, 0, '', 1, now, now))
    
    cursor.execute("SELECT * FROM periodes WHERE id = ?", (periode_id,))
    periode = cursor.fetchone()
    conn.commit()
    conn.close()
    
    return PeriodeResponse(**dict(periode))

@router.patch("/{periode_id}", response_model=PeriodeResponse)
def update_periode(periode_id: str, data: PeriodeUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    if data.is_active == True:
        cursor.execute("UPDATE periodes SET is_active = 0")
    
    update_fields = []
    update_values = []
    
    if data.name is not None:
        update_fields.append("name = ?")
        update_values.append(data.name)
    
    if data.is_active is not None:
        update_fields.append("is_active = ?")
        update_values.append(data.is_active)
    
    if update_fields:
        update_fields.append("updated_at = ?")
        update_values.append(get_current_time())
        update_values.append(periode_id)
        
        query = f"UPDATE periodes SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)
    
    if data.is_active == True:
        cursor.execute("SELECT id FROM queue_settings WHERE periode_id = ?", (periode_id,))
        if not cursor.fetchone():
            settings_id = str(uuid.uuid4())
            now = get_current_time()
            cursor.execute('''
                INSERT INTO queue_settings (id, periode_id, current_queue_number, current_referral_code, next_queue_counter, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (settings_id, periode_id, 0, '', 1, now, now))
    
    cursor.execute("SELECT * FROM periodes WHERE id = ?", (periode_id,))
    periode = cursor.fetchone()
    conn.commit()
    conn.close()
    
    return PeriodeResponse(**dict(periode))

@router.delete("/{periode_id}")
def delete_periode(periode_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM periodes WHERE id = ?", (periode_id,))
    conn.commit()
    conn.close()
    return {"message": "Periode deleted successfully"}