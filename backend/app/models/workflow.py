"""
MedSentinel Agentic Architecture — Persistent Workflow Models
Stores durable workflow state, execution steps, checkpoints, events, and human reviews in MySQL.
Ensures workflows survive server restarts and can be inspected or resumed.
"""

from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Boolean, Float
from sqlalchemy.orm import relationship
from app.core.database import Base


class WorkflowInstance(Base):
    """
    Durable persistence of a MedSentinel agentic workflow execution.
    Maintains serialized state snapshot, plan, and lifecycle status.
    """
    __tablename__ = "workflows"
    __table_args__ = (
        Index("ix_workflows_user_id", "user_id"),
        Index("ix_workflows_patient_id", "patient_id"),
        Index("ix_workflows_status", "status"),
        Index("ix_workflows_type", "workflow_type"),
        Index("ix_workflows_created_at", "created_at"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    workflow_id = Column(String(64), unique=True, index=True, nullable=False)
    workflow_type = Column(String(50), nullable=False, default="AUTOMATIC")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    document_id = Column(Integer, nullable=True)
    status = Column(String(40), default="PENDING", nullable=False)  # PENDING, IN_PROGRESS, COMPLETED, FAILED, DOCTOR_REVIEW_REQUIRED, CANCELLED
    current_step = Column(String(100), nullable=True)
    plan_json = Column(Text, nullable=True)  # JSON-serialized execution plan DAG
    state_json = Column(Text, nullable=True)  # Full serialized WorkflowState snapshot
    retry_count = Column(Integer, default=0, nullable=False)
    failure_reason = Column(Text, nullable=True)
    escalation_required = Column(Boolean, default=False, nullable=False)
    escalation_reason = Column(Text, nullable=True)
    escalation_level = Column(String(30), default="NONE", nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    steps = relationship("WorkflowStepRecord", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStepRecord.id")
    events = relationship("WorkflowEventRecord", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowEventRecord.id")
    checkpoints = relationship("WorkflowCheckpointRecord", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowCheckpointRecord.id")
    reviews = relationship("HumanReviewRecord", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStepRecord(Base):
    """
    Granular execution telemetry and output record for each agent in a workflow.
    """
    __tablename__ = "workflow_steps"
    __table_args__ = (
        Index("ix_workflow_steps_wf_agent", "workflow_id", "agent_name"),
        Index("ix_workflow_steps_status", "status"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.workflow_id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, default=0, nullable=False)
    agent_name = Column(String(100), nullable=False, index=True)
    status = Column(String(30), default="RUNNING", nullable=False)  # RUNNING, COMPLETED, FAILED, SKIPPED, WAITING_FOR_HUMAN
    inputs_json = Column(Text, nullable=True)
    outputs_json = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    workflow = relationship("WorkflowInstance", back_populates="steps")


class WorkflowEventRecord(Base):
    """
    Chronological event log for workflow execution (consumed by SSE and audit).
    """
    __tablename__ = "workflow_events"
    __table_args__ = (
        Index("ix_workflow_events_wf_time", "workflow_id", "created_at"),
        Index("ix_workflow_events_type", "event_type"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.workflow_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(60), nullable=False)  # WORKFLOW_STARTED, AGENT_STARTED, AGENT_COMPLETED, SAFETY_REVIEW, etc.
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    workflow = relationship("WorkflowInstance", back_populates="events")


class WorkflowCheckpointRecord(Base):
    """
    State checkpoint after each agent execution for resume, retry, or rollback.
    """
    __tablename__ = "workflow_checkpoints"
    __table_args__ = (
        Index("ix_checkpoints_wf_step", "workflow_id", "step_index"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.workflow_id", ondelete="CASCADE"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    agent_name = Column(String(100), nullable=False)
    state_snapshot = Column(Text, nullable=False)  # JSON-encoded state at this point
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    workflow = relationship("WorkflowInstance", back_populates="checkpoints")


class HumanReviewRecord(Base):
    """
    Human-in-the-Loop review ticket created when clinical safety or fraud escalation occurs.
    """
    __tablename__ = "human_reviews"
    __table_args__ = (
        Index("ix_human_reviews_workflow", "workflow_id"),
        Index("ix_human_reviews_status", "status"),
        Index("ix_human_reviews_patient", "patient_id"),
        Index("ix_human_reviews_risk", "risk_level"),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    review_id = Column(String(64), unique=True, index=True, nullable=False)
    workflow_id = Column(String(64), ForeignKey("workflows.workflow_id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    risk_level = Column(String(20), default="HIGH", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, ESCALATED, MODIFIED
    reason = Column(Text, nullable=False)
    clinical_context_json = Column(Text, nullable=True)
    findings_json = Column(Text, nullable=True)
    
    decision = Column(String(30), nullable=True)  # APPROVE, REJECT, REQUEST_MORE_INFO, ESCALATE
    reviewer_notes = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    workflow = relationship("WorkflowInstance", back_populates="reviews")
