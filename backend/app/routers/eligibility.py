from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.eligibility import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    EligibilityRecommendationRequest,
    EligibilityRecommendationResponse,
    InsuranceEligibilityRequest,
    InsuranceEligibilityResponse,
)
from app.services.eligibility_service import EligibilityService

router = APIRouter(tags=["Eligibility"])

@router.post("/eligibility-check", response_model=EligibilityCheckResponse)
def check_scheme_eligibility(data: EligibilityCheckRequest):
    """Fast eligibility probability check for government healthcare schemes."""
    results = EligibilityService.calculate_scheme_eligibility(data)
    return EligibilityCheckResponse(eligible=results)

@router.post("/eligibility-recommendation", response_model=EligibilityRecommendationResponse)
def get_eligibility_recommendations(
    data: EligibilityRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Deterministic rule-based recommendation system evaluating user criteria against all schemes.
    Returns categorized eligible and ineligible schemes with precise reasons.
    Extensible for future ML model integration.
    """
    return EligibilityService.evaluate_scheme_recommendations(db=db, data=data)

@router.post("/insurance-eligibility", response_model=InsuranceEligibilityResponse)
def check_insurance_eligibility(
    data: InsuranceEligibilityRequest,
    db: Session = Depends(get_db)
):
    """Calculates personalized insurance plan fit and eligibility scores based on age and health profile."""
    results = EligibilityService.calculate_insurance_eligibility(db=db, data=data)
    return InsuranceEligibilityResponse(eligible=results)
