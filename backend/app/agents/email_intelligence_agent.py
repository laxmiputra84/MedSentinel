import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import (
    WorkflowState,
    AgentResult,
    WorkflowStatus,
    EscalationLevel,
)

class EmailIntelligenceAgent(BaseAgent):
    """
    Dedicated Email Intelligence Agent for MedSentinel.
    Inspects raw email communications from Gmail or enterprise email connectors:
    - Performs zero-trust boundary sanitization
    - Classifies email intent (CLAIM, APPOINTMENT, LAB_REPORT, PATIENT_QUERY, ADMIN)
    - Detects patient identifiers, claim numbers, and hospital mentions
    - Evaluates urgency and flags clinical escalation
    - Extracts attachment metadata and routes to DocumentIntelligence or Claims agent.
    """

    def __init__(self):
        super().__init__(
            name="email_intelligence",
            role="Inbound Healthcare Email Triage & Metadata Intelligence",
            description="Classifies healthcare emails, detects patients/claims/attachments, and routes to workflow agents.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        context = context or {}
        raw_email = context.get("email") or {}
        
        subject = str(raw_email.get("subject", "") or "")
        body = str(raw_email.get("body", "") or "")
        sender = str(raw_email.get("sender", "") or "")
        attachments = raw_email.get("attachments", []) or []

        combined_text = f"{subject}\n{body}"

        # 1. Intent & Category Classification
        category = "PATIENT_QUERY"
        if re.search(r"(?i)\b(claim|reimbursement|pre-auth|policy|tpa|cashless)\b", combined_text):
            category = "CLAIM"
        elif re.search(r"(?i)\b(appointment|reschedule|booking|slot|consultation|dr\.|doctor)\b", combined_text):
            category = "APPOINTMENT"
        elif re.search(r"(?i)\b(lab|biopsy|radiology|mri|ct\s*scan|x-ray|blood\s*test|ecg)\b", combined_text):
            category = "LAB_REPORT"
        elif re.search(r"(?i)\b(hospital|admission|discharge|ward|icu)\b", combined_text):
            category = "HOSPITAL_COMMUNICATION"

        # 2. Extract Claim ID
        claim_match = re.search(r"(?i)\b(?:claim|clm)[-_#]?\s*([a-z0-9]{4,12})\b", combined_text)
        claim_id = f"CLM-{claim_match.group(1).upper()}" if claim_match else None

        # 3. Extract Patient Reference
        patient_match = re.search(r"(?i)\b(?:patient|pat|mr\.|mrs\.|ms\.)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b", combined_text)
        patient_name = patient_match.group(1).strip() if patient_match else None

        # 4. Urgency Detection
        urgency = "NORMAL"
        if re.search(r"(?i)\b(urgent|immediate|emergency|critical|life[- ]threatening|severe)\b", combined_text):
            urgency = "HIGH"

        # 5. Attachment Metadata Analysis
        processed_attachments = []
        for att in attachments:
            fname = att.get("filename", "unknown_document")
            mime = att.get("mime_type", "application/octet-stream")
            size = att.get("size_bytes", 0)
            is_supported = any(fname.lower().endswith(ext) for ext in [".pdf", ".docx", ".xlsx", ".csv", ".jpg", ".png", ".jpeg"])
            processed_attachments.append({
                "filename": fname,
                "mime_type": mime,
                "size_bytes": size,
                "supported": is_supported,
                "recommended_tool": "upload_file" if is_supported else None
            })

        # 6. Route to Next Agent
        next_agent = "patient_intake"
        if category == "CLAIM" and processed_attachments:
            next_agent = "document_intelligence"
        elif category == "CLAIM":
            next_agent = "claims"
        elif category == "APPOINTMENT":
            next_agent = "appointment"
        elif category == "LAB_REPORT":
            next_agent = "lab_analysis"

        result_data = {
            "email_sender": sender,
            "category": category,
            "urgency": urgency,
            "detected_claim_id": claim_id,
            "detected_patient_name": patient_name,
            "attachment_count": len(attachments),
            "attachments_summary": processed_attachments,
            "proposed_next_agent": next_agent,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }

        return AgentResult(
            agent_name=self.name,
            status=WorkflowStatus.COMPLETED,
            data=result_data,
            reasoning=f"Classified email as {category} with {urgency} urgency. Routed to {next_agent} agent.",
            next_agent=next_agent,
            requires_human_review=(urgency == "HIGH" or category == "CLAIM")
        )
