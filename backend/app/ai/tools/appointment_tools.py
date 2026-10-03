from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import User, Appointment
from app.services.appointment_service import AppointmentService

def get_user_appointments_tool(
    db: Session,
    user: User,
    status_filter: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve appointments for the authenticated user."""
    query = db.query(Appointment).filter(Appointment.user_id == user.id)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    appts = query.order_by(Appointment.created_at.desc()).all()

    items = []
    for a in appts:
        items.append({
            "appointment_id": a.id,
            "patient_name": a.name,
            "hospital_name": a.hospital.name if a.hospital else "General Clinic",
            "department": a.department,
            "preferred_date": a.preferred_date,
            "preferred_time": a.preferred_time,
            "status": a.status,
            "reason": a.reason,
            "cancellation_reason": a.cancellation_reason
        })

    return {
        "user_email": user.email,
        "total_appointments": len(items),
        "appointments": items
    }

def get_available_appointment_slots_tool(
    db: Session,
    user: User,
    date: Optional[str] = None,
    department: Optional[str] = None
) -> Dict[str, Any]:
    """Get open consultation slots for a specific date and clinical department."""
    slots = AppointmentService.get_available_slots(db=db, date=date, department=department)
    return {
        "requested_date": date or "Next Available",
        "department": department or "General Consultation",
        "available_slots": slots,
        "booking_note": "To confirm a booking, please proceed via the Book Appointment interface or confirm with your selected slot."
    }

def suggest_appointment_action_tool(
    db: Session,
    user: User,
    appointment_id: int,
    action: str,  # 'cancel' or 'reschedule'
    new_date: Optional[str] = None,
    new_time: Optional[str] = None,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """Prepares a structured action for appointment modification requiring explicit user confirmation."""
    appt = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.user_id == user.id
    ).first()

    if not appt:
        return {
            "success": False,
            "error": f"Appointment #{appointment_id} not found in your account."
        }

    return {
        "success": True,
        "requires_user_confirmation": True,
        "proposed_action": action.upper(),
        "appointment_id": appt.id,
        "hospital_name": appt.hospital.name if appt.hospital else "Clinic",
        "current_schedule": f"{appt.preferred_date} at {appt.preferred_time}",
        "new_schedule": f"{new_date} at {new_time}" if (new_date and new_time) else None,
        "reason": reason or "Patient requested change",
        "confirmation_prompt": f"Please confirm if you want to {action.lower()} your {appt.department} appointment (ID #{appt.id})."
    }
