from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import User, Hospital
from app.services.hospital_service import HospitalService

def search_hospitals_tool(
    db: Session,
    user: User,
    query: Optional[str] = None,
    location: Optional[str] = None,
    specialization: Optional[str] = None,
    insurance: Optional[str] = None,
    scheme: Optional[str] = None,
    min_rating: Optional[float] = None,
    is_available: Optional[bool] = None,
    limit: int = 5
) -> Dict[str, Any]:
    """Search hospitals based on specialized criteria."""
    result = HospitalService.search_hospitals(
        db=db,
        query=query,
        location=location,
        specialization=specialization,
        insurance=insurance,
        scheme=scheme,
        min_rating=min_rating,
        is_available=is_available,
        page=1,
        limit=limit
    )

    hospitals = []
    for h in result["items"]:
        hospitals.append({
            "id": h.id,
            "name": h.name,
            "location": h.location,
            "specialization": h.specialization,
            "rating": h.rating,
            "distance_km": h.distance,
            "cost_range": h.cost_range,
            "accepted_schemes": h.schemes,
            "accepted_insurances": h.insurance_accepted,
            "is_available": h.is_available,
            "facilities": h.facilities,
            "phone": h.phone
        })

    return {
        "total_found": result["total"],
        "hospitals": hospitals,
        "search_parameters": {
            "query": query,
            "location": location,
            "specialization": specialization,
            "insurance": insurance,
            "scheme": scheme,
            "min_rating": min_rating
        }
    }
