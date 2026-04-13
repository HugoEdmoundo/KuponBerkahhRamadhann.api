from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.warga import Warga
from ..models.queue_settings import QueueSettings
from ..models.periode import Periode
from ..schemas.warga import WargaResponse
from ..schemas.queue_settings import QueueSettingsResponse

router = APIRouter(prefix="/api/queue", tags=["queue-management"])


def get_active_periode(db: Session) -> Periode:
    """Get the active periode"""
    periode = db.query(Periode).filter(Periode.is_active == True).first()
    if not periode:
        raise HTTPException(status_code=400, detail="No active periode found")
    return periode


def get_queue_settings_for_periode(periode_id: str, db: Session) -> QueueSettings:
    """Get queue settings for a periode"""
    settings = db.query(QueueSettings).filter(QueueSettings.periode_id == periode_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Queue settings not found for active periode")
    return settings


@router.post("/next", response_model=dict)
def handle_next_queue(db: Session = Depends(get_db)):
    """
    Handle next queue operation:
    1. Change current serving to served
    2. Change first waiting to serving
    3. Update queue settings
    """
    periode = get_active_periode(db)
    queue_settings = get_queue_settings_for_periode(periode.id, db)
    
    # Find current serving
    current_serving = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "serving"
    ).first()
    
    # Mark current serving as served
    if current_serving:
        current_serving.status = "served"
    
    # Find first waiting
    first_waiting = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "waiting"
    ).order_by(Warga.queue_number).first()
    
    if first_waiting:
        # Mark as serving
        first_waiting.status = "serving"
        
        # Update queue settings
        queue_settings.current_queue_number = first_waiting.queue_number
        queue_settings.current_referral_code = first_waiting.referral_code
        
        db.commit()
        
        return {
            "message": "Queue advanced successfully",
            "current_serving": {
                "id": str(first_waiting.id),
                "name": first_waiting.name,
                "queue_number": first_waiting.queue_number,
                "referral_code": first_waiting.referral_code
            },
            "previous_serving": {
                "id": str(current_serving.id) if current_serving else None,
                "name": current_serving.name if current_serving else None
            }
        }
    else:
        # No waiting queue, reset current serving
        queue_settings.current_queue_number = 0
        queue_settings.current_referral_code = ""
        db.commit()
        
        return {
            "message": "No waiting queue found",
            "current_serving": None,
            "previous_serving": {
                "id": str(current_serving.id) if current_serving else None,
                "name": current_serving.name if current_serving else None
            }
        }


@router.post("/pending", response_model=dict)
def handle_pending_queue(db: Session = Depends(get_db)):
    """
    Handle pending operation:
    1. Change current serving to pending
    2. Call first waiting as serving
    3. Update queue settings
    """
    periode = get_active_periode(db)
    queue_settings = get_queue_settings_for_periode(periode.id, db)
    
    # Find current serving
    current_serving = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "serving"
    ).first()
    
    if not current_serving:
        raise HTTPException(status_code=400, detail="No current serving to mark as pending")
    
    # Mark current serving as pending
    current_serving.status = "pending"
    
    # Find first waiting
    first_waiting = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "waiting"
    ).order_by(Warga.queue_number).first()
    
    if first_waiting:
        # Mark as serving
        first_waiting.status = "serving"
        
        # Update queue settings
        queue_settings.current_queue_number = first_waiting.queue_number
        queue_settings.current_referral_code = first_waiting.referral_code
        
        db.commit()
        
        return {
            "message": "Queue handled pending successfully",
            "current_serving": {
                "id": str(first_waiting.id),
                "name": first_waiting.name,
                "queue_number": first_waiting.queue_number,
                "referral_code": first_waiting.referral_code
            },
            "pending": {
                "id": str(current_serving.id),
                "name": current_serving.name,
                "queue_number": current_serving.queue_number,
                "referral_code": current_serving.referral_code
            }
        }
    else:
        # No waiting queue, reset current serving
        queue_settings.current_queue_number = 0
        queue_settings.current_referral_code = ""
        db.commit()
        
        return {
            "message": "Current serving marked as pending, no waiting queue",
            "current_serving": None,
            "pending": {
                "id": str(current_serving.id),
                "name": current_serving.name,
                "queue_number": current_serving.queue_number,
                "referral_code": current_serving.referral_code
            }
        }


@router.post("/back", response_model=dict)
def handle_back_queue(db: Session = Depends(get_db)):
    """
    Handle back operation:
    1. Change current serving to waiting
    2. Get last served as serving
    3. Update queue settings
    """
    periode = get_active_periode(db)
    queue_settings = get_queue_settings_for_periode(periode.id, db)
    
    # Find current serving
    current_serving = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "serving"
    ).first()
    
    if not current_serving:
        raise HTTPException(status_code=400, detail="No current serving to go back")
    
    # Mark current serving as waiting
    current_serving.status = "waiting"
    
    # Find last served
    last_served = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "served"
    ).order_by(Warga.queue_number.desc()).first()
    
    if last_served:
        # Mark as serving
        last_served.status = "serving"
        
        # Update queue settings
        queue_settings.current_queue_number = last_served.queue_number
        queue_settings.current_referral_code = last_served.referral_code
        
        db.commit()
        
        return {
            "message": "Queue went back successfully",
            "current_serving": {
                "id": str(last_served.id),
                "name": last_served.name,
                "queue_number": last_served.queue_number,
                "referral_code": last_served.referral_code
            },
            "returned_to_waiting": {
                "id": str(current_serving.id),
                "name": current_serving.name,
                "queue_number": current_serving.queue_number,
                "referral_code": current_serving.referral_code
            }
        }
    else:
        # No served queue, reset current serving
        queue_settings.current_queue_number = 0
        queue_settings.current_referral_code = ""
        db.commit()
        
        return {
            "message": "Current serving returned to waiting, no served queue found",
            "current_serving": None,
            "returned_to_waiting": {
                "id": str(current_serving.id),
                "name": current_serving.name,
                "queue_number": current_serving.queue_number,
                "referral_code": current_serving.referral_code
            }
        }


@router.get("/status", response_model=dict)
def get_queue_status(db: Session = Depends(get_db)):
    """Get current queue status"""
    periode = get_active_periode(db)
    
    try:
        queue_settings = get_queue_settings_for_periode(periode.id, db)
    except HTTPException:
        # Create queue settings if not exists
        queue_settings = QueueSettings(periode_id=periode.id)
        db.add(queue_settings)
        db.commit()
        db.refresh(queue_settings)
    
    # Get current serving
    current_serving = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "serving"
    ).first()
    
    # Get queue counts
    waiting_count = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "waiting"
    ).count()
    
    served_count = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "served"
    ).count()
    
    pending_count = db.query(Warga).filter(
        Warga.periode_id == periode.id,
        Warga.status == "pending"
    ).count()
    
    return {
        "periode": {
            "id": str(periode.id),
            "name": periode.name
        },
        "queue_settings": {
            "current_queue_number": queue_settings.current_queue_number,
            "current_referral_code": queue_settings.current_referral_code,
            "next_queue_counter": queue_settings.next_queue_counter
        },
        "current_serving": {
            "id": str(current_serving.id) if current_serving else None,
            "name": current_serving.name if current_serving else None,
            "queue_number": current_serving.queue_number if current_serving else None,
            "referral_code": current_serving.referral_code if current_serving else None
        },
        "statistics": {
            "waiting": waiting_count,
            "serving": 1 if current_serving else 0,
            "served": served_count,
            "pending": pending_count,
            "total": waiting_count + (1 if current_serving else 0) + served_count + pending_count
        }
    }
