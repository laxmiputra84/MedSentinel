from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class AIRequestLog(Base):
    __tablename__ = "ai_request_logs"
    __table_args__ = (
        Index("ix_ai_request_logs_user_status", "user_id", "status"),
        Index("ix_ai_request_logs_created", "created_at"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(String(100), nullable=True, index=True)
    request_type = Column(String(50), default="PRIVATE_CHAT", nullable=False) # PRIVATE_CHAT, TOOL_CHAT, ADMIN_INSIGHTS, RAG_RETRIEVAL
    provider = Column(String(50), default="gemini", nullable=False)
    model = Column(String(100), default="gemini-1.5-flash", nullable=False)
    status = Column(String(50), default="SUCCESS", nullable=False) # SUCCESS, ERROR, RATE_LIMITED, FILTERED
    latency_ms = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    datasets_used = Column(Text, nullable=True) # JSON list of dataset IDs or titles
    tools_used = Column(Text, nullable=True) # JSON list of tools invoked
    error_code = Column(String(100), nullable=True) # e.g. AI_PROVIDER_RATE_LIMITED, AI_PROVIDER_UNAVAILABLE, AI_TIMEOUT
    user_query_preview = Column(String(255), nullable=True) # Redacted preview
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User")
