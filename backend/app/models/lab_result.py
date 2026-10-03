from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class LabResult(Base):
    __tablename__ = "lab_results"
    __table_args__ = (
        Index("ix_lab_results_patient_test", "patient_id", "test_name"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("user_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    test_name = Column(String(100), nullable=False, index=True) # e.g. Hemoglobin, WBC, CRP, Potassium
    observed_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False) # e.g. g/dL, cells/uL, mg/L
    reference_min = Column(Float, nullable=True)
    reference_max = Column(Float, nullable=True)
    status = Column(String(20), default="NORMAL", nullable=False) # NORMAL, LOW, HIGH, CRITICAL, UNKNOWN
    is_critical = Column(Boolean, default=False, nullable=False)
    test_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="lab_results")
    document = relationship("UserDocument", back_populates="lab_results")
