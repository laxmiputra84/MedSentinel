from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.hospital import Hospital
from app.schemas.hospital import HospitalResponse, HospitalPaginatedResponse
from app.services.hospital_service import HospitalService

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])

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
    db: Session = Depends(get_db)
):
    """Retrieve list of hospitals with multi-criteria filtering, sorting, and optional pagination."""
    items, total = HospitalService.get_hospitals(
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
        limit=limit
    )

    if page is not None and limit is not None:
        pages = (total + limit - 1) // limit if limit > 0 else 1
        return HospitalPaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=pages
        )

    return items

@router.get("/search", response_model=List[HospitalResponse])
def search_hospitals(
    q: Optional[str] = Query(None, alias="query"),
    db: Session = Depends(get_db)
):
    """Dedicated search endpoint for fast illness & hospital lookups."""
    items, _ = HospitalService.get_hospitals(db=db, search=q)
    return items

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
