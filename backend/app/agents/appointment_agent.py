from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.appointment_service import AppointmentService
from app.models.appointment import Appointment

class AppointmentAgent:
    """
    Retrieves and summarizes consultation records strictly authorized for the user.
    """
    @staticmethod
    async def get_user_appointments_data(user_id: int, user_role: str, db: Session) -> Dict[str, Any]:
        if user_role == "SUPER_ADMIN" or user_role == "HOSPITAL_ADMIN":
            appts = db.query(Appointment).order_by(Appointment.created_at.desc()).limit(10).all()
        else:
            appts = AppointmentService.get_user_appointments(db=db, user_id=user_id)

        items = []
        for a in appts:
            items.append({
                "appointment_id": a.id,
                "hospital": a.hospital.name if a.hospital else "Hospital",
                "department": a.department,
                "preferred_date": str(a.preferred_date),
                "preferred_time": a.preferred_time,
                "status": a.status,
                "reason": a.reason
            })

        return {
            "appointments": items,
            "total": len(items)
        }
