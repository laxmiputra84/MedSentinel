from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class HospitalImage(Base):
    __tablename__ = "hospital_images"
    __table_args__ = (
        Index("ix_hospital_images_hospital_type", "hospital_id", "image_type"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    image_type = Column(String(50), nullable=False) # LOGO, COVER, GALLERY, FACILITY, DOCTOR, DOCUMENT
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    ai_generated_caption = Column(Text, nullable=True)
    is_approved_by_admin = Column(Boolean, default=True, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    hospital = relationship("Hospital")
    uploader = relationship("User")
