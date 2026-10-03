from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.core.database import Base

class AIConversation(Base):
    __tablename__ = "ai_conversations"
    __table_args__ = (
        Index("ix_ai_conversations_user_created", "user_id", "created_at"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), default="New Medical Consultation")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="AIMessage.created_at.asc()")

class AIMessage(Base):
    __tablename__ = "ai_messages"
    __table_args__ = (
        Index("ix_ai_messages_conv_created", "conversation_id", "created_at"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    tools_used = Column(Text, nullable=True)     # JSON array string of tool names
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    conversation = relationship("AIConversation", back_populates="messages")
