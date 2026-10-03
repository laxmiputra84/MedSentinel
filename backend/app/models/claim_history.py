from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class ClaimStatusHistory(Base):
    __tablename__ = "claim_status_history"
    __table_args__ = (
        Index("ix_claim_status_history_claim_date", "claim_id", "created_at"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    claim_id = Column(Integer, ForeignKey("insurance_claims.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    claim = relationship("InsuranceClaim", back_populates="status_history")
    updated_by = relationship("User")
