from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class QueueSettingsBase(BaseModel):
    current_queue_number: int = Field(default=0, description="Nomor antrian yang sedang dipanggil")
    current_referral_code: str = Field(default="", description="Kode referral dari antrean yang sedang dipanggil")
    next_queue_counter: int = Field(default=1, description="Nomor antrean berikutnya untuk pendaftaran baru")
    periode_id: str = Field(..., description="ID periode terkait")


class QueueSettingsCreate(QueueSettingsBase):
    pass


class QueueSettingsUpdate(BaseModel):
    current_queue_number: Optional[int] = Field(None, description="Nomor antrian yang sedang dipanggil")
    current_referral_code: Optional[str] = Field(None, description="Kode referral dari antrean yang sedang dipanggil")
    next_queue_counter: Optional[int] = Field(None, description="Nomor antrean berikutnya untuk pendaftaran baru")


class QueueSettingsResponse(QueueSettingsBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
