from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Periode(Base):
    __tablename__ = "periodes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    warga = relationship("Warga", back_populates="periode")
    queue_settings = relationship("QueueSettings", back_populates="periode")

    def __repr__(self):
        return f"<Periode(id={self.id}, name={self.name}, is_active={self.is_active})>"
