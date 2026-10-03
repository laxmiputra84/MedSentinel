import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload
from app.core.database import get_db
from app.models.insurance_claim import InsuranceClaim
from app.models.claim_history import ClaimStatusHistory
from app.models.fraud_analysis import FraudAnalysis
from app.models.user import User
from app.schemas.claim import (
    InsuranceClaimCreate,
    InsuranceClaimResponse,
    ClaimStatusUpdateRequest,
    ClaimStatusHistoryResponse,
    FraudAnalysisResponse,
)
from app.dependencies.auth import get_current_user, require_insurance_admin
from app.services.claim_service import ClaimService
from app.services.fraud_detector import FraudDetector
from app.core.events import EventType
from app.services.event_bus import publish_event

router = APIRouter(prefix="/insurance-claims", tags=["Insurance Claims"])

def _claim_eager_options():
    return [
        joinedload(InsuranceClaim.insurance),
        joinedload(InsuranceClaim.hospital),
        joinedload(InsuranceClaim.fraud_analysis),
        selectinload(InsuranceClaim.status_history),
    ]

def _format_claim_response(claim: InsuranceClaim) -> dict:
    fraud_data = None
    if claim.fraud_analysis:
        try:
            flags_list = json.loads(claim.fraud_analysis.flags) if claim.fraud_analysis.flags else []
        except Exception:
            flags_list = [claim.fraud_analysis.flags] if claim.fraud_analysis.flags else []

        fraud_data = FraudAnalysisResponse(
            fraud_score=claim.fraud_analysis.fraud_score,
            fraud_risk=claim.fraud_analysis.fraud_risk,
            flags=flags_list,
            duplicate_docs_detected=claim.fraud_analysis.duplicate_docs_detected,
            duplicate_invoices_detected=claim.fraud_analysis.duplicate_invoices_detected,
            reused_hash_detected=claim.fraud_analysis.reused_hash_detected,
            patient_mismatch_detected=claim.fraud_analysis.patient_mismatch_detected,
        )

    return InsuranceClaimResponse(
        id=claim.id,
        user_id=claim.user_id,
        insurance_id=claim.insurance_id,
        hospital_id=claim.hospital_id,
        claim_amount=claim.claim_amount,
        claim_date=claim.claim_date,
        claim_status=claim.claim_status,
        claim_description=claim.claim_description,
        documents=claim.documents,
        insurance=claim.insurance,
        hospital=claim.hospital,
        status_history=claim.status_history,
        fraud_analysis=fraud_data,
    )

