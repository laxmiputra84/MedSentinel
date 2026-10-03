import re
from typing import Dict, Any, Tuple, Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai.safety import AISafetyGuard
from app.agents.base import BaseAgent
from app.agents.state import (
    WorkflowState,
    AgentResult,
    ClinicalFinding,
    EscalationLevel,
    WorkflowStatus,
)


class SafetyAgent(BaseAgent):
    """
    Production Safety & Clinical Guardrail Agent.
    - Validates user prompts, tool executions, and model responses against data leaks and injections.
    - Enforces strict non-diagnostic disclaimers on all clinical summaries.
    - Intercepts critical/panic laboratory values and mandates doctor review escalation.
    - Audits every automated clinical decision before final persistence.
    """

    MANDATORY_DISCLAIMER = (
        "Notice: MedSentinel is a clinical intelligence and decision-support platform. "
        "It does not provide definitive medical diagnoses, prescriptions, or autonomous clinical treatments. "
        "All alerts and findings must be reviewed by a licensed healthcare professional."
    )

    def __init__(self):
        super().__init__(
            name="safety",
            role="Clinical Safety & Regulatory Guardrail Supervisor",
            description="Enforces non-diagnostic compliance, panic value escalation, and safety verification across all workflows.",
            version="2.0.0",
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        findings: List[ClinicalFinding] = []
        critical_values_found: List[str] = []
        safety_violations: List[str] = []

        # 1. Inspect Laboratory Results for Critical Panic Values
        if state.lab_results:
            items = state.lab_results.values() if isinstance(state.lab_results, dict) else state.lab_results
            for lr in items:
                if isinstance(lr, dict):
                    is_crit = lr.get("is_critical", False)
                    status = str(lr.get("status", "")).upper()
                    test_name = lr.get("test_name", lr.get("name", "Unknown Test"))
                    val = lr.get("observed_value", lr.get("value"))
                    unit = lr.get("unit", "")
                elif hasattr(lr, "is_critical"):
                    is_crit = getattr(lr, "is_critical", False)
                    status = str(getattr(lr, "status", "")).upper()
                    test_name = getattr(lr, "test_name", "Unknown Test")
                    val = getattr(lr, "observed_value", "")
                    unit = getattr(lr, "unit", "")
                else:
                    continue

                if is_crit or status == "CRITICAL":
                    critical_values_found.append(f"{test_name}: {val} {unit} [CRITICAL PANIC VALUE]")

        # 2. Check for Critical Escalation Trigger
        if critical_values_found:
            state.escalation_required = True
            state.escalation_level = EscalationLevel.CRITICAL
            state.status = WorkflowStatus.DOCTOR_REVIEW_REQUIRED
            escalation_msg = (
                f"Critical panic value detected: Urgent Safety Alert for life-threatening laboratory values ({', '.join(critical_values_found[:3])}). "
                "Immediate physician/doctor clinical review is required."
            )
            state.escalation_reason = escalation_msg

            findings.append(
                self.create_finding(
                    title="Critical Value Emergency Escalation",
                    description=escalation_msg,
                    category="SAFETY_ESCALATION",
                    status="CRITICAL",
                    is_critical=True,
                    evidence="Clinical Pathology Panic Ranges",
                    confidence=0.99,
                )
            )

        # 3. Non-Diagnostic Verification of Executive Summary & Reports
        if state.final_report and state.final_report.executive_summary:
            summary_text = state.final_report.executive_summary
            # Ensure mandatory disclaimer is present
            if "does not provide a medical diagnosis" not in summary_text.lower() and "non-diagnostic" not in summary_text.lower():
                state.final_report.executive_summary += f"\n\n{self.MANDATORY_DISCLAIMER}"

        # 4. Record Safety Audit Entry
        safety_decision = {
            "critical_values_count": len(critical_values_found),
            "escalation_mandated": state.escalation_required,
            "disclaimer_attached": True,
            "safety_status": "FLAGGED_FOR_REVIEW" if state.escalation_required else "PASSED",
        }

        state.add_audit_entry(
            agent_name=self.name,
            action="Clinical safety and non-diagnostic compliance verification completed",
            status="SUCCESS",
            confidence=0.99,
            details=safety_decision,
        )

        return AgentResult(
            success=True,
            agent_name=self.name,
            findings=findings,
            data=safety_decision,
        )

    # -------------------------------------------------------------
    # Backwards-Compatible Static Methods for Direct Security Usage
    # -------------------------------------------------------------
    @staticmethod
    def validate_input(user_id: int, message: str) -> Tuple[bool, str]:
        """Validates input for prompt injection and rate limits."""
        try:
            AISafetyGuard.check_rate_limit(user_id)
        except HTTPException as e:
            return False, e.detail

        is_safe, safety_msg = AISafetyGuard.validate_user_input(message)
        if not is_safe:
            return False, safety_msg

        return True, ""

    @staticmethod
    def sanitize_output(response_text: str) -> str:
        """Sanitizes model output to redact API keys, connection strings, or raw SQL."""
        clean = AISafetyGuard.sanitize_model_output(response_text)
        if re.search(r"\b(SELECT\s+.*\s+FROM|INSERT\s+INTO|DROP\s+TABLE|DELETE\s+FROM)\b", clean, re.IGNORECASE):
            clean = "The requested information has been verified and processed securely through official backend channels."
        return clean
