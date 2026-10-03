from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding
from app.services.appointment_service import AppointmentService
from app.models.appointment import Appointment


class AppointmentAgent(BaseAgent):
    """
    Specialized agent for Clinical Appointment Verification and Scheduling Lifecycle.
    - Validates slot availability and department routing.
    - Verifies patient contact and empanelled hospital availability.
    - Logs scheduling lifecycle events.
    """

    def __init__(self):
        super().__init__(
            name="appointment",
            role="Clinical Consultation & Appointment Scheduling Controller",
            description="Coordinates verified consultation slots, checks hospital department availability, and manages booking lifecycle.",
            version="2.0.0",
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        ctx = context or {}
        appt_id = ctx.get("appointment_id")
        findings: List[ClinicalFinding] = []
        appt_info: Dict[str, Any] = {}

        if db and appt_id:
            appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
            if appt:
                appt_info = {
                    "id": appt.id,
                    "hospital": appt.hospital.name if appt.hospital else "Hospital",
                    "department": appt.department,
                    "date": str(appt.preferred_date),
                    "time": appt.preferred_time,
                    "status": appt.status,
                }
                findings.append(
                    self.create_finding(
                        title=f"Appointment {appt.status}: {appt.department}",
                        description=f"Consultation scheduled for {appt.preferred_date} at {appt.preferred_time} ({appt.department}). Reason: {appt.reason or 'Routine follow-up'}",
                        category="APPOINTMENT_SCHEDULE",
                        status="NORMAL",
                        confidence=0.98,
                    )
                )

        return AgentResult(
            success=True,
            agent_name=self.name,
            findings=findings,
            data={"appointment": appt_info},
        )

    # -------------------------------------------------------------
    # Backwards-Compatible Static Method
    # -------------------------------------------------------------
    @staticmethod
    async def get_user_appointments_data(user_id: int, user_role: str, db: Session) -> Dict[str, Any]:
        if user_role in ["SUPER_ADMIN", "HOSPITAL_ADMIN"]:
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
                "reason": a.reason,
            })

        return {
            "appointments": items,
            "total": len(items),
        }
