from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.insurance import InsuranceResponse
from app.schemas.hospital import HospitalResponse

class ClaimStatusHistoryResponse(BaseModel):
    id: int
    claim_id: int
    previous_status: Optional[str] = None
    new_status: str
    updated_by_id: Optional[int] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class InsuranceClaimCreate(BaseModel):
    insurance_id: Optional[int] = None
    hospital_id: Optional[int] = None
    claim_amount: float
    claim_description: Optional[str] = None
    documents: Optional[str] = None

class ClaimStatusUpdateRequest(BaseModel):
    new_status: str # SUBMITTED, UNDER_REVIEW, DOCUMENTS_REQUIRED, APPROVED, REJECTED, COMPLETED
    comment: Optional[str] = None

class InsuranceClaimResponse(BaseModel):
    id: int
    user_id: int
    insurance_id: Optional[int] = None
    hospital_id: Optional[int] = None
    claim_amount: float
    claim_date: Optional[datetime] = None
    claim_status: str
    claim_description: Optional[str] = None
    documents: Optional[str] = None
    insurance: Optional[InsuranceResponse] = None
    hospital: Optional[HospitalResponse] = None
    status_history: Optional[List[ClaimStatusHistoryResponse]] = []

    model_config = ConfigDict(from_attributes=True)
