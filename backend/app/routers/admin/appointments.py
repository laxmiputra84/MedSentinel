from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import require_any_admin
from app.models import User, Appointment
from app.services.audit_log_service import AuditLogService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/admin/appointments", tags=["Admin - Appointments"])

class AdminAppointmentStatusUpdate(BaseModel):
    status: str # PENDING, CONFIRMED, COMPLETED, CANCELLED
    notes: Optional[str] = None

@router.get("")
def list_appointments(
    status: Optional[str] = None,
    hospital_id: Optional[int] = None,
    date: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """List and filter patient consultations across all clinics."""
    query = db.query(Appointment)
    if status:
        query = query.filter(Appointment.status == status)
    if hospital_id:
        query = query.filter(Appointment.hospital_id == hospital_id)
    if date:
        query = query.filter(Appointment.preferred_date == date)

    if current_admin.role == "HOSPITAL_ADMIN" and current_admin.hospital_id:
        query = query.filter(Appointment.hospital_id == current_admin.hospital_id)

    total = query.count()
    appts = query.order_by(Appointment.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "id": a.id,
            "patient_name": a.name,
            "phone": a.phone,
            "email": a.email,
            "hospital_name": a.hospital.name if a.hospital else "General Clinic",
            "department": a.department,
            "preferred_date": a.preferred_date,
            "preferred_time": a.preferred_time,
            "status": a.status,
            "reason": a.reason,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in appts
    ]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items
    }

@router.patch("/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    payload: AdminAppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """Update appointment state (e.g. COMPLETED, CONFIRMED, CANCELLED)."""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

    if current_admin.role == "HOSPITAL_ADMIN" and current_admin.hospital_id != appt.hospital_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    old_status = appt.status
    appt.status = payload.status
    if payload.notes:
        appt.notes = payload.notes

    db.commit()
    db.refresh(appt)

    # Notify patient
    if appt.user_id:
        NotificationService.create_notification(
            db=db,
            user_id=appt.user_id,
            title=f"Appointment {payload.status.title()}",
            message=f"Your consultation with {appt.department} on {appt.preferred_date} has been updated to {payload.status}.",
            type="appointment"
        )

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="APPOINTMENT_STATUS_UPDATED",
        resource_type="Appointment",
        resource_id=str(appt.id),
        old_value={"status": old_status},
        new_value={"status": payload.status}
    )

    return appt
