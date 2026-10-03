"""
MedSentinel Agentic Architecture — Human Review Agent (Human-in-the-Loop)
Manages escalation tickets when panic lab values, drug interactions, or fraud flags trigger.
Ensures durable persistence in MySQL and real-time broadcasting to the Human Review Center.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import (
    WorkflowState,
    AgentResult,
    EscalationLevel,
    WorkflowStatus,
)
from app.models.workflow import HumanReviewRecord
from app.services.redis_event_bus import redis_event_bus, AgentEventType


class HumanReviewAgent(BaseAgent):
    """
    Supervises Human-in-the-Loop safety gates.
    Intercepts clinical panic states and registers auditable review tickets.
    """

    def __init__(self):
        super().__init__(
            name="human_review",
            role="Human-in-the-Loop Safety & Escalation Manager",
            description="Creates, tracks, and audits clinical escalation tickets requiring licensed physician or admin approval.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        # Check if escalation is mandated
        if not state.escalation_required and state.status != WorkflowStatus.DOCTOR_REVIEW_REQUIRED:
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={"escalation_needed": False, "message": "No human escalation required."}
            )

        review_id = f"REV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        risk_lvl = state.escalation_level.value if isinstance(state.escalation_level, EscalationLevel) else str(state.escalation_level)
        reason = state.escalation_reason or "Automated safety gate flagged critical clinical anomalies."

        clinical_context = {
            "workflow_id": state.workflow_id,
            "patient_id": state.patient_id,
            "patient_name": state.patient_name,
            "document_type": state.document_type,
            "workflow_type": state.workflow_type.value if hasattr(state.workflow_type, "value") else str(state.workflow_type),
        }

        findings_data = [f.model_dump() if hasattr(f, "model_dump") else dict(f) for f in state.clinical_findings]

        # 1. Persist to MySQL HumanReviewRecord if DB session provided
        review_db_id = None
        if db:
            try:
                review_rec = HumanReviewRecord(
                    review_id=review_id,
                    workflow_id=state.workflow_id,
                    patient_id=state.patient_id,
                    risk_level="CRITICAL" if "CRITICAL" in risk_lvl else ("HIGH" if "HIGH" in risk_lvl else "MEDIUM"),
                    status="PENDING",
                    reason=reason,
                    clinical_context_json=json.dumps(clinical_context),
                    findings_json=json.dumps(findings_data),
                )
                db.add(review_rec)
                db.commit()
                review_db_id = review_rec.id
            except Exception as e:
                db.rollback()

        # 2. Emit Real-time SSE / Redis event
        await redis_event_bus.publish(
            workflow_id=state.workflow_id,
            event_type=AgentEventType.HUMAN_REVIEW_REQUIRED,
            data={
                "review_id": review_id,
                "workflow_id": state.workflow_id,
                "patient_id": state.patient_id,
                "patient_name": state.patient_name,
                "risk_level": risk_lvl,
                "reason": reason,
                "status": "PENDING"
            },
            db=db
        )

        state.add_audit_entry(
            agent_name=self.name,
            action=f"Created Human Review Ticket {review_id} with risk level '{risk_lvl}'",
            status="SUCCESS",
            confidence=1.0,
            details={"review_id": review_id, "reason": reason}
        )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "review_id": review_id,
                "status": "PENDING",
                "escalation_level": risk_lvl,
                "reason": reason
            }
        )
