from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.appointment import Appointment
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentRescheduleRequest,
    AppointmentCancelRequest,
    AppointmentStatusUpdateRequest,
    AvailableSlotResponse,
)
from app.dependencies.auth import get_current_user, get_optional_current_user, require_hospital_admin
from app.services.appointment_service import AppointmentService
from app.core.events import EventType
from app.services.event_bus import publish_event

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("/slots", response_model=AvailableSlotResponse)
def get_slots(
    date: str = Query(..., description="Date formatted as YYYY-MM-DD"),
    department: str = Query("General Medicine", description="Medical department")
):
    """Retrieve available clinical consultation slots for a given date and department."""
    slots = AppointmentService.get_available_slots(date=date, department=department)
    return AvailableSlotResponse(
        date=date,
        department=department,
        available_slots=slots
    )

@router.get("", response_model=List[AppointmentResponse])
def get_user_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve appointments. Hospital admins see all hospital appointments; users see their own."""
    user_role = (current_user.role or "USER").upper()
    if user_role in ["HOSPITAL_ADMIN", "SUPER_ADMIN"]:
        if current_user.hospital_id and user_role == "HOSPITAL_ADMIN":
            return db.query(Appointment).filter(
                Appointment.hospital_id == current_user.hospital_id
            ).order_by(Appointment.created_at.desc()).all()
        return db.query(Appointment).order_by(Appointment.created_at.desc()).all()

    return db.query(Appointment).filter(
        (Appointment.user_id == current_user.id) | (Appointment.email == current_user.email)
    ).order_by(Appointment.created_at.desc()).all()

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_in: AppointmentCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Create a verified appointment booking."""
    appt = AppointmentService.create_appointment(
        db=db,
        name=appointment_in.name,
        phone=appointment_in.phone,
        email=appointment_in.email,
        preferred_date=appointment_in.preferred_date,
        preferred_time=appointment_in.preferred_time,
        department=appointment_in.department,
        reason=appointment_in.reason,
        hospital_id=appointment_in.hospital_id,
        user_id=current_user.id if current_user else None
    )

    publish_event(
        event_type=EventType.APPOINTMENT_CREATED.value,
        entity_id=appt.id,
        user_id=current_user.id if current_user else None,
        payload={"department": appt.department, "date": str(appt.preferred_date), "hospital_id": appt.hospital_id},
        entity_type="appointment",
        db=db,
        sync=False,
    )

    return appt

@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    cancel_in: AppointmentCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel an appointment with a reason."""
    cancelled = AppointmentService.cancel_appointment(
        db=db,
        appointment_id=appointment_id,
        user_or_admin=current_user,
        reason=cancel_in.cancellation_reason or "User cancelled"
    )

    publish_event(
        event_type=EventType.APPOINTMENT_CANCELLED.value,
        entity_id=appointment_id,
        user_id=current_user.id,
        payload={"reason": cancel_in.cancellation_reason},
        entity_type="appointment",
        db=db,
        sync=False,
    )

    return cancelled

@router.patch("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    appointment_id: int,
    reschedule_in: AppointmentRescheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reschedule an existing appointment to a new date and time."""
    rescheduled = AppointmentService.reschedule_appointment(
        db=db,
        appointment_id=appointment_id,
        user_or_admin=current_user,
        new_date=reschedule_in.preferred_date,
        new_time=reschedule_in.preferred_time,
        reason=reschedule_in.reason
    )

    publish_event(
        event_type=EventType.APPOINTMENT_UPDATED.value,
        entity_id=appointment_id,
        user_id=current_user.id,
        payload={"new_date": str(reschedule_in.preferred_date), "new_time": reschedule_in.preferred_time},
        entity_type="appointment",
        db=db,
        sync=False,
    )

    return rescheduled

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: int,
    status_in: AppointmentStatusUpdateRequest,
    current_admin: User = Depends(require_hospital_admin),
    db: Session = Depends(get_db)
):
    """Update appointment status (HOSPITAL_ADMIN & SUPER_ADMIN only)."""
    return AppointmentService.update_status(
        db=db,
        appointment_id=appointment_id,
        new_status=status_in.status,
        notes=status_in.notes
    )
