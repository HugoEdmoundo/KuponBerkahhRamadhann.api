from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class QueueSettings(Base):
    __tablename__ = "queue_settings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    current_queue_number = Column(Integer, default=0)
    current_referral_code = Column(Text, default='')
    next_queue_counter = Column(Integer, default=1)
    periode_id = Column(String, ForeignKey('periodes.id'), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    periode = relationship("Periode", back_populates="queue_settings")

    def __repr__(self):
        return f"<QueueSettings(id={self.id}, current_queue={self.current_queue_number}, next_counter={self.next_queue_counter})>"
