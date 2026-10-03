"""
MedSentinel Agentic Architecture — Data Validation Agent
Validates extracted clinical records for physiological impossibility, negative values,
missing mandatory fields, and format anomalies without inventing missing data.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, EscalationLevel
from app.agents.tools import validate_clinical_data_tool


class DataValidationAgent(BaseAgent):
    """
    Specialized agent for clinical sanity checking and physiological boundary verification.
    """

    def __init__(self):
        super().__init__(
            name="data_validation",
            role="Clinical Data Sanity & Validation",
            description="Performs physiological bounds validation, detects impossible/corrupt parameters, and enforces data integrity.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        tests = state.lab_results or []
        findings = []

        # If no tests exist yet, check extracted entities
        if not tests and state.extracted_entities.get("tests"):
            tests = state.extracted_entities["tests"]

        if not tests:
            # Nothing clinical to validate in this document
            state.validation_status = {"status": "SKIPPED_NO_CLINICAL_VALUES", "valid": True}
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={"status": "NO_CLINICAL_TESTS_TO_VALIDATE"}
            )

        # Call Clinical Data Validation Tool
        val_res = await validate_clinical_data_tool(tests)
        is_valid = val_res["is_valid"]
        valid_tests = val_res["valid_tests"]
        errors = val_res["errors"]
        warnings = val_res["warnings"]

        state.validation_status = {
            "is_valid": is_valid,
            "total_extracted": val_res["total_extracted"],
            "valid_count": val_res["valid_count"],
        }
        state.validation_errors = errors
        state.validation_warnings = warnings

        # Filter out corrupt/unparseable items from state.lab_results
        state.lab_results = valid_tests

        if errors:
            state.escalation_required = True
            state.escalation_level = EscalationLevel.DOCTOR_REVIEW_REQUIRED
            if not state.escalation_reason:
                state.escalation_reason = f"Data validation detected corrupt/impossible clinical values: {'; '.join(errors)}"

            findings.append(
                self.create_finding(
                    title="Data Validation Anomaly Detected",
                    description=f"Physiological inconsistency flagged: {'; '.join(errors)}",
                    category="DATA_INTEGRITY",
                    status="CRITICAL",
                    is_critical=True,
                    confidence=0.99
                )
            )

        if warnings:
            for w in warnings:
                findings.append(
                    self.create_finding(
                        title="Clinical Value Warning",
                        description=w,
                        category="DATA_INTEGRITY",
                        status="HIGH",
                        is_critical=False,
                        confidence=0.92
                    )
                )

        if is_valid and not errors:
            findings.append(
                self.create_finding(
                    title="Clinical Data Integrity Confirmed",
                    description=f"All {len(valid_tests)} extracted parameters satisfy physiological sanity bounds.",
                    category="DATA_INTEGRITY",
                    status="NORMAL",
                    confidence=0.98
                )
            )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "is_valid": is_valid,
                "valid_count": len(valid_tests),
                "error_count": len(errors),
                "warning_count": len(warnings),
            },
            findings=findings
        )
