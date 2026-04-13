from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


class WargaBase(BaseModel):
    name: str = Field(..., min_length=1, description="Nama peserta antrian")
    kk_number: str = Field(..., min_length=1, description="Nomor kartu keluarga")
    rt_rw: str = Field(..., min_length=1, description="RT/RW peserta")
    status: str = Field(default="waiting", description="Status antrian")
    queue_number: int = Field(..., description="Nomor antrian")
    referral_code: str = Field(..., min_length=1, description="Kode referral unik")
    periode_id: str = Field(..., description="ID periode aktif")

    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['waiting', 'serving', 'served', 'pending']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v


class WargaCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Nama peserta antrian")
    kk_number: str = Field(..., min_length=1, description="Nomor kartu keluarga")
    rt_rw: str = Field(..., min_length=1, description="RT/RW peserta")
    periode_id: str = Field(..., description="ID periode aktif")


class WargaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Nama peserta antrian")
    kk_number: Optional[str] = Field(None, min_length=1, description="Nomor kartu keluarga")
    rt_rw: Optional[str] = Field(None, min_length=1, description="RT/RW peserta")
    status: Optional[str] = Field(None, description="Status antrian")

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['waiting', 'serving', 'served', 'pending']
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v


class WargaResponse(WargaBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
