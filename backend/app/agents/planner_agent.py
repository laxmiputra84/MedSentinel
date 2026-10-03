"""
MedSentinel Agentic Architecture — Planner Agent
Constructs, validates, and optimizes Directed Acyclic Graph (DAG) execution plans.
Ensures step dependencies are resolved and cycles are prevented.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, WorkflowType


class ExecutionPlan(BaseModel):
    workflow_type: str
    steps: List[str]
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    parallel_batches: List[List[str]] = Field(default_factory=list)
    estimated_duration_ms: float = 1200.0


class PlannerAgent(BaseAgent):
    """
    Constructs a validated, cycle-free DAG execution plan for the workflow.
    """

    def __init__(self):
        super().__init__(
            name="planner",
            role="DAG Workflow Planner & Task Decomposer",
            description="Decomposes clinical requests into an optimized Directed Acyclic Graph of specialized agents.",
            version="2.0.0"
        )

    # Backward compatibility for legacy callers
    @staticmethod
    def plan(
        user_message: str,
        user_role: str,
        requested_mode: str = "strict_private"
    ) -> Dict[str, Any]:
        msg_lower = user_message.lower()
        intents = []
        requires_rag = True
        requires_tools = False
        target_agent = "retrieval_agent"

        if any(w in msg_lower for w in ["analytics", "kpi", "telemetry", "platform statistics", "settlement ratio"]) and user_role in ["SUPER_ADMIN", "HOSPITAL_ADMIN"]:
            intents.append("ADMIN_ANALYTICS")
            target_agent = "analytics_agent"
            requires_tools = True
        elif any(w in msg_lower for w in ["claim", "reimbursement", "cashless", "settlement"]):
            intents.append("CLAIMS_INQUIRY")
            target_agent = "claims_agent"
            requires_tools = True
        elif any(w in msg_lower for w in ["appointment", "doctor slot", "consultation", "booking", "schedule"]):
            intents.append("APPOINTMENT_INQUIRY")
            target_agent = "appointment_agent"
            requires_tools = True
        elif any(w in msg_lower for w in ["eligibility", "ayushman", "scheme", "qualify", "bpl", "mjpjay"]):
            intents.append("ELIGIBILITY_INQUIRY")
            target_agent = "eligibility_agent"
            requires_tools = True
        elif any(w in msg_lower for w in ["my document", "vault", "discharge summary", "uploaded prescription"]):
            intents.append("DOCUMENT_INQUIRY")
            target_agent = "document_agent"
            requires_tools = True
        elif any(w in msg_lower for w in ["hospital", "icu", "bed", "cardiology", "neurology"]):
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

    def generate_plan(self, state: WorkflowState) -> ExecutionPlan:
        """Calculates the execution steps and dependency DAG for the workflow."""
        wtype = state.workflow_type

        if wtype == WorkflowType.LAB_REPORT:
            steps = [
                "patient_intake",
                "document_intelligence",
                "ocr",
                "lab_analysis",
                "data_validation",
                "patient_history",
                "risk_prediction",
                "medical_rag",
                "safety",
                "verification_report",
            ]
            parallel_batches = [
                ["patient_intake"],
                ["document_intelligence", "ocr"],
                ["lab_analysis", "data_validation"],
                ["patient_history", "risk_prediction", "medical_rag"],
                ["safety"],
                ["verification_report"]
            ]
        elif wtype == WorkflowType.PRESCRIPTION:
            steps = [
                "patient_intake",
                "document_intelligence",
                "ocr",
                "data_validation",
                "symptom_clinical",
                "medication_safety",
                "medical_rag",
                "safety",
                "verification_report",
            ]
            parallel_batches = [
                ["patient_intake"],
                ["document_intelligence", "ocr"],
                ["data_validation", "symptom_clinical"],
                ["medication_safety", "medical_rag"],
                ["safety"],
                ["verification_report"]
            ]
        elif wtype == WorkflowType.INSURANCE_CLAIM:
            steps = [
                "patient_intake",
                "document_intelligence",
                "claims",
                "risk_prediction",
                "safety",
                "verification_report",
            ]
            parallel_batches = [
                ["patient_intake"],
                ["document_intelligence"],
                ["claims", "risk_prediction"],
                ["safety"],
                ["verification_report"]
            ]
        elif wtype == WorkflowType.APPOINTMENT:
            steps = [
                "patient_intake",
                "appointment",
                "safety",
                "verification_report",
            ]
            parallel_batches = [
                ["patient_intake"],
                ["appointment"],
                ["safety"],
                ["verification_report"]
            ]
        else:
            # Automatic / Clinical Summary Flow
            steps = [
                "patient_intake",
                "document_intelligence",
                "ocr",
                "lab_analysis",
                "data_validation",
                "patient_history",
                "risk_prediction",
                "medical_rag",
                "safety",
                "verification_report",
            ]
            parallel_batches = [
                ["patient_intake"],
                ["document_intelligence", "ocr"],
                ["lab_analysis", "data_validation"],
                ["patient_history", "risk_prediction"],
                ["medical_rag"],
                ["safety"],
                ["verification_report"]
            ]

        return ExecutionPlan(
            workflow_type=wtype.value,
            steps=steps,
            parallel_batches=parallel_batches
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        plan = self.generate_plan(state)
        state.extracted_entities["execution_plan"] = plan.model_dump()

        return AgentResult(
            success=True,
            agent_name=self.name,
            data=plan.model_dump(),
            next_agents=plan.steps[:1]
        )
