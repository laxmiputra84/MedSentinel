from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.dependencies.auth import require_any_admin
from app.models import User, InsuranceClaim, ClaimStatusHistory
from app.services.claim_service import ClaimService
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/admin/claims", tags=["Admin - Claims"])

class AdminClaimStatusUpdate(BaseModel):
    new_status: str # SUBMITTED, UNDER_REVIEW, DOCUMENTS_REQUIRED, APPROVED, REJECTED, COMPLETED
    comment: Optional[str] = None

@router.get("")
def list_claims(
    status: Optional[str] = None,
    hospital_id: Optional[int] = None,
    insurance_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """List and filter insurance claims with administrative scoping."""
    query = db.query(InsuranceClaim).options(
        joinedload(InsuranceClaim.user),
        joinedload(InsuranceClaim.hospital),
        joinedload(InsuranceClaim.insurance)
    )
    if status:
        query = query.filter(InsuranceClaim.claim_status == status)
    if hospital_id:
        query = query.filter(InsuranceClaim.hospital_id == hospital_id)
    if insurance_id:
        query = query.filter(InsuranceClaim.insurance_id == insurance_id)

    # RBAC Scoping
    if current_admin.role == "INSURANCE_ADMIN" and current_admin.insurance_id:
        query = query.filter(InsuranceClaim.insurance_id == current_admin.insurance_id)
    elif current_admin.role == "HOSPITAL_ADMIN" and current_admin.hospital_id:
        query = query.filter(InsuranceClaim.hospital_id == current_admin.hospital_id)

    total = query.count()
    claims = query.order_by(InsuranceClaim.claim_date.desc()).offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "id": c.id,
            "user_id": c.user_id,
            "patient_name": c.user.name if c.user else "Patient",
            "patient_email": c.user.email if c.user else "N/A",
            "hospital_name": c.hospital.name if c.hospital else "N/A",
            "insurance_plan": c.insurance.name if c.insurance else "N/A",
            "claim_amount": c.claim_amount,
            "claim_status": c.claim_status,
            "claim_description": c.claim_description,
            "claim_date": c.claim_date.isoformat() if c.claim_date else None
        }
        for c in claims
    ]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items
    }

@router.get("/{claim_id}")
def get_claim_detail(
    claim_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """Retrieve full claim record, documents, and historical status audit trail."""
    claim = db.query(InsuranceClaim).options(
        joinedload(InsuranceClaim.user),
        joinedload(InsuranceClaim.hospital),
        joinedload(InsuranceClaim.insurance)
    ).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")

    timeline = db.query(ClaimStatusHistory).options(
        joinedload(ClaimStatusHistory.updated_by)
    ).filter(
        ClaimStatusHistory.claim_id == claim.id
    ).order_by(ClaimStatusHistory.created_at.desc()).all()

    timeline_items = [
        {
            "id": h.id,
            "previous_status": h.previous_status,
            "new_status": h.new_status,
            "comment": h.comment,
            "updated_by_name": h.updated_by.name if h.updated_by else "System",
            "created_at": h.created_at.isoformat() if h.created_at else None
        }
        for h in timeline
    ]

    return {
        "id": claim.id,
        "patient": {
            "id": claim.user.id if claim.user else None,
            "name": claim.user.name if claim.user else "N/A",
            "email": claim.user.email if claim.user else "N/A",
            "phone": claim.user.phone if claim.user else "N/A"
        },
        "hospital": {
            "id": claim.hospital.id if claim.hospital else None,
            "name": claim.hospital.name if claim.hospital else "N/A",
            "location": claim.hospital.location if claim.hospital else "N/A"
        },
        "insurance": {
            "id": claim.insurance.id if claim.insurance else None,
            "name": claim.insurance.name if claim.insurance else "N/A"
        },
        "claim_amount": claim.claim_amount,
        "claim_status": claim.claim_status,
        "claim_description": claim.claim_description,
        "claim_date": claim.claim_date.isoformat() if claim.claim_date else None,
        "timeline": timeline_items,
        "timeline_history": timeline_items
    }

@router.patch("/{claim_id}/status")
def update_claim_status(
    claim_id: int,
    payload: AdminClaimStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """Transition claim status with validated workflow and audit logging."""
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")

    old_status = claim.claim_status
    updated_claim = ClaimService.update_claim_status(
        db=db,
        claim_id=claim_id,
        new_status=payload.new_status,
        comment=payload.comment,
        admin_user=current_admin
    )

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="CLAIM_STATUS_UPDATED",
        resource_type="Claim",
        resource_id=str(claim.id),
        old_value={"status": old_status},
        new_value={"status": payload.new_status, "comment": payload.comment}
    )

    return updated_claim
