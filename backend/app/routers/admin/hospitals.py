from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import require_super_admin, require_any_admin
from app.models import User, Hospital
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/admin/hospitals", tags=["Admin - Hospitals"])

class HospitalCreateUpdate(BaseModel):
    name: str
    location: Optional[str] = None
    specialization: Optional[str] = None
    rating: Optional[float] = 0.0
    distance: Optional[float] = 0.0
    cost_range: Optional[str] = None
    schemes: Optional[str] = None
    insurance_accepted: Optional[str] = None
    is_available: Optional[bool] = True
    facilities: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

@router.get("")
def list_hospitals(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """List all hospitals for administrative management."""
    query = db.query(Hospital)
    if search:
        s = f"%{search}%"
        query = query.filter((Hospital.name.ilike(s)) | (Hospital.location.ilike(s)) | (Hospital.specialization.ilike(s)))

    # If hospital admin, only show assigned hospital
    if current_admin.role == "HOSPITAL_ADMIN" and current_admin.hospital_id:
        query = query.filter(Hospital.id == current_admin.hospital_id)

    total = query.count()
    hospitals = query.order_by(Hospital.name.asc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": hospitals
    }

@router.post("", status_code=status.HTTP_201_CREATED)
def create_hospital(
    payload: HospitalCreateUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Create a new hospital facility in the platform."""
    hospital = Hospital(**payload.dict())
    db.add(hospital)
    db.commit()
    db.refresh(hospital)

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="HOSPITAL_CREATED",
        resource_type="Hospital",
        resource_id=str(hospital.id),
        new_value={"name": hospital.name, "location": hospital.location}
    )

    return hospital

@router.put("/{hospital_id}")
def update_hospital(
    hospital_id: int,
    payload: HospitalCreateUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """Update hospital details with RBAC scoping."""
    if current_admin.role == "HOSPITAL_ADMIN" and current_admin.hospital_id != hospital_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only manage your assigned hospital.")

    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found.")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(hospital, key, value)

    db.commit()
    db.refresh(hospital)

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="HOSPITAL_UPDATED",
        resource_type="Hospital",
        resource_id=str(hospital.id),
        new_value={"name": hospital.name}
    )

    return hospital

@router.patch("/{hospital_id}/toggle-availability")
def toggle_hospital_availability(
    hospital_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """Toggle bed/clinical availability status."""
    if current_admin.role == "HOSPITAL_ADMIN" and current_admin.hospital_id != hospital_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found.")

    hospital.is_available = not hospital.is_available
    db.commit()

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="HOSPITAL_AVAILABILITY_TOGGLED",
        resource_type="Hospital",
        resource_id=str(hospital.id),
        new_value={"is_available": hospital.is_available}
    )

    return {"message": "Hospital availability updated.", "is_available": hospital.is_available}
