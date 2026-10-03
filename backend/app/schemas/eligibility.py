from pydantic import BaseModel
from typing import List, Optional

class EligibilityCheckRequest(BaseModel):
    familySize: Optional[int] = 1
    location: Optional[str] = "urban"
    income: Optional[str] = "low"
    conditions: Optional[List[str]] = None

class SchemeEligibilityItem(BaseModel):
    scheme: str
    probability: int

class EligibilityCheckResponse(BaseModel):
    eligible: List[SchemeEligibilityItem]

class SchemeRecommendationItem(BaseModel):
    scheme_id: int
    scheme_name: str
    coverage: Optional[str] = None
    reason: str
    match_score: int

class IneligibleSchemeItem(BaseModel):
    scheme_id: int
    scheme_name: str
    reason: str

class EligibilityEvaluationRequest(BaseModel):
    age: Optional[int] = 30
    income: Optional[str] = "low" # low, medium, high, bpl
    annual_income: Optional[float] = None
    annual_income_inr: Optional[float] = None
    location: Optional[str] = "urban" # urban, rural
    state: Optional[str] = None
    family_size: Optional[int] = 4
    is_formally_employed: Optional[bool] = False
    has_bpl_card: Optional[bool] = False
    has_critical_illness: Optional[bool] = False

class EligibilityRecommendationRequest(BaseModel):
    age: Optional[int] = 30
    income: Optional[str] = "low" # low, medium, high, bpl
    annual_income_inr: Optional[float] = None
    location: Optional[str] = "urban" # urban, rural
    state: Optional[str] = None
    family_size: Optional[int] = 4
    is_formally_employed: Optional[bool] = False
    has_bpl_card: Optional[bool] = False
    has_critical_illness: Optional[bool] = False

class EligibilityRecommendationResponse(BaseModel):
    eligible: List[SchemeRecommendationItem]
    not_eligible: List[IneligibleSchemeItem]
    evaluation_engine: str = "deterministic_v1"

class InsuranceEligibilityRequest(BaseModel):
    age: int
    income_range: Optional[str] = None
    family_size: Optional[int] = 1
    pre_existing_conditions: Optional[bool] = False

class InsuranceEligibilityItem(BaseModel):
    id: int
    name: str
    provider: str
    eligibility_score: int
    recommended: bool

class InsuranceEligibilityResponse(BaseModel):
    eligible: List[InsuranceEligibilityItem]
