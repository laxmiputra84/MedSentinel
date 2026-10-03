from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class FraudAnalysis(Base):
    __tablename__ = "fraud_analyses"
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    claim_id = Column(Integer, ForeignKey("insurance_claims.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    fraud_score = Column(Integer, default=0, nullable=False) # 0 - 100
    fraud_risk = Column(String(20), default="LOW", nullable=False, index=True) # LOW, MEDIUM, HIGH
    flags = Column(Text, nullable=True) # JSON list of strings
    duplicate_docs_detected = Column(Boolean, default=False, nullable=False)
    duplicate_invoices_detected = Column(Boolean, default=False, nullable=False)
    reused_hash_detected = Column(Boolean, default=False, nullable=False)
    patient_mismatch_detected = Column(Boolean, default=False, nullable=False)
    suspicious_amount_flag = Column(Boolean, default=False, nullable=False)
    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    claim = relationship("InsuranceClaim", back_populates="fraud_analysis")
