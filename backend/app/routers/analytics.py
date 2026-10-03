from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    PlatformAnalyticsResponse,
    HospitalAnalyticsResponse,
    InsuranceAnalyticsResponse,
)
from app.dependencies.auth import (
    require_super_admin,
    require_hospital_admin,
    require_insurance_admin,
    get_current_user,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/platform", response_model=PlatformAnalyticsResponse)
def get_platform_analytics(
    current_admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Retrieve platform-wide operational and financial analytics (SUPER_ADMIN only)."""
    return AnalyticsService.get_platform_analytics(db=db)

@router.get("/hospital", response_model=HospitalAnalyticsResponse)
def get_hospital_analytics(
    hospital_id: int = Query(1, description="Target hospital ID"),
    current_admin: User = Depends(require_hospital_admin),
    db: Session = Depends(get_db)
):
    """Retrieve hospital appointment and department metrics (HOSPITAL_ADMIN & SUPER_ADMIN)."""
    target_id = current_admin.hospital_id if current_admin.hospital_id else hospital_id
    return AnalyticsService.get_hospital_analytics(db=db, hospital_id=target_id)

@router.get("/insurance", response_model=InsuranceAnalyticsResponse)
def get_insurance_analytics(
    current_admin: User = Depends(require_insurance_admin),
    db: Session = Depends(get_db)
):
    """Retrieve insurance policy enrollment and claim payout analytics (INSURANCE_ADMIN & SUPER_ADMIN)."""
    return AnalyticsService.get_insurance_analytics(db=db)
