from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Event(Base):
    """
    Persistent store for healthcare system and user events.
    Guarantees event deduplication, idempotency, and audit traceability.
    """
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_type_status", "event_type", "status"),
        Index("ix_events_entity", "entity_type", "entity_id"),
        Index("ix_events_user_created", "user_id", "created_at"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    event_type = Column(String(100), index=True, nullable=False)
    entity_type = Column(String(50), index=True, nullable=False)
    entity_id = Column(String(100), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    payload = Column(Text, nullable=True)  # JSON-encoded payload
    status = Column(String(30), default="PENDING", index=True, nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED, RETRYING
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    user = relationship("User")
    tasks = relationship("AgentTask", back_populates="event", cascade="all, delete-orphan", order_by="AgentTask.id")
