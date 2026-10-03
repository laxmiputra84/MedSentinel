from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class HealthScore(Base):
    __tablename__ = "health_scores"
    __table_args__ = (
        Index("ix_health_scores_patient_date", "patient_id", "calculated_at"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("user_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    health_score = Column(Integer, default=100, nullable=False) # 0 - 100
    risk_score = Column(Integer, default=0, nullable=False)     # 0 - 100
    risk_level = Column(String(20), default="LOW", nullable=False, index=True) # LOW, MODERATE, HIGH, CRITICAL
    abnormal_tests = Column(Integer, default=0, nullable=False)
    ai_summary = Column(Text, nullable=True) # Patient-friendly non-diagnostic summary
    calculated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="health_scores")
    document = relationship("UserDocument", back_populates="health_scores")
