"""
MedSentinel Agentic Architecture — Patient 360 & Longitudinal Timeline Router
Provides unified clinical intelligence view: 360 overview, chronological timeline,
and longitudinal lab trajectories with biological reference ranges.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.patient import Patient
from app.models.lab_result import LabResult
from app.models.document import UserDocument
from app.models.appointment import Appointment
from app.models.insurance_claim import InsuranceClaim
from app.models.health_score import HealthScore
from app.models.workflow import WorkflowInstance, HumanReviewRecord

router = APIRouter(prefix="/patients", tags=["Patient 360 Intelligence & Timeline"])


def _check_patient_access(patient: Patient, user: User):
    """Enforces patient isolation: users can only see their own records, admins can see all."""
    user_role = (user.role or "USER").upper()
    if user_role not in ["SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN"]:
        if patient.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot access other patient records.")


@router.get("/{patient_id}/360")
def get_patient_360_view(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves comprehensive Patient 360 Intelligence summary."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    _check_patient_access(patient, current_user)

    # 1. Latest Health Score
    latest_score = db.query(HealthScore).filter(HealthScore.patient_id == patient_id).order_by(HealthScore.calculated_at.desc()).first()

    # 2. Lab Results Summary
    labs = db.query(LabResult).filter(LabResult.patient_id == patient_id).order_by(LabResult.test_date.desc()).limit(20).all()
    lab_summary = [{
        "id": l.id,
        "name": l.test_name,
        "value": l.observed_value,
        "unit": l.unit,
        "status": l.status,
        "is_critical": l.is_critical,
        "date": l.test_date.isoformat() if l.test_date else None
    } for l in labs]

    # 3. Documents Vault
    docs = db.query(UserDocument).filter(UserDocument.patient_id == patient_id).order_by(UserDocument.upload_date.desc()).limit(10).all()
    doc_summary = [{
        "id": d.id,
        "code": d.document_code,
        "type": d.doc_type,
        "name": d.original_name,
        "status": d.verification_status,
        "date": d.upload_date.isoformat() if d.upload_date else None
    } for d in docs]

    # 4. Claims
    claims = db.query(InsuranceClaim).filter(InsuranceClaim.patient_id == patient_id).order_by(InsuranceClaim.claim_date.desc()).limit(10).all()
    claim_summary = [{
        "id": c.id,
        "claim_number": f"CLM-{c.id:06d}",
        "amount": c.claim_amount,
        "status": c.claim_status,
        "date": c.claim_date.isoformat() if c.claim_date else None
    } for c in claims]

    # 5. Workflows & Pending Reviews
    wfs = db.query(WorkflowInstance).filter(WorkflowInstance.patient_id == patient_id).order_by(WorkflowInstance.created_at.desc()).limit(10).all()
    wf_summary = [{
        "workflow_id": w.workflow_id,
        "type": w.workflow_type,
        "status": w.status,
        "escalation_required": w.escalation_required,
        "date": w.created_at.isoformat() if w.created_at else None
    } for w in wfs]

    return {
        "patient": {
            "id": patient.id,
            "patient_code": patient.patient_code,
            "name": patient.name,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "emergency_contact": patient.emergency_contact,
        },
        "health_score": {
            "score": latest_score.health_score if latest_score else 85,
            "risk_score": latest_score.risk_score if latest_score else 15,
            "risk_level": latest_score.risk_level if latest_score else "LOW",
            "summary": latest_score.ai_summary if latest_score else "No critical anomalies recorded.",
        },
        "recent_labs": lab_summary,
        "recent_documents": doc_summary,
        "recent_claims": claim_summary,
        "recent_workflows": wf_summary,
    }


@router.get("/{patient_id}/timeline")
def get_patient_timeline(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves unified chronological clinical timeline across all modalities."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    _check_patient_access(patient, current_user)

    events = []

    # 1. Appointments
    if patient.user_id:
        appts = db.query(Appointment).filter(Appointment.user_id == patient.user_id).all()
        for a in appts:
            if a.preferred_date:
                events.append({
                    "type": "APPOINTMENT",
                    "title": f"Appointment: {a.department or 'General Consultation'}",
                    "description": f"Status: {a.status} with Hospital ID #{a.hospital_id}",
                    "date": a.preferred_date if isinstance(a.preferred_date, str) else str(a.preferred_date),
                    "badge": a.status,
                })

    # 2. Lab Results
    labs = db.query(LabResult).filter(LabResult.patient_id == patient_id).all()
    for l in labs:
        if l.test_date:
            events.append({
                "type": "LAB_REPORT",
                "title": f"Lab Test: {l.test_name} ({l.observed_value} {l.unit or ''})",
                "description": f"Status: {l.status} | Critical: {l.is_critical}",
                "date": l.test_date.isoformat() if hasattr(l.test_date, "isoformat") else str(l.test_date),
                "badge": "CRITICAL" if l.is_critical else l.status,
            })

    # 3. Documents
    docs = db.query(UserDocument).filter(UserDocument.patient_id == patient_id).all()
    for d in docs:
        if d.upload_date:
            events.append({
                "type": "DOCUMENT",
                "title": f"Document: {d.doc_type or 'Medical Record'}",
                "description": f"File: {d.original_name} (Code: {d.document_code})",
                "date": d.upload_date.isoformat() if hasattr(d.upload_date, "isoformat") else str(d.upload_date),
                "badge": d.verification_status,
            })

    # 4. Claims
    claims = db.query(InsuranceClaim).filter(InsuranceClaim.patient_id == patient_id).all()
    for c in claims:
        if c.claim_date:
            events.append({
                "type": "CLAIM",
                "title": f"Claim #CLM-{c.id:06d}",
                "description": f"Amount: ₹{c.claim_amount:,.2f} | Status: {c.claim_status}",
                "date": c.claim_date.isoformat() if hasattr(c.claim_date, "isoformat") else str(c.claim_date),
                "badge": c.claim_status,
            })

    # Sort descending by date
    events.sort(key=lambda x: x["date"], reverse=True)

    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "total_timeline_events": len(events),
        "events": events
    }


@router.get("/{patient_id}/labs/trends")
def get_patient_lab_trends(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves longitudinal test trajectories grouped by parameter name."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    _check_patient_access(patient, current_user)

    results = db.query(LabResult).filter(
        LabResult.patient_id == patient_id
    ).order_by(LabResult.test_date.asc()).all()

    trends: Dict[str, Dict[str, Any]] = {}
    for r in results:
        tname = r.test_name
        if tname not in trends:
            trends[tname] = {
                "test_name": tname,
                "unit": r.unit,
                "reference_min": r.reference_min,
                "reference_max": r.reference_max,
                "history": []
            }
        trends[tname]["history"].append({
            "date": r.test_date.isoformat() if r.test_date else None,
            "value": r.observed_value,
            "status": r.status,
            "is_critical": r.is_critical
        })

    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "parameters_tracked": len(trends),
        "trends": list(trends.values())
    }
