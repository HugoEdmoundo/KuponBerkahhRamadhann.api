from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import random
import string

from ..database import get_db
from ..models.warga import Warga
from ..models.periode import Periode
from ..models.queue_settings import QueueSettings
from ..schemas.warga import WargaCreate, WargaResponse, WargaUpdate

router = APIRouter(prefix="/api/registrations", tags=["registrations"])


def generate_referral_code(length: int = 8) -> str:
    """Generate random referral code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))


@router.get("/", response_model=List[WargaResponse])
def get_registrations(
    periodeId: Optional[str] = Query(None, description="Filter by periode ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get registrations with optional filters"""
    query = db.query(Warga)
    
    if periodeId:
        query = query.filter(Warga.periode_id == periodeId)
    
    if status:
        if status not in ['waiting', 'serving', 'served', 'pending']:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: waiting, serving, served, or pending")
        query = query.filter(Warga.status == status)
    
    # Order by queue_number
    registrations = query.order_by(Warga.queue_number).all()
    return registrations


@router.get("/{registration_id}", response_model=WargaResponse)
def get_registration(registration_id: str, db: Session = Depends(get_db)):
    """Get registration by ID"""
    registration = db.query(Warga).filter(Warga.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    return registration


@router.post("/", response_model=WargaResponse, status_code=201)
def create_registration(registration: WargaCreate, db: Session = Depends(get_db)):
    """Create a new registration"""
    # Verify periode exists
    periode = db.query(Periode).filter(Periode.id == registration.periode_id).first()
    if not periode:
        raise HTTPException(status_code=404, detail="Periode not found")
    
    # Get or create queue settings for this periode
    queue_settings = db.query(QueueSettings).filter(QueueSettings.periode_id == registration.periode_id).first()
    if not queue_settings:
        queue_settings = QueueSettings(periode_id=registration.periode_id)
        db.add(queue_settings)
        db.commit()
        db.refresh(queue_settings)
    
    # Generate unique referral code
    referral_code = generate_referral_code()
    while db.query(Warga).filter(Warga.referral_code == referral_code).first():
        referral_code = generate_referral_code()
    
    # Create registration
    db_registration = Warga(
        name=registration.name,
        kk_number=registration.kk_number,
        rt_rw=registration.rt_rw,
        referral_code=referral_code,
        queue_number=queue_settings.next_queue_counter,
        status="waiting",
        periode_id=registration.periode_id
    )
    
    # Update queue settings counter
    queue_settings.next_queue_counter += 1
    
    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)
    
    return db_registration


@router.patch("/{registration_id}", response_model=WargaResponse)
def update_registration(
    registration_id: str, 
    registration_update: WargaUpdate, 
    db: Session = Depends(get_db)
):
    """Update registration"""
    registration = db.query(Warga).filter(Warga.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    update_data = registration_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(registration, field, value)
    
    db.commit()
    db.refresh(registration)
    return registration


@router.delete("/{registration_id}", status_code=204)
def delete_registration(registration_id: str, db: Session = Depends(get_db)):
    """Delete registration"""
    registration = db.query(Warga).filter(Warga.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    db.delete(registration)
    db.commit()
    return None
