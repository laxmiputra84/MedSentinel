"""
MedSentinel Agentic Architecture — Orchestrator Agent (Workflow Controller)
Central coordinator managing dynamic conditional DAG routing, state persistence,
step-by-step agent invocation, error containment, and audit compilation.
"""

from typing import Any, Dict, List, Optional, Type
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import (
    WorkflowState,
    AgentResult,
    WorkflowType,
    WorkflowStatus,
    EscalationLevel,
)
from app.agents.patient_intake_agent import PatientIntakeAgent
from app.agents.document_intelligence_agent import DocumentIntelligenceAgent
from app.agents.ocr_agent import OCRAgent
from app.agents.data_validation_agent import DataValidationAgent
from app.agents.patient_history_agent import PatientHistoryAgent
from app.agents.symptom_clinical_agent import SymptomClinicalAgent
from app.agents.lab_analysis_agent import LabAnalysisAgent
from app.agents.medical_rag_agent import MedicalRAGAgent
from app.agents.risk_prediction_agent import RiskPredictionAgent
from app.agents.verification_report_agent import VerificationReportAgent
from app.agents.hospital_matching_agent import HospitalMatchingAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.claims_agent import ClaimsAgent
from app.agents.appointment_agent import AppointmentAgent


class AgentRegistry:
    """Lightweight registry holding initialized specialized agents."""

    def __init__(self):
        doc_intel = DocumentIntelligenceAgent()
        patient_hist = PatientHistoryAgent()
        claims_ag = ClaimsAgent()

        self._agents: Dict[str, BaseAgent] = {
            "patient_intake": PatientIntakeAgent(),
            "document_intelligence": doc_intel,
            "document_classification": doc_intel,
            "ocr": OCRAgent(),
            "data_validation": DataValidationAgent(),
            "patient_history": patient_hist,
            "patient_timeline": patient_hist,
            "symptom_clinical": SymptomClinicalAgent(),
            "lab_analysis": LabAnalysisAgent(),
            "medical_rag": MedicalRAGAgent(),
            "risk_prediction": RiskPredictionAgent(),
            "verification_report": VerificationReportAgent(),
            "hospital_matching": HospitalMatchingAgent(),
            "safety": SafetyAgent(),
            "claims": claims_ag,
            "fraud_detection": claims_ag,
            "appointment": AppointmentAgent(),
            "appointment_workflow": AppointmentAgent(),
        }

    def get(self, name: str) -> Optional[BaseAgent]:
        return self._agents.get(name)

    def register(self, name: str, agent: BaseAgent) -> None:
        self._agents[name] = agent

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())


