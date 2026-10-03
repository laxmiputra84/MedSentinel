from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class UserInsurance(Base):
    __tablename__ = "user_insurances"
    __table_args__ = (
        Index("ix_user_insurances_user_status", "user_id", "status"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    insurance_id = Column(Integer, ForeignKey("insurances.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_number = Column(String(100), unique=True, index=True, nullable=False)
    start_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="active", index=True) # active, expired, cancelled
    sum_insured = Column(Float, nullable=False)
    dependents = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="user_insurances")
    insurance = relationship("Insurance", back_populates="user_insurances")
