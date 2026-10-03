from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.core.database import get_db
from app.dependencies.auth import require_any_admin, require_super_admin
from app.models import (
    User,
    Hospital,
    Insurance,
    UserInsurance,
    InsuranceClaim,
    Appointment,
    UserDocument,
    Notification,
    AdminAuditLog
)

router = APIRouter(prefix="/admin/dashboard", tags=["Admin - Dashboard"])

@router.get("")
@router.get("/")
@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """Provides high-level KPI cards and recent operational activity for the Super Admin overview."""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_hospitals = db.query(Hospital).count()
    total_insurances = db.query(Insurance).count()
    total_policies = db.query(UserInsurance).count()

    total_claims = db.query(InsuranceClaim).count()
    pending_claims = db.query(InsuranceClaim).filter(InsuranceClaim.claim_status.in_(["SUBMITTED", "UNDER_REVIEW", "DOCUMENTS_REQUIRED"])).count()
    approved_claims = db.query(InsuranceClaim).filter(InsuranceClaim.claim_status == "APPROVED").count()
    rejected_claims = db.query(InsuranceClaim).filter(InsuranceClaim.claim_status == "REJECTED").count()

    total_appointments = db.query(Appointment).count()
    pending_documents = db.query(UserDocument).filter(UserDocument.status == "PENDING").count()
    unread_notifications = db.query(Notification).filter(Notification.is_read == False).count()

    # Today's counts
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_registrations = db.query(User).filter(User.created_at >= today_start).count()
    today_claims = db.query(InsuranceClaim).filter(InsuranceClaim.claim_date >= today_start).count()
    today_appointments = db.query(Appointment).filter(Appointment.created_at >= today_start).count()

    # Recent Audit Log Activity
    recent_logs = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(8).all()
    recent_activity = [
        {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "admin_name": log.admin_user.name if log.admin_user else "System Admin",
            "timestamp": log.created_at.isoformat() if log.created_at else None
        }
        for log in recent_logs
    ]

    return {
        "cards": {
            "total_users": total_users,
            "active_users": active_users,
            "total_hospitals": total_hospitals,
            "total_insurances": total_insurances,
            "total_policies": total_policies,
            "total_claims": total_claims,
            "pending_claims": pending_claims,
            "approved_claims": approved_claims,
            "rejected_claims": rejected_claims,
            "total_appointments": total_appointments,
            "pending_documents": pending_documents,
            "unread_notifications": unread_notifications
        },
        "today": {
            "registrations": today_registrations,
            "claims": today_claims,
            "appointments": today_appointments
        },
        "recent_activity": recent_activity
    }
