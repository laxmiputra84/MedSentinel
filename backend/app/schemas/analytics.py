from pydantic import BaseModel
from typing import Dict, Any, List

class PlatformAnalyticsResponse(BaseModel):
    total_users: int
    total_hospitals: int
    total_appointments: int
    total_insurance_policies: int
    total_claims: int
    approved_claims: int
    rejected_claims: int
    under_review_claims: int
    total_claims_amount: float
    recent_users_count: int

class HospitalAnalyticsResponse(BaseModel):
    hospital_id: int
    hospital_name: str
    today_appointments: int
    upcoming_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    department_distribution: Dict[str, int]

class InsuranceAnalyticsResponse(BaseModel):
    total_plans: int
    total_active_enrolled_policies: int
    total_claims: int
    claims_under_review: int
    approved_claims: int
    rejected_claims: int
    documents_required_claims: int
    total_payout_amount: float
