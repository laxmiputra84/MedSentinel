from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class PluginStatus(str, enum.Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    DISCONNECTED = "DISCONNECTED"
    REVOKED = "REVOKED"
    ERROR = "ERROR"
    MOCK_SANDBOX = "MOCK/SANDBOX"

class ActionRiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class PluginConnection(Base):
    __tablename__ = "plugin_connections"

    id = Column(Integer, primary_key=True, index=True)
    plugin_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)
    provider = Column(String(64), nullable=False)
    status = Column(String(32), default=PluginStatus.CONNECTED.value, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    config_metadata = Column(JSON, nullable=True) # Encrypted or masked config
    permissions = Column(JSON, nullable=True) # Allowed scopes
    rate_limit_rpm = Column(Integer, default=60, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    last_tested_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "plugin_id": self.plugin_id,
            "name": self.name,
            "category": self.category,
            "provider": self.provider,
            "status": self.status,
            "is_enabled": self.is_enabled,
            "permissions": self.permissions or [],
            "rate_limit_rpm": self.rate_limit_rpm,
            "usage_count": self.usage_count,
            "error_count": self.error_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_tested_at": self.last_tested_at.isoformat() if self.last_tested_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class PluginActionAudit(Base):
    __tablename__ = "plugin_action_audits"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(64), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    agent_id = Column(String(64), index=True, nullable=False)
    plugin_id = Column(String(64), index=True, nullable=False)
    tool_name = Column(String(128), index=True, nullable=False)
    resource_id = Column(String(128), nullable=True)
    risk_level = Column(String(32), default=ActionRiskLevel.LOW.value, nullable=False)
    parameters_masked = Column(JSON, nullable=True)
    decision = Column(String(256), nullable=True)
    policy_evaluation = Column(String(256), nullable=True)
    approval_status = Column(String(32), default="NOT_REQUIRED", nullable=False)
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    external_transaction_id = Column(String(128), nullable=True)
    result_summary = Column(Text, nullable=True)
    verification_status = Column(String(32), default="VERIFIED", nullable=False)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "plugin_id": self.plugin_id,
            "tool_name": self.tool_name,
            "resource_id": self.resource_id,
            "risk_level": self.risk_level,
            "parameters": self.parameters_masked,
            "decision": self.decision,
            "approval_status": self.approval_status,
            "approved_by_id": self.approved_by_id,
            "external_transaction_id": self.external_transaction_id,
            "result_summary": self.result_summary,
            "verification_status": self.verification_status,
            "error_message": self.error_message,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class PluginApprovalRequest(Base):
    __tablename__ = "plugin_approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(64), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    agent_id = Column(String(64), nullable=False)
    plugin_id = Column(String(64), nullable=False)
    tool_name = Column(String(128), nullable=False)
    parameters = Column(JSON, nullable=False)
    risk_level = Column(String(32), default=ActionRiskLevel.HIGH.value, nullable=False)
    status = Column(String(32), default=ApprovalStatus.PENDING.value, nullable=False)
    requester_notes = Column(Text, nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "plugin_id": self.plugin_id,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "risk_level": self.risk_level,
            "status": self.status,
            "requester_notes": self.requester_notes,
            "reviewer_id": self.reviewer_id,
            "reviewer_comment": self.reviewer_comment,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class EmergencyControl(Base):
    __tablename__ = "emergency_controls"

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String(32), nullable=False) # GLOBAL, PLUGIN, AGENT, OUTBOUND, EXTERNAL_API
    target_id = Column(String(64), nullable=True) # Specific plugin_id or agent_id or ALL
    is_paused = Column(Boolean, default=False, nullable=False)
    reason = Column(String(256), nullable=True)
    triggered_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    triggered_by = relationship("User", foreign_keys=[triggered_by_id])

    def to_dict(self):
        return {
            "id": self.id,
            "scope": self.scope,
            "target_id": self.target_id,
            "is_paused": self.is_paused,
            "reason": self.reason,
            "triggered_by_id": self.triggered_by_id,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class PluginWebhookEvent(Base):
    __tablename__ = "plugin_webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(64), index=True, nullable=False) # whatsapp, sms, voice, etc.
    event_id = Column(String(128), index=True, nullable=True) # Provider-issued idempotency/message ID
    event_type = Column(String(64), nullable=False) # message, delivery_receipt, call_event, etc.
    signature_header = Column(String(256), nullable=True)
    signature_valid = Column(Boolean, default=False, nullable=False)
    payload_preview = Column(JSON, nullable=True)
    processed = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "provider": self.provider,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "signature_valid": self.signature_valid,
            "processed": self.processed,
            "error_message": self.error_message,
            "received_at": self.received_at.isoformat() if self.received_at else None,
        }
