from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class Warga(Base):
    __tablename__ = "warga"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text, nullable=False)
    kk_number = Column(Text, nullable=False)
    rt_rw = Column(Text, nullable=False)
    referral_code = Column(Text, nullable=False, unique=True)
    queue_number = Column(Integer, nullable=False)
    status = Column(Text, nullable=False, default='waiting')  # waiting, serving, served, pending
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    periode_id = Column(String, ForeignKey('periodes.id'), nullable=False)

    # Relationships
    periode = relationship("Periode", back_populates="warga")

    def __repr__(self):
        return f"<Warga(id={self.id}, name={self.name}, queue_number={self.queue_number}, status={self.status})>"
