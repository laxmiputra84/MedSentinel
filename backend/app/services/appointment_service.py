from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.appointment import Appointment
from app.models.user import User
from app.services.notification_service import NotificationService

VALID_APPT_STATUSES = ["PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"]

class AppointmentService:
    @staticmethod
    def get_available_slots(
        db: Optional[Session] = None,
        date: Optional[str] = None,
        department: Optional[str] = None
    ) -> List[str]:
        # Standard clinical consultation slots
        all_slots = [
            "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM", "11:00 AM",
            "11:30 AM", "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM",
            "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM", "06:00 PM"
        ]
        return all_slots

    @staticmethod
    def create_appointment(
        db: Session,
        name: str,
        phone: str,
        email: str,
        preferred_date: str,
        preferred_time: str,
        department: str,
        reason: Optional[str] = None,
        hospital_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> Appointment:
        appointment = Appointment(
            user_id=user_id,
            hospital_id=hospital_id,
            name=name,
            phone=phone,
            email=email,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            department=department,
            reason=reason,
            status="CONFIRMED"
        )
        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        if user_id:
            NotificationService.create_notification(
                db=db,
                user_id=user_id,
                title="Appointment Confirmed",
                message=f"Your consultation for {department} on {preferred_date} at {preferred_time} is confirmed.",
                type="appointment"
            )

        return appointment

    @staticmethod
    def cancel_appointment(
        db: Session,
        appointment_id: int,
        user_or_admin: User,
        reason: str = "User requested cancellation"
    ) -> Appointment:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

        # Authorization: user must own appointment unless admin
        is_owner = (appointment.user_id == user_or_admin.id) or (appointment.email == user_or_admin.email)
        is_admin = user_or_admin.role in ["HOSPITAL_ADMIN", "SUPER_ADMIN"]

        if not (is_owner or is_admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        appointment.status = "CANCELLED"
        appointment.cancelled_at = datetime.now(timezone.utc)
        appointment.cancellation_reason = reason
        db.commit()
        db.refresh(appointment)

        if appointment.user_id:
            NotificationService.create_notification(
                db=db,
                user_id=appointment.user_id,
                title="Appointment Cancelled",
                message=f"Your consultation scheduled for {appointment.preferred_date} has been cancelled. Reason: {reason}",
                type="appointment"
            )

        return appointment

    @staticmethod
    def reschedule_appointment(
        db: Session,
        appointment_id: int,
        user_or_admin: User,
        new_date: str,
        new_time: str,
        reason: Optional[str] = None
    ) -> Appointment:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

        is_owner = (appointment.user_id == user_or_admin.id) or (appointment.email == user_or_admin.email)
        is_admin = user_or_admin.role in ["HOSPITAL_ADMIN", "SUPER_ADMIN"]

        if not (is_owner or is_admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        old_date = appointment.preferred_date
        old_time = appointment.preferred_time

        appointment.preferred_date = new_date
        appointment.preferred_time = new_time
        appointment.status = "CONFIRMED"
        if reason:
            appointment.notes = f"Rescheduled from {old_date} {old_time}. Reason: {reason}"
        db.commit()
        db.refresh(appointment)

        if appointment.user_id:
            NotificationService.create_notification(
                db=db,
                user_id=appointment.user_id,
                title="Appointment Rescheduled",
                message=f"Your consultation has been moved to {new_date} at {new_time}.",
                type="appointment"
            )

        return appointment

    @staticmethod
    def update_status(
        db: Session,
        appointment_id: int,
        new_status: str,
        notes: Optional[str] = None
    ) -> Appointment:
        norm = new_status.upper().strip()
        if norm not in VALID_APPT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{new_status}'. Allowed: {', '.join(VALID_APPT_STATUSES)}"
            )

        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

        appointment.status = norm
        if notes:
            appointment.notes = notes
        db.commit()
        db.refresh(appointment)

        if appointment.user_id:
            NotificationService.create_notification(
                db=db,
                user_id=appointment.user_id,
                title=f"Appointment Status: {norm}",
                message=f"Your consultation status is now {norm}.",
                type="appointment"
            )

        return appointment

    @staticmethod
    def get_user_appointments(db: Session, user_id: int) -> List[Appointment]:
        return db.query(Appointment).filter(
            Appointment.user_id == user_id
        ).order_by(Appointment.created_at.desc()).all()

