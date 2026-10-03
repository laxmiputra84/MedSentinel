from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.hospital import Hospital
from app.schemas.hospital import (
    HospitalResponse,
    HospitalPaginatedResponse,
    HospitalSearchResponse,
    SearchIntentMeta,
    PatientHospitalRecommendationRequest,
    PatientHospitalRecommendationResponse,
)
from app.services.hospital_service import HospitalService
from app.services.patient_condition_service import PatientConditionService

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])

@router.get("/intent", response_model=SearchIntentMeta)
def analyze_search_intent(query: Optional[str] = Query(None, description="Query string to parse for search intent")):
    """Analyze query and return detected intent, location, specialty, and strategy."""
    intent_data = HospitalService.detect_search_intent(query)
    return SearchIntentMeta(**intent_data)

@router.post("/recommendations/patient-condition", response_model=PatientHospitalRecommendationResponse)
def recommend_hospitals_by_patient_condition(
    req: PatientHospitalRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Recommends verified hospitals driven strictly by patient clinical data & biomarkers.
    Analyzes evidence, determines indicated specializations, and ranks real matching hospitals by distance/rating.
    """
    extracted_text = req.extracted_text
    lab_results = req.lab_results
    clinical_notes = req.clinical_notes

    # If workflow_id provided, fetch state from workflow_manager
    if req.workflow_id:
        from app.services.workflow_manager import workflow_manager
        state = workflow_manager.get_workflow(req.workflow_id)
        if state:
            extracted_text = extracted_text or state.extracted_text
            lab_results = lab_results or state.lab_results

    # If patient_id provided and no explicit text/labs, pull latest lab results & documents from DB
    if req.patient_id and not lab_results and not extracted_text:
        from app.models.lab_result import LabResult
        from app.models.document import UserDocument

        db_labs = db.query(LabResult).filter(
            LabResult.patient_id == req.patient_id
        ).order_by(LabResult.recorded_date.desc()).limit(20).all()
        if db_labs:
            lab_results = [
                {
                    "name": l.test_name,
                    "value": l.value,
                    "unit": l.unit,
                    "status": l.status,
                    "reference_min": l.reference_min,
                    "reference_max": l.reference_max,
                }
                for l in db_labs
            ]

        latest_doc = db.query(UserDocument).filter(
            UserDocument.patient_id == req.patient_id
        ).order_by(UserDocument.id.desc()).first()
        if latest_doc and latest_doc.ocr_extracted_text:
            extracted_text = (extracted_text or "") + " " + latest_doc.ocr_extracted_text

    # Run evidence extraction
    analysis_res = PatientConditionService.extract_patient_condition_evidence(
        extracted_text=extracted_text,
        lab_results=lab_results,
        clinical_notes=clinical_notes,
        extracted_data=req.extracted_data,
    )

    # Match and rank hospitals
    match_data = HospitalService.recommend_hospitals_for_patient_condition(
        db=db,
        condition_analysis=analysis_res,
        latitude=req.latitude,
        longitude=req.longitude,
        location=req.location,
        radius_km=req.radius_km,
        is_available=req.is_available,
        min_rating=req.min_rating,
        limit=req.limit,
    )

    return PatientHospitalRecommendationResponse(**match_data)

@router.get("/recommendations/workflow/{workflow_id}", response_model=PatientHospitalRecommendationResponse)
def get_workflow_hospital_recommendations(
    workflow_id: str,
    latitude: Optional[float] = Query(None, description="Patient latitude for GPS distance"),
    longitude: Optional[float] = Query(None, description="Patient longitude for GPS distance"),
    radius_km: Optional[float] = Query(None, description="Filter radius in kilometers"),
    location: Optional[str] = Query(None, description="City or area filter"),
    is_available: Optional[bool] = Query(None, description="Filter only available hospitals"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Returns hospital recommendations directly derived from a completed or in-progress
    Agentic Workflow's extracted findings.
    """
    from app.services.workflow_manager import workflow_manager
    state = workflow_manager.get_workflow(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' not found."
        )

    analysis_res = PatientConditionService.extract_patient_condition_evidence(
        extracted_text=state.extracted_text,
        lab_results=state.lab_results,
        clinical_findings=state.clinical_findings,
    )

    match_data = HospitalService.recommend_hospitals_for_patient_condition(
        db=db,
        condition_analysis=analysis_res,
        latitude=latitude,
        longitude=longitude,
        location=location,
        radius_km=radius_km,
        is_available=is_available,
        limit=limit,
    )

    return PatientHospitalRecommendationResponse(**match_data)

@router.get("", response_model=Union[List[HospitalResponse], HospitalPaginatedResponse])
def list_hospitals(
    search: Optional[str] = Query(None, description="Search by name, illness, location, facilities, or scheme"),
    location: Optional[str] = Query(None, description="Filter by city or state"),
    specialization: Optional[str] = Query(None, description="Filter by medical specialization"),
    insurance_accepted: Optional[str] = Query(None, description="Filter by insurance accepted"),
    maxDistance: Optional[float] = Query(None, description="Maximum distance in km"),
    minRating: Optional[float] = Query(None, description="Minimum star rating"),
    scheme: Optional[str] = Query(None, description="Filter by supported government scheme"),
    is_available: Optional[bool] = Query(None, description="Filter by doctor/bed availability"),
    sort_by: Optional[str] = Query(None, description="Sort by rating, distance, or name"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    page: Optional[int] = Query(None, ge=1, description="Page number for pagination"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    latitude: Optional[float] = Query(None, description="User latitude for Haversine distance calculation"),
    longitude: Optional[float] = Query(None, description="User longitude for Haversine distance calculation"),
    radius: Optional[float] = Query(None, description="Radius in km for nearby distance search"),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """Retrieve list of hospitals with multi-criteria filtering, intent analysis, sorting, and optional GPS distance calculation."""
    items, total, intent = HospitalService.get_hospitals(
        db=db,
        search=search,
        location=location,
        specialization=specialization,
        insurance_accepted=insurance_accepted,
        max_distance=maxDistance,
        min_rating=minRating,
        scheme=scheme,
        is_available=is_available,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit,
        latitude=latitude,
        longitude=longitude,
        radius=radius,
    )

    if response is not None:
        response.headers["X-Search-Type"] = intent["search_type"]
        response.headers["X-Nearby-Intent"] = str(intent["is_nearby_search"]).lower()
        response.headers["X-Has-Coordinates"] = str(intent["has_coordinates"]).lower()
        if intent.get("detected_location"):
            response.headers["X-Detected-Location"] = intent["detected_location"]
        if intent.get("detected_specialty"):
            response.headers["X-Detected-Specialty"] = intent["detected_specialty"]

    if page is not None and limit is not None:
        pages = (total + limit - 1) // limit if limit > 0 else 1
        return HospitalPaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            intent=SearchIntentMeta(**intent)
        )

    return items

@router.get("/search", response_model=Union[HospitalSearchResponse, List[HospitalResponse]])
def search_hospitals(
    q: Optional[str] = Query(None, alias="query"),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    radius: Optional[float] = Query(None),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """Dedicated search endpoint for illness & hospital lookups with intent detection."""
    result = HospitalService.search_hospitals(
        db=db,
        query=q,
        latitude=latitude,
        longitude=longitude,
        radius=radius,
    )

    if response is not None:
        intent = result["intent"]
        response.headers["X-Search-Type"] = intent["search_type"]
        response.headers["X-Nearby-Intent"] = str(intent["is_nearby_search"]).lower()
        response.headers["X-Has-Coordinates"] = str(intent["has_coordinates"]).lower()
        if intent.get("detected_location"):
            response.headers["X-Detected-Location"] = intent["detected_location"]
        if intent.get("detected_specialty"):
            response.headers["X-Detected-Specialty"] = intent["detected_specialty"]

    return HospitalSearchResponse(
        items=result["items"],
        total=result["total"],
        intent=SearchIntentMeta(**result["intent"])
    )

@router.get("/{hospital_id}", response_model=HospitalResponse)
def get_hospital_by_id(hospital_id: int, db: Session = Depends(get_db)):
    """Retrieve single hospital by its ID."""
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found"
        )
    return hospital
