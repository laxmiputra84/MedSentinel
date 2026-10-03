from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_user_status", "user_id", "status"),
        Index("ix_appointments_hospital_status", "hospital_id", "status"),
        Index("ix_appointments_date_dept", "preferred_date", "department"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(150), nullable=False)
    preferred_date = Column(String(50), nullable=False, index=True)
    preferred_time = Column(String(50), nullable=False)
    department = Column(String(100), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="CONFIRMED", nullable=False, index=True) # PENDING, CONFIRMED, COMPLETED, CANCELLED
    notes = Column(Text, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="appointments")
    hospital = relationship("Hospital")
