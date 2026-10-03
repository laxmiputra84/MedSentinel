"""
MedSentinel Agentic Architecture — Agent Workflow Router
Exposes production-ready REST endpoints and real-time Server-Sent Events (SSE)
for launching, monitoring, streaming, and reviewing agentic healthcare workflows.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security import decode_token, normalize_role
from app.dependencies.auth import get_current_user, require_any_admin, get_optional_current_user
from app.models.user import User
from app.models.patient import Patient
from app.agents.state import (
    WorkflowState,
    WorkflowType,
    WorkflowStatus,
    EscalationLevel,
)
from app.services.workflow_manager import workflow_manager

router = APIRouter(prefix="/agent-workflow", tags=["Agentic Workflow"])


# ==========================================
# Pydantic Request & Response Schemas
# ==========================================

class StartWorkflowRequest(BaseModel):
    patient_id: Optional[int] = None
    document_id: Optional[int] = None
    file_path: Optional[str] = None
    filename: Optional[str] = None
    extracted_text: Optional[str] = None
    workflow_type: Optional[WorkflowType] = WorkflowType.AUTOMATIC
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class StartWorkflowResponse(BaseModel):
    workflow_id: str
    status: str = "STARTED"
    message: str = "Agent workflow started"


class ReviewWorkflowRequest(BaseModel):
    decision: str = Field(..., description="APPROVE, REJECT, or REQUEST_MORE_INFORMATION")
    notes: Optional[str] = None


class WorkflowHistoryItem(BaseModel):
    workflow_id: str
    patient_id: Optional[int]
    patient_name: Optional[str]
    document_id: Optional[int]
    document_type: Optional[str]
    workflow_type: str
    status: str
    escalation_required: bool
    risk_level: Optional[str] = None
    created_at: str
    updated_at: str
    has_final_report: bool


# ==========================================
# Helpers
# ==========================================

def _verify_patient_access(db: Session, current_user: User, patient_id: Optional[int]) -> None:
    """Ensures a standard user can only access their own patient records."""
    if not patient_id:
        return
    user_role = (current_user.role or "USER").upper()
    if user_role in ["SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN"]:
        return

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to access this patient's records."
        )


def _authenticate_sse_token(token: Optional[str], db: Session) -> Optional[User]:
    """Helper to authenticate token from query parameter or bearer for EventSource SSE."""
    if not token:
        return None
    try:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if user_id:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if user and user.is_active:
                if user.role:
                    user.role = normalize_role(user.role)
                return user
    except Exception:
        pass
    return None


# ==========================================
# Endpoints
# ==========================================

@router.post("/run", response_model=StartWorkflowResponse, status_code=status.HTTP_201_CREATED)
async def start_agent_workflow(
    req: StartWorkflowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start an agentic healthcare decision-support workflow in the background.
    Determines required specialized agents dynamically using Orchestrator.
    """
    _verify_patient_access(db, current_user, req.patient_id)

    # Auto-resolve patient ID if not provided
    resolved_patient_id = req.patient_id
    if not resolved_patient_id:
        p = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if p:
            resolved_patient_id = p.id

    workflow_id = workflow_manager.generate_workflow_id()

    state = WorkflowState(
        workflow_id=workflow_id,
        user_id=current_user.id,
        user_role=current_user.role or "USER",
        patient_id=resolved_patient_id,
        hospital_id=current_user.hospital_id,
        document_id=req.document_id,
        file_path=req.file_path,
        filename=req.filename,
        extracted_text=req.extracted_text,
        workflow_type=req.workflow_type or WorkflowType.AUTOMATIC,
        status=WorkflowStatus.PENDING,
    )

    # Launch background async execution
    workflow_manager.start_background_workflow(
        state=state,
        context=req.context,
        db_session_factory=SessionLocal
    )

    return StartWorkflowResponse(
        workflow_id=workflow_id,
        status="STARTED",
        message="Agent workflow started"
    )


@router.get("/{workflow_id}", response_model=Dict[str, Any])
def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve current structured execution state, findings, and final report for a workflow.
    """
    state = workflow_manager.get_workflow(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' was not found."
        )

    # Access control verification
    user_role = (current_user.role or "USER").upper()
    if user_role not in ["SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN"]:
        if state.user_id and state.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot view workflows belonging to other users."
            )

    return state.model_dump()


@router.get("/{workflow_id}/stream")
async def stream_workflow_events(
    workflow_id: str,
    request: Request,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Server-Sent Events (SSE) stream broadcasting live step-by-step agent telemetry,
    execution state transitions, findings, and human review requests.
    """
    state = workflow_manager.get_workflow(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' was not found."
        )

    # Optional auth validation for stream connection
    auth_user = _authenticate_sse_token(token, db)
    if auth_user:
        user_role = (auth_user.role or "USER").upper()
        if user_role not in ["SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN"]:
            if state.user_id and state.user_id != auth_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to stream."
                )

    return StreamingResponse(
        workflow_manager.subscribe(workflow_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/{workflow_id}/review", response_model=Dict[str, Any])
async def review_workflow(
    workflow_id: str,
    req: ReviewWorkflowRequest,
    current_admin: User = Depends(require_any_admin),
    db: Session = Depends(get_db)
):
    """
    Human-in-the-Loop review endpoint allowing licensed doctors / admins
    to approve, modify, or reject an escalated critical workflow.
    """
    state = workflow_manager.get_workflow(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' was not found."
        )

    try:
        updated_state = await workflow_manager.review_workflow(
            workflow_id=workflow_id,
            decision=req.decision,
            reviewer_user=current_admin,
            notes=req.notes
        )
        return {
            "workflow_id": workflow_id,
            "decision": req.decision.upper(),
            "status": updated_state.status.value,
            "reviewer_name": current_admin.name,
            "message": f"Workflow successfully {req.decision.lower()}ed by reviewer."
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/patient/{patient_id}/history", response_model=List[WorkflowHistoryItem])
def get_patient_workflow_history(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve historical agent workflows executed for a given patient.
    """
    _verify_patient_access(db, current_user, patient_id)

    workflows = workflow_manager.list_workflows_for_patient(patient_id)
    results = []

    for w in sorted(workflows, key=lambda x: x.created_at, reverse=True):
        risk_lvl = None
        if w.risk_result:
            risk_lvl = w.risk_result.get("risk_level")

        results.append(
            WorkflowHistoryItem(
                workflow_id=w.workflow_id,
                patient_id=w.patient_id,
                patient_name=w.patient_name,
                document_id=w.document_id,
                document_type=w.document_type,
                workflow_type=w.workflow_type.value,
                status=w.status.value,
                escalation_required=w.escalation_required,
                risk_level=risk_lvl,
                created_at=w.created_at.isoformat(),
                updated_at=w.updated_at.isoformat(),
                has_final_report=w.final_report is not None,
            )
        )

    return results
