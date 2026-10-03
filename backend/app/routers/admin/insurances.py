from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.dependencies.auth import require_any_admin, require_super_admin
from app.models import User, Insurance, InsuranceClaim
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/admin/insurances", tags=["Admin - Insurances"])

class InsuranceCreateUpdate(BaseModel):
    name: str
    provider: str
    coverage_amount: float
    premium_monthly: float
    premium_annual: float
    cashless_network: Optional[int] = 0
    claim_settlement_days: Optional[int] = 3
    rating: Optional[float] = 0.0
    features: Optional[str] = None
    inclusions: Optional[str] = None
    exclusions: Optional[str] = None
    coverage_type: Optional[str] = "Comprehensive"
    waiting_period_days: Optional[int] = 30
    eligibility_age_min: Optional[int] = 18
    eligibility_age_max: Optional[int] = 65

@router.get("")
def list_insurances(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """List all insurance policies and active claim statistics."""
    query = db.query(Insurance)
    if current_admin.role == "INSURANCE_ADMIN" and current_admin.insurance_id:
        query = query.filter(Insurance.id == current_admin.insurance_id)

    plans = query.all()

    # Aggregate claim counts in a single group-by query
    claim_counts = dict(
        db.query(InsuranceClaim.insurance_id, func.count(InsuranceClaim.id))
        .group_by(InsuranceClaim.insurance_id)
        .all()
    )

    items = []
    for p in plans:
        total_claims = claim_counts.get(p.id, 0)
        items.append({
            "id": p.id,
            "name": p.name,
            "provider": p.provider,
            "coverage_amount": p.coverage_amount,
            "premium_monthly": p.premium_monthly,
            "premium_annual": p.premium_annual,
            "cashless_network": p.cashless_network,
            "rating": p.rating,
            "coverage_type": p.coverage_type,
            "total_claims": total_claims
        })

    return items

@router.post("", status_code=status.HTTP_201_CREATED)
def create_insurance(
    payload: InsuranceCreateUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Create a new insurance policy tier."""
    ins = Insurance(**payload.dict())
    db.add(ins)
    db.commit()
    db.refresh(ins)

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="INSURANCE_CREATED",
        resource_type="Insurance",
        resource_id=str(ins.id),
        new_value={"name": ins.name, "provider": ins.provider}
    )

    return ins

@router.put("/{insurance_id}")
def update_insurance(
    insurance_id: int,
    payload: InsuranceCreateUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """Update insurance policy details."""
    if current_admin.role == "INSURANCE_ADMIN" and current_admin.insurance_id != insurance_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    ins = db.query(Insurance).filter(Insurance.id == insurance_id).first()
    if not ins:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance not found.")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(ins, key, value)

    db.commit()
    db.refresh(ins)

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="INSURANCE_UPDATED",
        resource_type="Insurance",
        resource_id=str(ins.id),
        new_value={"name": ins.name}
    )

    return ins
