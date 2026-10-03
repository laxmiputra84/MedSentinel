from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class UserDocument(Base):
    __tablename__ = "user_documents"
    __table_args__ = (
        Index("ix_user_documents_user_status", "user_id", "status"),
        Index("ix_user_documents_user_type", "user_id", "doc_type"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doc_type = Column(String(100), default="Other", index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, default=0)
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, APPROVED, REJECTED
    verified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="documents")
    verified_by = relationship("User", foreign_keys=[verified_by_id])
