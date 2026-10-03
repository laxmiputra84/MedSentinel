import random
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.insurance import Insurance
from app.models.user_insurance import UserInsurance
from app.schemas.insurance import (
    InsuranceResponse,
    UserInsuranceEnrollRequest,
    UserInsuranceResponse,
)
from app.schemas.auth import MessageResponse

router = APIRouter(tags=["Insurance"])

@router.get("/insurances", response_model=List[InsuranceResponse])
def list_insurances(
    search: Optional[str] = Query(None, description="Search by name, provider, features, or inclusions"),
    coverage_type: Optional[str] = Query(None, description="Filter by coverage type (e.g. Comprehensive, Family Floater)"),
    maxPremium: Optional[float] = Query(None, description="Maximum monthly premium"),
    minRating: Optional[float] = Query(None, description="Minimum star rating"),
    provider: Optional[str] = Query(None, description="Filter by insurance company/provider"),
    db: Session = Depends(get_db)
):
    """Retrieve insurance policies matching search and filter criteria."""
    query = db.query(Insurance)

    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Insurance.name.ilike(s),
                Insurance.provider.ilike(s),
                Insurance.features.ilike(s),
                Insurance.inclusions.ilike(s),
            )
        )

    if coverage_type:
        query = query.filter(Insurance.coverage_type.ilike(f"%{coverage_type}%"))

    if maxPremium is not None:
        query = query.filter(Insurance.premium_monthly <= maxPremium)

    if minRating is not None:
        query = query.filter(Insurance.rating >= minRating)

    if provider:
        query = query.filter(Insurance.provider.ilike(f"%{provider}%"))

    return query.all()

@router.get("/insurances/{insurance_id}", response_model=InsuranceResponse)
def get_insurance_by_id(insurance_id: int, db: Session = Depends(get_db)):
    """Retrieve details for a specific insurance policy."""
    insurance = db.query(Insurance).filter(Insurance.id == insurance_id).first()
    if not insurance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance plan not found"
        )
    return insurance

@router.get("/user-insurances", response_model=List[UserInsuranceResponse])
def get_user_enrolled_insurances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all insurance plans enrolled by the authenticated user."""
    user_insurances = db.query(UserInsurance).filter(UserInsurance.user_id == current_user.id).all()
    return user_insurances

@router.post("/user-insurances", response_model=UserInsuranceResponse, status_code=status.HTTP_201_CREATED)
def enroll_user_insurance(
    data: UserInsuranceEnrollRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enroll the authenticated user into an insurance policy."""
    insurance = db.query(Insurance).filter(Insurance.id == data.insurance_id).first()
    if not insurance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insurance plan not found"
        )

    policy_no = data.policy_number or f"POL-{random.randint(100000, 999999)}-{current_user.id}"
    start_date = data.coverage_start_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    end_date = data.coverage_end_date or (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d")
    sum_insured_val = data.sum_insured or insurance.coverage_amount

    new_enrollment = UserInsurance(
        user_id=current_user.id,
        insurance_id=data.insurance_id,
        policy_number=policy_no,
        coverage_start_date=start_date,
        coverage_end_date=end_date,
        sum_insured=sum_insured_val,
        dependents=data.dependents,
        status="active"
    )
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment

@router.delete("/user-insurances/{user_insurance_id}", response_model=MessageResponse)
def cancel_user_insurance(
    user_insurance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel or remove an enrolled user policy."""
    record = db.query(UserInsurance).filter(
        UserInsurance.id == user_insurance_id,
        UserInsurance.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrolled insurance record not found"
        )

    db.delete(record)
    db.commit()
    return MessageResponse(message="Insurance policy enrollment cancelled successfully")
