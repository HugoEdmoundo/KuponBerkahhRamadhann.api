from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.queue_settings import QueueSettings
from ..models.periode import Periode
from ..schemas.queue_settings import QueueSettingsCreate, QueueSettingsResponse, QueueSettingsUpdate

router = APIRouter(prefix="/api/queue-settings", tags=["queue-settings"])


@router.get("/", response_model=List[QueueSettingsResponse])
def get_all_queue_settings(db: Session = Depends(get_db)):
    """Get all queue settings"""
    settings = db.query(QueueSettings).all()
    return settings


@router.get("/periode/{periode_id}", response_model=QueueSettingsResponse)
def get_queue_settings_by_periode(periode_id: str, db: Session = Depends(get_db)):
    """Get queue settings for a specific periode"""
    settings = db.query(QueueSettings).filter(QueueSettings.periode_id == periode_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Queue settings not found for this periode")
    return settings


@router.post("/", response_model=QueueSettingsResponse, status_code=201)
def create_queue_settings(settings: QueueSettingsCreate, db: Session = Depends(get_db)):
    """Create queue settings for a periode"""
    # Verify periode exists
    periode = db.query(Periode).filter(Periode.id == settings.periode_id).first()
    if not periode:
        raise HTTPException(status_code=404, detail="Periode not found")
    
    # Check if settings already exist for this periode
    existing = db.query(QueueSettings).filter(QueueSettings.periode_id == settings.periode_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Queue settings already exist for this periode")
    
    db_settings = QueueSettings(**settings.dict())
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings


@router.patch("/{settings_id}", response_model=QueueSettingsResponse)
def update_queue_settings(
    settings_id: str, 
    settings_update: QueueSettingsUpdate, 
    db: Session = Depends(get_db)
):
    """Update queue settings"""
    settings = db.query(QueueSettings).filter(QueueSettings.id == settings_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Queue settings not found")
    
    update_data = settings_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    db.commit()
    db.refresh(settings)
    return settings
