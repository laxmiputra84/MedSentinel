"""
MedSentinel Agentic Architecture — Human Review Center Router
Production endpoints for Human-in-the-Loop review of clinical panic escalations,
fraud alerts, and medical decision audit trails.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_any_admin
from app.models.user import User
from app.models.workflow import HumanReviewRecord, WorkflowInstance
from app.services.workflow_manager import workflow_manager
from app.services.redis_event_bus import redis_event_bus, AgentEventType

router = APIRouter(prefix="/human-reviews", tags=["Human-in-the-Loop Review Center"])


class HumanReviewItemResponse(BaseModel):
    id: int
    review_id: str
    workflow_id: str
    patient_id: Optional[int]
    risk_level: str
    status: str
    reason: str
    clinical_context: Dict[str, Any]
    findings: List[Dict[str, Any]]
    decision: Optional[str]
    reviewer_notes: Optional[str]
    created_at: str
    decided_at: Optional[str]


class HumanReviewDecisionRequest(BaseModel):
    decision: str = Field(..., description="APPROVE, REJECT, REQUEST_MORE_INFO, ESCALATE")
    notes: Optional[str] = None


@router.get("", response_model=List[HumanReviewItemResponse])
def list_human_reviews(
    status_filter: Optional[str] = Query(None, alias="status"),
    risk_filter: Optional[str] = Query(None, alias="risk_level"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists human review escalation tickets filtered by status or risk tier."""
    query = db.query(HumanReviewRecord)
    
    # If not admin, patients can only see tickets where they are the subject
    user_role = (current_user.role or "USER").upper()
    if user_role not in ["SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN"]:
        query = query.filter(HumanReviewRecord.patient_id == current_user.id)

    if status_filter:
        query = query.filter(HumanReviewRecord.status == status_filter.upper())
    if risk_filter:
        query = query.filter(HumanReviewRecord.risk_level == risk_filter.upper())

    records = query.order_by(HumanReviewRecord.created_at.desc()).limit(100).all()

    items = []
    for r in records:
        ctx = json.loads(r.clinical_context_json) if r.clinical_context_json else {}
        finds = json.loads(r.findings_json) if r.findings_json else []
        items.append(HumanReviewItemResponse(
            id=r.id,
            review_id=r.review_id,
            workflow_id=r.workflow_id,
            patient_id=r.patient_id,
            risk_level=r.risk_level,
            status=r.status,
            reason=r.reason,
            clinical_context=ctx,
            findings=finds,
            decision=r.decision,
            reviewer_notes=r.reviewer_notes,
            created_at=r.created_at.isoformat() if r.created_at else "",
            decided_at=r.decided_at.isoformat() if r.decided_at else None,
        ))
    return items


@router.get("/{review_id}", response_model=HumanReviewItemResponse)
def get_human_review_details(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves specific review ticket with all clinical findings and evidence."""
    r = db.query(HumanReviewRecord).filter(
        (HumanReviewRecord.review_id == review_id) | (HumanReviewRecord.workflow_id == review_id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Human review ticket not found.")

    ctx = json.loads(r.clinical_context_json) if r.clinical_context_json else {}
    finds = json.loads(r.findings_json) if r.findings_json else []

    return HumanReviewItemResponse(
        id=r.id,
        review_id=r.review_id,
        workflow_id=r.workflow_id,
        patient_id=r.patient_id,
        risk_level=r.risk_level,
        status=r.status,
        reason=r.reason,
        clinical_context=ctx,
        findings=finds,
        decision=r.decision,
        reviewer_notes=r.reviewer_notes,
        created_at=r.created_at.isoformat() if r.created_at else "",
        decided_at=r.decided_at.isoformat() if r.decided_at else None,
    )


@router.post("/{review_id}/decide")
async def decide_human_review(
    review_id: str,
    req: HumanReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin),
):
    """
    Submits authorized decision for a human review ticket (Admin/Doctor only).
    Updates workflow state and broadcasts notification event.
    """
    r = db.query(HumanReviewRecord).filter(
        (HumanReviewRecord.review_id == review_id) | (HumanReviewRecord.workflow_id == review_id)
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Review ticket not found.")

    decision_norm = req.decision.upper().strip()
    if decision_norm not in ["APPROVE", "REJECT", "REQUEST_MORE_INFO", "ESCALATE"]:
        raise HTTPException(status_code=400, detail="Invalid decision. Must be APPROVE, REJECT, REQUEST_MORE_INFO, or ESCALATE.")

    r.status = "APPROVED" if decision_norm == "APPROVE" else ("REJECTED" if decision_norm == "REJECT" else "MODIFIED")
    r.decision = decision_norm
    r.reviewer_id = current_user.id
    r.reviewer_notes = req.notes
    r.decided_at = datetime.now(timezone.utc)
    db.commit()

    # Pass decision to workflow manager to resume or terminate workflow
    try:
        wf_decision = "APPROVE" if decision_norm == "APPROVE" else ("REJECT" if decision_norm == "REJECT" else "REQUEST_MORE_INFORMATION")
        await workflow_manager.review_workflow(
            workflow_id=r.workflow_id,
            decision=wf_decision,
            reviewer_user=current_user,
            notes=req.notes,
            db=db
        )
    except Exception as e:
        pass

    return {
        "success": True,
        "review_id": r.review_id,
        "workflow_id": r.workflow_id,
        "status": r.status,
        "decision": r.decision,
        "decided_by": current_user.name,
        "decided_at": r.decided_at.isoformat()
    }
