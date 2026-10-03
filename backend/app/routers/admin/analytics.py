from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.dependencies.auth import require_super_admin
from app.models import User, Hospital, Insurance, InsuranceClaim, Appointment

router = APIRouter(prefix="/admin/analytics", tags=["Admin - Analytics"])

@router.get("/overview")
def get_extended_analytics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Deep platform analytics breakdown for administrative charts."""
    # 1. Users by Role
    role_counts = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    users_by_role = {r[0]: r[1] for r in role_counts}

    # 2. Claims by Status
    status_counts = db.query(InsuranceClaim.claim_status, func.count(InsuranceClaim.id)).group_by(InsuranceClaim.claim_status).all()
    claims_by_status = {s[0]: s[1] for s in status_counts}

    # 3. Appointments by Status
    appt_counts = db.query(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status).all()
    appointments_by_status = {a[0]: a[1] for a in appt_counts}

    # 4. Top Specializations
    top_specs = db.query(Hospital.specialization, func.count(Hospital.id)).group_by(Hospital.specialization).limit(5).all()
    specializations = [{"name": s[0] or "General", "count": s[1]} for s in top_specs]

    # 5. Financial aggregates
    total_claim_val = db.query(func.sum(InsuranceClaim.claim_amount)).scalar() or 0.0
    approved_claim_val = db.query(func.sum(InsuranceClaim.claim_amount)).filter(InsuranceClaim.claim_status == "APPROVED").scalar() or 0.0

    return {
        "users_by_role": users_by_role,
        "claims_by_status": claims_by_status,
        "appointments_by_status": appointments_by_status,
        "specializations": specializations,
        "financials": {
            "total_claims_value": float(total_claim_val),
            "approved_claims_value": float(approved_claim_val)
        }
    }
