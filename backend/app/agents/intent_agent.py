"""
MedSentinel Agentic Architecture — Intent Agent
Parses raw user requests and contextual medical data into structured, validated intent.
Never executes sensitive medical operations directly.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, WorkflowType


class StructuredIntent(BaseModel):
    intent: str
    patient_id: Optional[int] = None
    requested_operation: str
    workflow_type: WorkflowType
    risk_level: str = "UNKNOWN"
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.90


class IntentAgent(BaseAgent):
    """
    Translates incoming clinical inquiries or uploaded file contexts
    into a structured Intent specification.
    """

    def __init__(self):
        super().__init__(
            name="intent",
            role="Clinical Request & Document Intent Classifier",
            description="Extracts structured intent, clinical domain, and operation scope from user requests.",
            version="2.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        ctx = context or {}
        user_message = ctx.get("message", "") or ""
        text = state.extracted_text or ctx.get("text", "") or ""
        combined_text = f"{user_message} {text} {state.filename or ''}".lower()

        intent_name = "general_medical_inquiry"
        wtype = state.workflow_type or WorkflowType.AUTOMATIC
        operation = "review_clinical_data"
        entities = {}

        # 1. Classify Intent
        if any(w in combined_text for w in ["lab", "blood", "cbc", "lipid", "cholesterol", "hba1c", "hemoglobin", "platelet"]):
            intent_name = "lab_analysis"
            wtype = WorkflowType.LAB_REPORT
            operation = "analyze_lab_results"
        elif any(w in combined_text for w in ["prescription", "rx", "tablet", "capsule", "dosage", "medication", "mg"]):
            intent_name = "prescription_analysis"
            wtype = WorkflowType.PRESCRIPTION
            operation = "validate_prescription_and_medications"
        elif any(w in combined_text for w in ["claim", "invoice", "reimbursement", "cashless", "settlement", "insurance bill"]):
            intent_name = "claim_audit"
            wtype = WorkflowType.INSURANCE_CLAIM
            operation = "audit_insurance_claim"
        elif any(w in combined_text for w in ["appointment", "booking", "schedule", "slot", "doctor visit"]):
            intent_name = "appointment_scheduling"
            wtype = WorkflowType.APPOINTMENT
            operation = "manage_appointment"
        elif any(w in combined_text for w in ["analytics", "kpi", "dataset", "csv", "excel", "trend", "aggregate"]):
            intent_name = "healthcare_analytics"
            wtype = WorkflowType.CLINICAL_SUMMARY
            operation = "run_dataset_analytics"
        elif any(w in combined_text for w in ["summary", "discharge", "timeline", "history", "profile"]):
            intent_name = "patient_clinical_summary"
            wtype = WorkflowType.CLINICAL_SUMMARY
            operation = "synthesize_patient_summary"

        # Update state workflow type if AUTOMATIC
        if state.workflow_type == WorkflowType.AUTOMATIC or not state.workflow_type:
            state.workflow_type = wtype

        structured_intent = StructuredIntent(
            intent=intent_name,
            patient_id=state.patient_id,
            requested_operation=operation,
            workflow_type=wtype,
            risk_level="UNKNOWN",
            extracted_entities=entities,
            confidence=0.95
        )

        state.extracted_entities["structured_intent"] = structured_intent.model_dump()

        return AgentResult(
            success=True,
            agent_name=self.name,
            data=structured_intent.model_dump(),
            next_agents=["planner"]
        )
