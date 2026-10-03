from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_recommendations_user_status", "user_id", "status"),
        Index("ix_recommendations_patient_status", "patient_id", "status"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=True, index=True)

    recommendation_type = Column(String(50), nullable=False, index=True) # MISSING_RECORD, RELATED_RECORD, TREND_REVIEW, CLAIM_SUPPORT, DATA_QUALITY, DOCUMENT_FOLLOW_UP
    priority = Column(String(20), default="LOW", nullable=False, index=True) # LOW, MEDIUM, HIGH

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)

    confidence = Column(Float, default=0.0, nullable=False)
    sources = Column(Text, nullable=True) # JSON list e.g. ["RULE_BASED", "TREND_ANALYSIS"]

    status = Column(String(30), default="ACTIVE", nullable=False, index=True) # ACTIVE, VIEWED, DISMISSED, COMPLETED

    related_document_id = Column(Integer, ForeignKey("user_documents.id", ondelete="SET NULL"), nullable=True)
    related_claim_id = Column(Integer, ForeignKey("insurance_claims.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="recommendations")
    patient = relationship("Patient", back_populates="recommendations")
    document = relationship("UserDocument")
    claim = relationship("InsuranceClaim")
