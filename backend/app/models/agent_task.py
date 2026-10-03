from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class AgentTask(Base):
    """
    Persistent store for tasks assigned to specialized AI agents.
    Tracks execution lifecycle, scoped input context, output findings, and retry metrics.
    """
    __tablename__ = "agent_tasks"
    __table_args__ = (
        Index("ix_agent_tasks_event_status", "event_id", "status"),
        Index("ix_agent_tasks_agent_status", "agent_type", "status"),
        Index("ix_agent_tasks_priority", "priority"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False)
    event_id = Column(String(64), ForeignKey("events.event_id", ondelete="CASCADE"), index=True, nullable=False)
    agent_type = Column(String(100), index=True, nullable=False)
    entity_id = Column(String(100), index=True, nullable=True)
    priority = Column(String(20), default="NORMAL", nullable=False)  # LOW, NORMAL, HIGH, CRITICAL
    status = Column(String(30), default="QUEUED", index=True, nullable=False)  # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    input_context = Column(Text, nullable=True)  # JSON-encoded scoped context
    output_result = Column(Text, nullable=True)  # JSON-encoded result/findings
    retry_count = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    event = relationship("Event", back_populates="tasks")
