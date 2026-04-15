from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PeriodeBase(BaseModel):
    name: str
    is_active: bool = False

class PeriodeCreate(PeriodeBase):
    pass

class PeriodeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class PeriodeResponse(PeriodeBase):
    id: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
