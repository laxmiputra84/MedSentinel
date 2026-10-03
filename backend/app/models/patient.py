from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    patient_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. MS-2026-08892
    name = Column(String(100), nullable=False)
    dob = Column(String(50), nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(20), nullable=True)
    emergency_contact = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="patients")
    documents = relationship("UserDocument", back_populates="patient", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="patient", cascade="all, delete-orphan")
    health_scores = relationship("HealthScore", back_populates="patient", cascade="all, delete-orphan")
    claims = relationship("InsuranceClaim", back_populates="patient")
    recommendations = relationship("Recommendation", back_populates="patient", cascade="all, delete-orphan")
