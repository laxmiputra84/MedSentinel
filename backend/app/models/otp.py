from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from datetime import datetime, timezone
from app.core.database import Base

class OtpCode(Base):
    __tablename__ = "otp_codes"
    __table_args__ = (
        Index("ix_otp_codes_phone_verified", "phone", "is_verified"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone = Column(String(20), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
