"""
MedSentinel Agentic Architecture — Lab Analysis Agent (CORE FEATURE)
Deep laboratory diagnostics extracting clinical parameters, evaluating against
standard biological reference ranges, detecting panic/critical thresholds,
and identifying abnormal clinical patterns with evidence.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding, LabFinding, EscalationLevel
from app.agents.tools import analyze_lab_data_tool, evaluate_lab_parameter_tool


class LabAnalysisAgent(BaseAgent):
    """
    Core specialized agent for extracting laboratory tests, evaluating standard reference ranges,
    and classifying values as NORMAL, LOW, HIGH, or CRITICAL.
    """

    def __init__(self):
        super().__init__(
            name="lab_analysis",
            role="Laboratory Data Extraction & Reference Range Evaluation",
            description="Parses structured laboratory results, compares observed values against biological intervals, and flags critical clinical panic values.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        text = state.extracted_text or (context.get("text") if context else "") or ""

        if not text.strip():
            return AgentResult(
                success=False,
                agent_name=self.name,
                errors=["No clinical text available for laboratory analysis."]
            )

        # 1. Call Lab Extraction Tool
        lab_data = await analyze_lab_data_tool(text)
        tests = lab_data.get("tests", [])

        # Update patient name/id in state if discovered from report header
        if lab_data.get("patient_name") and not state.patient_name:
            state.patient_name = lab_data["patient_name"]

        state.lab_results = tests
        state.extracted_entities["lab_data"] = {
            "patient_name": lab_data.get("patient_name"),
            "patient_id": lab_data.get("patient_id"),
            "report_date": lab_data.get("report_date"),
            "tests_count": len(tests)
        }

        findings: List[ClinicalFinding] = []
        lab_findings: List[LabFinding] = []
        critical_tests: List[Dict[str, Any]] = []
        abnormal_tests: List[Dict[str, Any]] = []

        for t in tests:
            name = t["name"]
            val = t["value"]
            unit = t["unit"]
            ref_min = t.get("reference_min")
            ref_max = t.get("reference_max")
            status = t.get("status", "NORMAL")
            is_critical = t.get("is_critical", False)

            ref_str = f"[{ref_min} - {ref_max}]" if ref_min is not None and ref_max is not None else "Standard range"
            evidence_str = f"Observed: {val} {unit} | Reference Range: {ref_str} | Status: {status}"

            lab_finding = LabFinding(
                test_name=name,
                observed_value=val,
                unit=unit,
                reference_min=ref_min,
                reference_max=ref_max,
                status=status,
                is_critical=is_critical,
                evidence=evidence_str
            )
            lab_findings.append(lab_finding)

            if status != "NORMAL":
                abnormal_tests.append(t)
                severity_cat = "BIOCHEMISTRY"
                if name in ["Hemoglobin", "WBC", "Platelets", "RBC Count", "PCV", "Neutrophils", "Lymphocytes"]:
                    severity_cat = "HEMATOLOGY"

                findings.append(
                    self.create_finding(
                        title=f"{name}: {status} ({val} {unit})",
                        description=f"{name} measured at {val} {unit}, which is outside reference interval {ref_str}.",
                        category=severity_cat,
                        parameter_name=name,
                        observed_value=val,
                        reference_range=ref_str,
                        unit=unit,
                        status=status,
                        is_critical=is_critical,
                        evidence=evidence_str,
                        confidence=0.96
                    )
                )

            if is_critical:
                critical_tests.append(t)

        # 2. Critical panic threshold escalation handling
        if critical_tests:
            crit_names = [f"{t['name']} ({t['value']} {t['unit']})" for t in critical_tests]
            state.escalation_required = True
            state.escalation_level = EscalationLevel.DOCTOR_REVIEW_REQUIRED
            state.escalation_reason = f"Critical panic value detected: {', '.join(crit_names)}"

            findings.append(
                self.create_finding(
                    title="CRITICAL PANIC VALUE ALERT",
                    description=(
                        f"One or more parameters reached critical medical thresholds: {', '.join(crit_names)}. "
                        "Immediate human/doctor clinical review is required."
                    ),
                    category="CRITICAL_ALERT",
                    status="CRITICAL",
                    is_critical=True,
                    confidence=0.99
                )
            )

        if not abnormal_tests and tests:
            findings.append(
                self.create_finding(
                    title="All Laboratory Parameters Within Reference Range",
                    description=f"All {len(tests)} tested parameters are within standard biological reference ranges.",
                    category="HEMATOLOGY",
                    status="NORMAL",
                    confidence=0.95
                )
            )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "total_tests": len(tests),
                "abnormal_count": len(abnormal_tests),
                "critical_count": len(critical_tests),
                "escalation_required": state.escalation_required,
            },
            findings=findings
        )
