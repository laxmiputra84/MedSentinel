from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any

class SearchIntentMeta(BaseModel):
    search_query: Optional[str] = None
    search_type: str = "keyword" # "keyword", "location", "specialty", "specialty_location", "nearby"
    is_nearby_search: bool = False
    detected_location: Optional[str] = None
    detected_specialty: Optional[str] = None
    detected_keyword: Optional[str] = None
    detected_facilities: List[str] = []
    requires_availability: bool = False
    has_coordinates: bool = False

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
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class HospitalResponse(HospitalBase):
    id: int
    distance_km: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class HospitalPaginatedResponse(BaseModel):
    items: List[HospitalResponse]
    total: int
    page: int
    limit: int
    pages: int
    intent: Optional[SearchIntentMeta] = None

class HospitalSearchResponse(BaseModel):
    items: List[HospitalResponse]
    total: int
    intent: SearchIntentMeta

class SavedHospitalCreate(BaseModel):
    hospital_id: int

class DetectedConditionSchema(BaseModel):
    condition_name: str
    category: str
    supporting_evidence: List[str]
    confidence: float = 0.85
    risk_level: str = "MODERATE"
    source_data: str = "Laboratory Biomarkers"
    recommended_specialties: List[str]
    requires_icu: bool = False

class HospitalMatchItem(HospitalResponse):
    icu_status: str = "Unknown" # "Available", "Occupied / Unavailable", "Unknown / Not Listed"
    is_verified: bool = True
    match_reasons: List[str] = []

class PatientHospitalRecommendationRequest(BaseModel):
    workflow_id: Optional[str] = None
    patient_id: Optional[int] = None
    extracted_data: Optional[Dict[str, Any]] = None
    extracted_text: Optional[str] = None
    clinical_notes: Optional[str] = None
    lab_results: Optional[List[Dict[str, Any]]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    radius_km: Optional[float] = None
    is_available: Optional[bool] = None
    min_rating: Optional[float] = None
    limit: int = 10

class PatientHospitalRecommendationResponse(BaseModel):
    has_sufficient_evidence: bool
    patient_condition: Optional[DetectedConditionSchema] = None
    all_conditions: List[DetectedConditionSchema] = []
    recommended_specialties: List[str] = []
    requires_icu_or_critical_care: bool = False
    clinical_summary: str
    hospitals: List[HospitalMatchItem]
    total_found: int
    applied_filters: Dict[str, Any]
