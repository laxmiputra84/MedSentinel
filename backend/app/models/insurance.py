from sqlalchemy import Column, Integer, String, Float, Text, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Insurance(Base):
    __tablename__ = "insurances"
    __table_args__ = (
        Index("ix_insurances_provider_type", "provider", "coverage_type"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    provider = Column(String(100), nullable=False, index=True)
    coverage_amount = Column(Float, nullable=False)
    premium_monthly = Column(Float, nullable=False)
    premium_annual = Column(Float, nullable=False)
    cashless_network = Column(Integer, default=0)
    claim_settlement_days = Column(Integer, default=3)
    rating = Column(Float, default=0.0)
    features = Column(Text, nullable=True)
    inclusions = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)
    coverage_type = Column(String(50), nullable=True)
    waiting_period_days = Column(Integer, default=30)
    eligibility_age_min = Column(Integer, default=18)
    eligibility_age_max = Column(Integer, default=65)

    # Relationships
    user_insurances = relationship("UserInsurance", back_populates="insurance", cascade="all, delete-orphan")
    claims = relationship("InsuranceClaim", back_populates="insurance")