@router.get("", response_model=List[InsuranceClaimResponse])
def get_user_claims(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve insurance claims. Admins see all claims; users see their own."""
    user_role = (current_user.role or "USER").upper()
    query = db.query(InsuranceClaim).options(*_claim_eager_options())

    if user_role in ["INSURANCE_ADMIN", "SUPER_ADMIN"]:
        claims = query.order_by(InsuranceClaim.claim_date.desc()).all()
    else:
        claims = query.filter(
            InsuranceClaim.user_id == current_user.id
        ).order_by(InsuranceClaim.claim_date.desc()).all()

    return [_format_claim_response(c) for c in claims]

@router.post("", response_model=InsuranceClaimResponse, status_code=status.HTTP_201_CREATED)
def submit_claim(
    claim_in: InsuranceClaimCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a new insurance claim with initial status history, fraud analysis, and notification."""
    claim = ClaimService.create_claim(
        db=db,
        user_id=current_user.id,
        insurance_id=claim_in.insurance_id,
        hospital_id=claim_in.hospital_id,
        claim_amount=claim_in.claim_amount,
        claim_description=claim_in.claim_description,
        documents=claim_in.documents,
    )
    # Run automatic fraud analysis with safe error trapping
    try:
        fraud_res = FraudDetector.analyze_claim(db, claim.id)
        if fraud_res.get("fraud_risk") in ["MEDIUM", "HIGH"]:
            publish_event(
                event_type=EventType.FRAUD_FLAG_DETECTED.value,
                entity_id=claim.id,
                user_id=current_user.id,
                payload={"claim_id": claim.id, "fraud_risk": fraud_res.get("fraud_risk")},
                entity_type="claim",
                db=db,
                sync=False,
            )
    except Exception as e:
        print(f"Warning: Automatic fraud analysis error for claim {claim.id}: {e}")

    # Publish CLAIM_CREATED Event
    publish_event(
        event_type=EventType.CLAIM_CREATED.value,
        entity_id=claim.id,
        user_id=current_user.id,
        payload={"claim_amount": claim.claim_amount, "insurance_id": claim.insurance_id, "hospital_id": claim.hospital_id},
        entity_type="claim",
        db=db,
        sync=False,
    )

    # Re-query with eager loading
    reloaded_claim = db.query(InsuranceClaim).options(*_claim_eager_options()).filter(InsuranceClaim.id == claim.id).first()
    return _format_claim_response(reloaded_claim or claim)

@router.get("/{claim_id}", response_model=InsuranceClaimResponse)
def get_claim_by_id(
    claim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get claim by ID with verification of user ownership or admin role."""
    claim = db.query(InsuranceClaim).options(*_claim_eager_options()).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")

    is_owner = claim.user_id == current_user.id
    is_admin = (current_user.role or "USER").upper() in ["INSURANCE_ADMIN", "SUPER_ADMIN"]
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # If fraud analysis hasn't been run yet, run it
    if not claim.fraud_analysis:
        try:
            FraudDetector.analyze_claim(db, claim.id)
            db.refresh(claim)
        except Exception as e:
            print(f"Warning: Fraud check execution note: {e}")

    return _format_claim_response(claim)

@router.get("/{claim_id}/fraud-analysis", response_model=FraudAnalysisResponse)
def get_claim_fraud_analysis(
    claim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    FEATURE 9: Retrieve fraud risk score and diagnostic audit flags for an insurance claim.
    """
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")

    is_owner = claim.user_id == current_user.id
    is_admin = (current_user.role or "USER").upper() in ["INSURANCE_ADMIN", "SUPER_ADMIN"]
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    res = FraudDetector.analyze_claim(db, claim_id)
    return FraudAnalysisResponse(
        fraud_score=res["fraud_score"],
        fraud_risk=res["fraud_risk"],
        flags=res["flags"],
        duplicate_docs_detected=res.get("duplicate_docs_detected", False),
        duplicate_invoices_detected=res.get("duplicate_invoices_detected", False),
        reused_hash_detected=res.get("reused_hash_detected", False),
        patient_mismatch_detected=res.get("patient_mismatch_detected", False),
    )

@router.post("/{claim_id}/run-fraud-check", response_model=FraudAnalysisResponse)
def trigger_claim_fraud_check(
    claim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    FEATURE 9: Trigger on-demand deep fraud check for an insurance claim.
    """
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")

    res = FraudDetector.analyze_claim(db, claim_id)
    return FraudAnalysisResponse(
        fraud_score=res["fraud_score"],
        fraud_risk=res["fraud_risk"],
        flags=res["flags"],
        duplicate_docs_detected=res.get("duplicate_docs_detected", False),
        duplicate_invoices_detected=res.get("duplicate_invoices_detected", False),
        reused_hash_detected=res.get("reused_hash_detected", False),
        patient_mismatch_detected=res.get("patient_mismatch_detected", False),
    )

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
    updated = ClaimService.update_claim_status(
        db=db,
        claim_id=claim_id,
        new_status=status_update.new_status,
        admin_user=current_admin,
        comment=status_update.comment
    )

    publish_event(
        event_type=EventType.CLAIM_UPDATED.value,
        entity_id=claim_id,
        user_id=current_admin.id,
        payload={"new_status": status_update.new_status, "comment": status_update.comment},
        entity_type="claim",
        db=db,
        sync=False,
    )

    return _format_claim_response(updated)
