import re
from typing import Dict, Any, List

class PlannerAgent:
    """
    Classifies user intent, selects active execution mode, and orchestrates
    necessary sub-agents (RAG, Tools, Data).
    """
    @staticmethod
    def plan(
        user_message: str,
        user_role: str,
        requested_mode: str = "strict_private"
    ) -> Dict[str, Any]:
        msg_lower = user_message.lower()

        # Intent classification
        intents = []
        requires_rag = True
        requires_tools = False
        target_agent = "retrieval_agent"

        # Check for administrative analytics
        if any(w in msg_lower for w in ["analytics", "kpi", "telemetry", "platform statistics", "settlement ratio"]) and user_role in ["SUPER_ADMIN", "HOSPITAL_ADMIN"]:
            intents.append("ADMIN_ANALYTICS")
            target_agent = "analytics_agent"
            requires_tools = True

        # Check for claim inquiries
        elif any(w in msg_lower for w in ["claim", "reimbursement", "cashless", "settlement"]):
            intents.append("CLAIMS_INQUIRY")
            target_agent = "claims_agent"
            requires_tools = True

        # Check for appointment inquiries
        elif any(w in msg_lower for w in ["appointment", "doctor slot", "consultation", "booking", "schedule"]):
            intents.append("APPOINTMENT_INQUIRY")
            target_agent = "appointment_agent"
            requires_tools = True

        # Check for government scheme eligibility
        elif any(w in msg_lower for w in ["eligibility", "ayushman", "scheme", "qualify", "bpl", "mjpjay"]):
            intents.append("ELIGIBILITY_INQUIRY")
            target_agent = "eligibility_agent"
            requires_tools = True

        # Check for medical vault documents
        elif any(w in msg_lower for w in ["my document", "vault", "discharge summary", "uploaded prescription", "pending verification"]):
            intents.append("DOCUMENT_INQUIRY")
            target_agent = "document_agent"
            requires_tools = True

        # Check for hospital searches & facilities
        elif any(w in msg_lower for w in ["hospital", "icu", "bed", "cardiology", "neurology", "orthopedic", "facility"]):
            intents.append("HOSPITAL_INQUIRY")
            target_agent = "hospital_agent"
            requires_tools = True
        else:
            intents.append("GENERAL_KNOWLEDGE_INQUIRY")
            target_agent = "retrieval_agent"

        return {
            "intents": intents,
            "target_agent": target_agent,
            "requires_rag": requires_rag,
            "requires_tools": requires_tools,
            "mode": requested_mode
        }
