from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    __table_args__ = (
        Index("ix_admin_audit_logs_action_resource", "action", "resource_type"),
        Index("ix_admin_audit_logs_admin_created", "admin_user_id", "created_at"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    admin_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True) # e.g. USER_ROLE_CHANGED, HOSPITAL_UPDATED, CLAIM_APPROVED
    resource_type = Column(String(50), nullable=False, index=True) # e.g. User, Hospital, Claim, Document, Scheme
    resource_id = Column(String(50), nullable=True)
    old_value = Column(Text, nullable=True) # JSON or descriptive string
    new_value = Column(Text, nullable=True) # JSON or descriptive string
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    admin_user = relationship("User")
