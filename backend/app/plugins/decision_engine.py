import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models import User
from app.plugins.schema import ToolRequest, ToolResult
from app.plugins.manager import plugin_manager, PluginManager

logger = logging.getLogger("medsentinel.plugins.decision")

class DecisionEngine:
    """
    Agentic Decision Engine.
    Translates high-level clinical and administrative intents from AI agents
    into discrete, verifiable ToolRequests and dispatches them through the Plugin Manager.
    """

    def __init__(self, manager: Optional[PluginManager] = None):
        self.manager = manager or plugin_manager

    async def route_intent(
        self,
        intent: str,
        parameters: Dict[str, Any],
        agent_id: str,
        workflow_id: Optional[str] = None,
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        current_user: Optional[User] = None
    ) -> ToolResult:
        """
        Interprets agent intent, constructs the ToolRequest, and delegates to PluginManager.
        """
        intent_lower = intent.lower()

        # 1. Patient Communication Intents
        if "whatsapp" in intent_lower:
            tool_name = "send_whatsapp_message"
            permission = "whatsapp:send"
        elif "sms" in intent_lower or "otp" in intent_lower:
            tool_name = "send_otp" if "otp" in intent_lower else "send_sms"
            permission = "otp:generate" if "otp" in intent_lower else "sms:send"
        elif "email" in intent_lower or "gmail" in intent_lower:
            if "draft" in intent_lower:
                tool_name = "create_draft"
                permission = "gmail:drafts"
            else:
                tool_name = "send_approved_email"
                permission = "gmail:send"
        elif "notify" in intent_lower or "alert" in intent_lower:
            tool_name = "notify"
            permission = "notify:dispatch"

        # 2. Document & File Processing Intents
        elif "excel" in intent_lower or "spreadsheet" in intent_lower or "csv" in intent_lower:
            if "duplicate" in intent_lower:
                tool_name = "detect_duplicates"
            else:
                tool_name = "write_spreadsheet"
            permission = "excel:export"
        elif "pdf" in intent_lower:
            tool_name = "generate_pdf" if "generate" in intent_lower else "read_pdf"
            permission = "pdf:generate" if "generate" in intent_lower else "pdf:read"
        elif "word" in intent_lower or "docx" in intent_lower:
            tool_name = "generate_docx"
            permission = "docx:generate"
        elif "ocr" in intent_lower or "scan" in intent_lower:
            tool_name = "ocr_image"
            permission = "image:ocr"
        elif "vault" in intent_lower or "file" in intent_lower:
            tool_name = "upload"
            permission = "file:write"

        # 3. Clinical & Operations Intents
        elif "calendar" in intent_lower or "appointment" in intent_lower:
            tool_name = "check_availability" if "availability" in intent_lower else "create_appointment"
            permission = "calendar:read" if "availability" in intent_lower else "calendar:book"
        elif "hospital" in intent_lower or "bed" in intent_lower:
            tool_name = "check_bed_availability" if "bed" in intent_lower else "search_hospitals"
            permission = "hospital:read"
        elif "claim" in intent_lower or "insurance" in intent_lower:
            tool_name = "submit_insurance_claim" if "submit" in intent_lower else "verify_policy_eligibility"
            permission = "insurance:claim" if "submit" in intent_lower else "insurance:verify"
        elif "payment" in intent_lower or "bill" in intent_lower:
            tool_name = "create_payment_request"
            permission = "payment:charge"
        else:
            tool_name = intent
            permission = None

        request = ToolRequest(
            workflow_id=workflow_id,
            user_id=user_id,
            agent_id=agent_id,
            tool_name=tool_name,
            parameters=parameters,
            permission=permission
        )

        logger.info(f"DecisionEngine mapped intent '{intent}' -> tool '{tool_name}' for agent '{agent_id}'")
        return await self.manager.execute_tool(request, db=db, current_user=current_user)

decision_engine = DecisionEngine()
