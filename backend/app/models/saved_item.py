from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class SavedItem(Base):
    __tablename__ = "saved_items"
    __table_args__ = (
        Index("ix_saved_items_user_hospital", "user_id", "hospital_id"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    saved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="saved_items")
    hospital = relationship("Hospital", back_populates="saved_by")
