from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class InsuranceClaim(Base):
    __tablename__ = "insurance_claims"
    __table_args__ = (
        Index("ix_insurance_claims_user_status", "user_id", "claim_status"),
        Index("ix_insurance_claims_status_date", "claim_status", "claim_date"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    insurance_id = Column(Integer, ForeignKey("insurances.id", ondelete="SET NULL"), nullable=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True, index=True)
    claim_amount = Column(Float, nullable=False)
    claim_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    claim_status = Column(String(50), default="SUBMITTED", nullable=False, index=True) # SUBMITTED, UNDER_REVIEW, DOCUMENTS_REQUIRED, APPROVED, REJECTED, COMPLETED
    claim_description = Column(Text, nullable=True)
    documents = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="insurance_claims")
    insurance = relationship("Insurance", back_populates="claims")
    hospital = relationship("Hospital", back_populates="claims")
    status_history = relationship("ClaimStatusHistory", back_populates="claim", cascade="all, delete-orphan", order_by="ClaimStatusHistory.created_at.desc()")
