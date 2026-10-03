from sqlalchemy import Column, Integer, String, Float, Text, Boolean, Index
from sqlalchemy.orm import relationship
from app.core.database import Base

class Hospital(Base):
    __tablename__ = "hospitals"
    __table_args__ = (
        Index("ix_hospitals_location_specialization", "location", "specialization"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    location = Column(String(200), nullable=True, index=True)
    specialization = Column(String(200), nullable=True, index=True)
    rating = Column(Float, default=0.0, index=True)
    distance = Column(Float, default=0.0, index=True)
    cost_range = Column(String(100), nullable=True)
    schemes = Column(Text, nullable=True)
    insurance_accepted = Column(Text, nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)
    image_url = Column(String(255), nullable=True)
    facilities = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Relationships
    saved_by = relationship("SavedItem", back_populates="hospital", cascade="all, delete-orphan")
    claims = relationship("InsuranceClaim", back_populates="hospital")
