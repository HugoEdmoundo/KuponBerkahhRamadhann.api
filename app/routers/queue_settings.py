from fastapi import APIRouter, HTTPException
from ..database import get_db, get_active_periode, get_queue_settings, get_current_time
from ..models.queue_settings import QueueSettingsCreate, QueueSettingsUpdate, QueueSettingsResponse
import uuid

router = APIRouter()

@router.get("/queue-settings", response_model=list[QueueSettingsResponse])
def get_all_queue_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM queue_settings")
    settings = cursor.fetchall()
    conn.close()
    return [QueueSettingsResponse(**dict(s)) for s in settings]

@router.get("/queue-settings/periode/{periode_id}", response_model=QueueSettingsResponse)
def get_queue_settings_by_periode(periode_id: str):
    settings = get_queue_settings(periode_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Queue settings not found for this periode")
    return QueueSettingsResponse(**settings)

@router.post("/queue-settings", response_model=QueueSettingsResponse, status_code=201)
def create_queue_settings(data: QueueSettingsCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM periodes WHERE id = ?", (data.periode_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Periode not found")
    
    existing = get_queue_settings(data.periode_id)
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Queue settings already exist for this periode")
    
    settings_id = str(uuid.uuid4())
    now = get_current_time()
    
    cursor.execute('''
        INSERT INTO queue_settings (id, current_queue_number, current_referral_code, next_queue_counter, periode_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (settings_id, 
          data.current_queue_number,
          data.current_referral_code,
          data.next_queue_counter,
          data.periode_id, now, now))
    
    conn.commit()
    conn.close()
    
    return QueueSettingsResponse(
        id=settings_id,
        current_queue_number=data.current_queue_number,
        current_referral_code=data.current_referral_code,
        next_queue_counter=data.next_queue_counter,
        periode_id=data.periode_id,
        created_at=now,
        updated_at=now
    )

@router.patch("/queue-settings/{settings_id}", response_model=QueueSettingsResponse)
def update_queue_settings(settings_id: str, data: QueueSettingsUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM queue_settings WHERE id = ?", (settings_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Queue settings not found")
    
    update_fields = []
    update_values = []
    
    if data.current_queue_number is not None:
        update_fields.append("current_queue_number = ?")
        update_values.append(data.current_queue_number)
    
    if data.current_referral_code is not None:
        update_fields.append("current_referral_code = ?")
        update_values.append(data.current_referral_code)
    
    if data.next_queue_counter is not None:
        update_fields.append("next_queue_counter = ?")
        update_values.append(data.next_queue_counter)
    
    if update_fields:
        update_fields.append("updated_at = ?")
        update_values.append(get_current_time())
        update_values.append(settings_id)
        
        query = f"UPDATE queue_settings SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)
    
    cursor.execute("SELECT * FROM queue_settings WHERE id = ?", (settings_id,))
    settings = cursor.fetchone()
    conn.commit()
    conn.close()
    
    return QueueSettingsResponse(**dict(settings))
