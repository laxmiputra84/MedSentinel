from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class InsuranceBase(BaseModel):
    name: str
    provider: str
    coverage_amount: Optional[float] = 0.0
    premium_monthly: Optional[float] = 0.0
    premium_annual: Optional[float] = 0.0
    coverage_type: Optional[str] = None
    inclusions: Optional[str] = None
    exclusions: Optional[str] = None
    eligibility_age_min: Optional[int] = 18
    eligibility_age_max: Optional[int] = 65
    waiting_period_days: Optional[int] = 30
    cashless_network: Optional[int] = 5000
    claim_settlement_days: Optional[int] = 30
    features: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = 4.5

class InsuranceResponse(InsuranceBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserInsuranceEnrollRequest(BaseModel):
    insurance_id: int
    policy_number: Optional[str] = None
    coverage_start_date: Optional[str] = None
    coverage_end_date: Optional[str] = None
    sum_insured: Optional[float] = None
    dependents: Optional[str] = None

class UserInsuranceResponse(BaseModel):
    id: int
    insurance_id: int
    policy_number: str
    enrollment_date: Optional[datetime] = None
    status: str
    coverage_start_date: Optional[str] = None
    coverage_end_date: Optional[str] = None
    sum_insured: Optional[float] = None
    dependents: Optional[str] = None
    insurance: Optional[InsuranceResponse] = None

    model_config = ConfigDict(from_attributes=True)
