from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.periode import Periode
from ..schemas.periode import PeriodeCreate, PeriodeResponse, PeriodeUpdate

router = APIRouter(prefix="/api/periodes", tags=["periodes"])


@router.get("/", response_model=List[PeriodeResponse])
def get_all_periodes(db: Session = Depends(get_db)):
    """Get all periodes"""
    periodes = db.query(Periode).all()
    return periodes


@router.get("/active", response_model=PeriodeResponse)
def get_active_periode(db: Session = Depends(get_db)):
    """Get the active periode"""
    periode = db.query(Periode).filter(Periode.is_active == True).first()
    if not periode:
        raise HTTPException(status_code=404, detail="No active periode found")
    return periode


@router.post("/", response_model=PeriodeResponse, status_code=201)
def create_periode(periode: PeriodeCreate, db: Session = Depends(get_db)):
    """Create a new periode"""
    # If this periode is set to active, deactivate all other periodes
    if periode.is_active:
        db.query(Periode).filter(Periode.is_active == True).update({"is_active": False})
    
    db_periode = Periode(**periode.dict())
    db.add(db_periode)
    db.commit()
    db.refresh(db_periode)
    return db_periode


@router.patch("/{periode_id}/activate", response_model=PeriodeResponse)
def activate_periode(periode_id: str, db: Session = Depends(get_db)):
    """Set a periode as active (deactivates all others)"""
    # Check if periode exists
    periode = db.query(Periode).filter(Periode.id == periode_id).first()
    if not periode:
        raise HTTPException(status_code=404, detail="Periode not found")
    
    # Deactivate all periodes
    db.query(Periode).filter(Periode.is_active == True).update({"is_active": False})
    
    # Activate this periode
    periode.is_active = True
    db.commit()
    db.refresh(periode)
    return periode


@router.patch("/{periode_id}", response_model=PeriodeResponse)
def update_periode(periode_id: str, periode_update: PeriodeUpdate, db: Session = Depends(get_db)):
    """Update a periode"""
    periode = db.query(Periode).filter(Periode.id == periode_id).first()
    if not periode:
        raise HTTPException(status_code=404, detail="Periode not found")
    
    # If setting this periode to active, deactivate all others
    update_data = periode_update.dict(exclude_unset=True)
    if update_data.get("is_active") == True:
        db.query(Periode).filter(Periode.is_active == True).update({"is_active": False})
    
    for field, value in update_data.items():
        setattr(periode, field, value)
    
    db.commit()
    db.refresh(periode)
    return periode


@router.delete("/{periode_id}", status_code=204)
def delete_periode(periode_id: str, db: Session = Depends(get_db)):
    """Delete a periode"""
    periode = db.query(Periode).filter(Periode.id == periode_id).first()
    if not periode:
        raise HTTPException(status_code=404, detail="Periode not found")
    
    db.delete(periode)
    db.commit()
    return None
