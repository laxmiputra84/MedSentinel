from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.insurance_claim import InsuranceClaim
from app.models.claim_history import ClaimStatusHistory
from app.models.user import User
from app.schemas.claim import (
    InsuranceClaimCreate,
    InsuranceClaimResponse,
    ClaimStatusUpdateRequest,
    ClaimStatusHistoryResponse,
)
from app.dependencies.auth import get_current_user, require_insurance_admin
from app.services.claim_service import ClaimService

router = APIRouter(prefix="/insurance-claims", tags=["Insurance Claims"])

@router.get("", response_model=List[InsuranceClaimResponse])
def get_user_claims(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve insurance claims. Admins see all claims; users see their own."""
    if (current_user.role or "USER").upper() in ["INSURANCE_ADMIN", "SUPER_ADMIN"]:
        return db.query(InsuranceClaim).order_by(InsuranceClaim.claim_date.desc()).all()

    return db.query(InsuranceClaim).filter(
        InsuranceClaim.user_id == current_user.id
    ).order_by(InsuranceClaim.claim_date.desc()).all()

@router.post("", response_model=InsuranceClaimResponse, status_code=status.HTTP_201_CREATED)
def submit_claim(
    claim_in: InsuranceClaimCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a new insurance claim with initial status history and notification."""
    claim = ClaimService.create_claim(
        db=db,
        user_id=current_user.id,
        insurance_id=claim_in.insurance_id,
        hospital_id=claim_in.hospital_id,
        claim_amount=claim_in.claim_amount,
        claim_description=claim_in.claim_description,
        documents=claim_in.documents,
    )
    return claim

@router.get("/{claim_id}", response_model=InsuranceClaimResponse)
def get_claim_by_id(
    claim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get claim by ID with verification of user ownership or admin role."""
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")

    is_owner = claim.user_id == current_user.id
    is_admin = (current_user.role or "USER").upper() in ["INSURANCE_ADMIN", "SUPER_ADMIN"]
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return claim

@router.get("/{claim_id}/timeline", response_model=List[ClaimStatusHistoryResponse])
def get_claim_timeline(
    claim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full status transition audit trail for a claim."""
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")

    is_owner = claim.user_id == current_user.id
    is_admin = (current_user.role or "USER").upper() in ["INSURANCE_ADMIN", "SUPER_ADMIN"]
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return db.query(ClaimStatusHistory).filter(
        ClaimStatusHistory.claim_id == claim_id
    ).order_by(ClaimStatusHistory.created_at.desc()).all()

@router.patch("/{claim_id}/status", response_model=InsuranceClaimResponse)
def update_claim_status(
    claim_id: int,
    status_update: ClaimStatusUpdateRequest,
    current_admin: User = Depends(require_insurance_admin),
    db: Session = Depends(get_db)
):
    """Update claim status (INSURANCE_ADMIN & SUPER_ADMIN only). Logs history and notifies user."""
    return ClaimService.update_claim_status(
        db=db,
        claim_id=claim_id,
        new_status=status_update.new_status,
        admin_user=current_admin,
        comment=status_update.comment
    )
