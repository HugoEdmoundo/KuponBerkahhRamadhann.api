from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PeriodeBase(BaseModel):
    name: str = Field(..., min_length=1, description="Nama periode")
    is_active: bool = Field(default=False, description="Status aktif periode")


class PeriodeCreate(PeriodeBase):
    pass


class PeriodeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Nama periode")
    is_active: Optional[bool] = Field(None, description="Status aktif periode")


class PeriodeResponse(PeriodeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
