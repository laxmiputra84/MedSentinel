from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class HospitalBase(BaseModel):
    name: str
    location: Optional[str] = None
    specialization: Optional[str] = None
    rating: Optional[float] = 0.0
    distance: Optional[float] = 0.0
    cost_range: Optional[str] = None
    schemes: Optional[str] = None
    insurance_accepted: Optional[str] = None
    is_available: Optional[bool] = True
    image_url: Optional[str] = None
    facilities: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class HospitalResponse(HospitalBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class HospitalPaginatedResponse(BaseModel):
    items: List[HospitalResponse]
    total: int
    page: int
    limit: int
    pages: int

class SavedHospitalCreate(BaseModel):
    hospital_id: int
