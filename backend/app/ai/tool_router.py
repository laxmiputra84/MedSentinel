import re
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.models import User
from app.ai.tools.hospital_tools import search_hospitals_tool
from app.ai.tools.claim_tools import get_user_claims_tool
from app.ai.tools.appointment_tools import (
    get_user_appointments_tool,
    get_available_appointment_slots_tool,
    suggest_appointment_action_tool
)
from app.ai.tools.eligibility_tools import check_scheme_eligibility_tool
from app.ai.tools.insurance_tools import search_insurance_plans_tool
from app.ai.tools.document_tools import get_user_documents_tool
from app.ai.tools.notification_tools import get_user_notifications_tool

class ToolRouter:
    @staticmethod
    def route_and_execute(
        db: Session,
        user: User,
        user_message: str
    ) -> Tuple[List[str], Dict[str, Any], List[Dict[str, Any]]]:
        """
        Analyzes user query intent, executes matching secure Python tools,
        and aggregates context without ever exposing raw SQL or direct DB queries to the LLM.
        """
        msg = user_message.lower()
        tools_used: List[str] = []
        collected_context: Dict[str, Any] = {}
        suggested_actions: List[Dict[str, Any]] = []

        # 1. Hospital Search Intent
        if any(w in msg for w in ["hospital", "doctor", "clinic", "bed", "cardiology", "neurology", "orthopedic", "oncology", "bengaluru", "mumbai", "delhi", "near me"]):
            # Extract specialization
            spec = None
            if "heart" in msg or "cardio" in msg:
                spec = "Cardiology"
            elif "neuro" in msg or "brain" in msg:
                spec = "Neurology"
            elif "ortho" in msg or "bone" in msg:
                spec = "Orthopedics"
            elif "cancer" in msg or "oncol" in msg:
                spec = "Oncology"

            # Extract location
            loc = None
            if "bengaluru" in msg or "bangalore" in msg:
                loc = "Bengaluru"

            hosp_res = search_hospitals_tool(
                db=db,
                user=user,
                location=loc,
                specialization=spec,
                limit=5
            )
            tools_used.append("search_hospitals")
            collected_context["hospitals"] = hosp_res
            suggested_actions.append({
                "label": "View All Hospitals",
                "action": "NAVIGATE",
                "url": "/hospitals"
            })

        # 2. Insurance Claim Intent
        if any(w in msg for w in ["claim", "under review", "rejected", "approved", "reimbursement", "cashless", "settlement"]):
            claim_res = get_user_claims_tool(db=db, user=user)
            tools_used.append("get_user_claims")
            collected_context["claims"] = claim_res
            suggested_actions.append({
                "label": "Check Claim Timeline",
                "action": "NAVIGATE",
                "url": "/claims"
            })

        # 3. Appointment Intent
        if any(w in msg for w in ["appointment", "visit", "consultation", "booking", "reschedule", "cancel my appointment"]):
            appt_res = get_user_appointments_tool(db=db, user=user)
            tools_used.append("get_user_appointments")
            collected_context["appointments"] = appt_res

            # Check if user wants slot availability
            if any(w in msg for w in ["slot", "available", "when can i", "open time"]):
                slots_res = get_available_appointment_slots_tool(db=db, user=user)
                tools_used.append("get_available_appointment_slots")
                collected_context["available_slots"] = slots_res

            # Check if user requested cancellation or rescheduling
            if "cancel" in msg and appt_res["appointments"]:
                target_appt = appt_res["appointments"][0]
                action_res = suggest_appointment_action_tool(
                    db=db,
                    user=user,
                    appointment_id=target_appt["appointment_id"],
                    action="cancel",
                    reason="Patient requested via AI Assistant"
                )
                tools_used.append("suggest_appointment_cancellation")
                collected_context["appointment_action_proposal"] = action_res
                suggested_actions.append({
                    "label": f"Confirm Cancel Appointment #{target_appt['appointment_id']}",
                    "action": "CONFIRM_APPOINTMENT_CANCEL",
                    "appointment_id": target_appt["appointment_id"]
                })

            elif "reschedule" in msg and appt_res["appointments"]:
                target_appt = appt_res["appointments"][0]
                action_res = suggest_appointment_action_tool(
                    db=db,
                    user=user,
                    appointment_id=target_appt["appointment_id"],
                    action="reschedule",
                    new_date="2026-09-15",
                    new_time="10:30 AM"
                )
                tools_used.append("suggest_appointment_reschedule")
                collected_context["appointment_action_proposal"] = action_res
                suggested_actions.append({
                    "label": "Reschedule Appointment",
                    "action": "NAVIGATE",
                    "url": "/profile"
                })

        # 4. Government Scheme & Eligibility Intent
        if any(w in msg for w in ["scheme", "eligib", "ayushman", "pmjay", "mjpjay", "cghs", "esic", "qualif"]):
            # Check user eligibility with default or extracted parameters
            has_bpl = "bpl" in msg or "low income" in msg or "poor" in msg
            elig_res = check_scheme_eligibility_tool(
                db=db,
                user=user,
                income_level="low" if has_bpl else "medium",
                has_bpl_card=has_bpl,
                is_formally_employed="employed" in msg or "job" in msg
            )
            tools_used.append("check_scheme_eligibility")
            collected_context["eligibility"] = elig_res
            suggested_actions.append({
                "label": "Full Eligibility Calculator",
                "action": "NAVIGATE",
                "url": "/eligibility"
            })

        # 5. Insurance Plans Intent
        if any(w in msg for w in ["insurance plan", "premium", "coverage", "policy", "hdfc", "star health", "care supreme"]):
            ins_res = search_insurance_plans_tool(db=db, user=user)
            tools_used.append("search_insurance_plans")
            collected_context["insurances"] = ins_res
            suggested_actions.append({
                "label": "Compare Insurance Plans",
                "action": "NAVIGATE",
                "url": "/insurances"
            })

        # 6. Medical Vault / Document Intent
        if any(w in msg for w in ["document", "vault", "record", "upload", "prescription", "discharge", "report"]):
            doc_res = get_user_documents_tool(db=db, user=user)
            tools_used.append("get_user_documents")
            collected_context["documents"] = doc_res
            suggested_actions.append({
                "label": "Open Medical Vault",
                "action": "NAVIGATE",
                "url": "/medical-vault"
            })

        # 7. Notification Intent
        if any(w in msg for w in ["notification", "alert", "message", "update"]):
            notif_res = get_user_notifications_tool(db=db, user=user)
            tools_used.append("get_user_notifications")
            collected_context["notifications"] = notif_res

        # If no specific intent was detected, load general user overview
        if not tools_used:
            collected_context["user_summary"] = {
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "blood_group": user.blood_group
            }

        return tools_used, collected_context, suggested_actions