class OrchestratorAgent(BaseAgent):
    """
    Central workflow coordinator for MedSentinel.
    Plans, dynamically routes, and executes specialized agents conditionally.
    """

    def __init__(self, registry: Optional[AgentRegistry] = None):
        super().__init__(
            name="orchestrator",
            role="Central Workflow Planner & Execution Controller",
            description="Dynamic DAG planner orchestrating conditional execution of specialized healthcare agents.",
            version="1.0.0"
        )
        self.registry = registry or AgentRegistry()

    def plan_workflow(self, state: WorkflowState) -> List[str]:
        """
        Calculates the optimal sequential and conditional DAG of agents to run
        based on the workflow type.
        """
        wtype = state.workflow_type

        if wtype == WorkflowType.LAB_REPORT:
            return [
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
        elif wtype == WorkflowType.PRESCRIPTION:
            return [
                "patient_intake",
                "document_intelligence",
                "ocr",
                "data_validation",
                "symptom_clinical",
                "medical_rag",
                "safety",
                "verification_report",
            ]
        elif wtype == WorkflowType.INSURANCE_CLAIM:
            return [
                "patient_intake",
                "document_intelligence",
                "claims",
                "risk_prediction",
                "safety",
                "verification_report",
            ]
        elif wtype == WorkflowType.APPOINTMENT:
            return [
                "patient_intake",
                "appointment",
                "safety",
                "verification_report",
            ]
        elif wtype == WorkflowType.PATIENT_PROFILE:
            return [
                "patient_intake",
                "patient_history",
                "risk_prediction",
                "safety",
                "verification_report",
            ]
        elif wtype == WorkflowType.CLINICAL_SUMMARY:
            return [
                "patient_intake",
                "document_intelligence",
                "ocr",
                "data_validation",
                "patient_history",
                "symptom_clinical",
                "medical_rag",
                "risk_prediction",
                "safety",
                "verification_report",
            ]
        else:
            # Default / Automatic Discovery Flow
            return [
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

    def plan_for_event(self, event_type: str, state: WorkflowState) -> List[str]:
        """
        Dynamically plans the required agent execution DAG based on incoming healthcare event.
        Ensures scoped execution without running unnecessary agents.
        """
        ev = event_type.upper().strip()

        # Patient Events
        if ev == "PATIENT_CREATED":
            return ["patient_intake", "verification_report"]
        elif ev == "PATIENT_UPDATED":
            return ["patient_history", "risk_prediction", "verification_report"]

        # Document Events
        elif ev == "DOCUMENT_UPLOADED":
            return ["document_intelligence"]
        elif ev == "DOCUMENT_UPDATED":
            return ["document_intelligence", "verification_report"]
        elif ev == "DOCUMENT_VERIFIED":
            return ["verification_report"]
        elif ev == "DOCUMENT_DUPLICATE_DETECTED":
            return ["safety", "verification_report"]

        # Laboratory Events
        elif ev == "LAB_REPORT_RECEIVED":
            return ["ocr", "lab_analysis", "patient_history", "risk_prediction", "safety", "verification_report"]
        elif ev == "LAB_ANALYSIS_COMPLETED":
            return ["risk_prediction", "safety", "verification_report"]
        elif ev == "CRITICAL_LAB_VALUE_DETECTED":
            return ["safety", "verification_report"]

        # Insurance Events
        elif ev == "CLAIM_CREATED":
            return ["claims", "safety", "verification_report"]
        elif ev == "CLAIM_UPDATED":
            return ["claims", "verification_report"]
        elif ev == "FRAUD_FLAG_DETECTED":
            return ["safety", "verification_report"]

        # Appointment Events
        elif ev == "APPOINTMENT_CREATED":
            return ["appointment", "safety", "verification_report"]
        elif ev == "APPOINTMENT_UPDATED":
            return ["appointment", "verification_report"]
        elif ev == "APPOINTMENT_CANCELLED":
            return ["appointment", "verification_report"]

        # Fallback to standard workflow type planner
        return self.plan_workflow(state)

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Orchestrates step-by-step execution across specialized agents.
        Emits live execution telemetry events if on_event callback is provided in context.
        """
        on_event = context.get("on_event") if context else None

        state.status = WorkflowStatus.IN_PROGRESS
        state.add_audit_entry(
            agent_name=self.name,
            action=f"Orchestrator planned workflow '{state.workflow_type.value}' for workflow ID {state.workflow_id}",
            status="SUCCESS",
            confidence=0.99
        )

        if on_event:
            await on_event("workflow_started", {
                "workflow_id": state.workflow_id,
                "workflow_type": state.workflow_type.value,
                "status": state.status.value,
            })

        planned_dag = self.plan_workflow(state)
        current_dag = list(planned_dag)
        executed_steps: List[str] = []

        i = 0
        while i < len(current_dag):
            agent_key = current_dag[i]
            agent = self.registry.get(agent_key)

            if not agent:
                state.mark_agent_skipped(agent_key)
                if on_event:
                    await on_event("agent_skipped", {
                        "workflow_id": state.workflow_id,
                        "agent": agent_key,
                        "status": "SKIPPED"
                    })
                i += 1
                continue

            # Live event: Agent started
            if on_event:
                await on_event("agent_started", {
                    "workflow_id": state.workflow_id,
                    "agent": agent_key,
                    "status": "RUNNING"
                })

            # Execute agent safely
            result = await agent.run(state=state, db=db, context=context)
            executed_steps.append(agent_key)

            # Live event: Agent completed / failed
            if on_event:
                duration_ms = result.execution_log.duration_ms if result.execution_log else None
                confidence = result.execution_log.confidence if result.execution_log else None
                if result.success:
                    await on_event("agent_completed", {
                        "workflow_id": state.workflow_id,
                        "agent": agent_key,
                        "status": "COMPLETED",
                        "duration_ms": duration_ms,
                        "confidence": confidence,
                        "findings_count": len(result.findings)
                    })
                else:
                    await on_event("agent_failed", {
                        "workflow_id": state.workflow_id,
                        "agent": agent_key,
                        "status": "FAILED",
                        "error": "; ".join(result.errors) if result.errors else "Agent execution failed"
                    })

            # Check if critical escalation was triggered in this step
            if state.escalation_required and on_event:
                await on_event("escalation_required", {
                    "workflow_id": state.workflow_id,
                    "agent": agent_key,
                    "reason": state.escalation_reason,
                    "escalation_level": state.escalation_level.value if hasattr(state.escalation_level, "value") else str(state.escalation_level)
                })

            # 1. Dynamic DAG Re-planning: Check if Document Intelligence changed workflow type
            if agent_key == "document_intelligence":
                new_plan = self.plan_workflow(state)
                # Rebuild remaining DAG excluding already completed agents
                remaining = [step for step in new_plan if step not in executed_steps]
                current_dag = executed_steps + remaining
                if on_event:
                    await on_event("decision", {
                        "workflow_id": state.workflow_id,
                        "decision": f"Re-planned workflow to {state.workflow_type.value}",
                        "remaining_steps": remaining
                    })

            # 2. Early Failure Interception: If OCR or Intake fatally fails, route to verification
            if not result.success and agent_key in ["ocr", "patient_intake"]:
                # Mark remaining non-report agents as skipped
                for remaining_step in current_dag[i + 1:]:
                    if remaining_step != "verification_report":
                        state.mark_agent_skipped(remaining_step)
                        if on_event:
                            await on_event("agent_skipped", {
                                "workflow_id": state.workflow_id,
                                "agent": remaining_step,
                                "status": "SKIPPED",
                                "reason": f"Skipped due to upstream failure in '{agent_key}'"
                            })

                # Ensure verification report agent runs to compile error report
                verif_agent = self.registry.get("verification_report")
                if verif_agent:
                    if on_event:
                        await on_event("agent_started", {
                            "workflow_id": state.workflow_id,
                            "agent": "verification_report",
                            "status": "RUNNING"
                        })
                    verif_res = await verif_agent.run(state=state, db=db, context=context)
                    if on_event:
                        await on_event("agent_completed", {
                            "workflow_id": state.workflow_id,
                            "agent": "verification_report",
                            "status": "COMPLETED",
                            "duration_ms": verif_res.execution_log.duration_ms if verif_res.execution_log else None
                        })
                break

            i += 1

        # Determine final workflow status if not already set by Verification Agent
        if state.status == WorkflowStatus.IN_PROGRESS:
            if state.escalation_required:
                state.status = WorkflowStatus.DOCTOR_REVIEW_REQUIRED
            else:
                state.status = WorkflowStatus.COMPLETED

        state.add_audit_entry(
            agent_name=self.name,
            action=f"Orchestrator finalized workflow execution with status '{state.status.value}'",
            status="SUCCESS",
            confidence=0.98,
            details={"executed_steps": executed_steps, "status": state.status.value}
        )

        if on_event:
            await on_event("workflow_completed", {
                "workflow_id": state.workflow_id,
                "status": state.status.value,
                "requires_human_review": state.escalation_required,
                "findings_count": len(state.clinical_findings),
                "summary": state.final_report.executive_summary if state.final_report else "Workflow completed"
            })

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "status": state.status.value,
                "executed_steps": executed_steps,
                "escalation_required": state.escalation_required,
                "findings_count": len(state.clinical_findings),
            }
        )
