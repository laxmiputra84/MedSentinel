"""
MedSentinel Agentic Architecture — Risk Prediction Agent
Computes health risk scores, abnormal test burdens, and claim fraud risks
using existing rule-based and ML scoring engines with transparent confidence.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding, WorkflowType, EscalationLevel
from app.agents.tools import calculate_health_risk_tool, detect_claim_fraud_tool


class RiskPredictionAgent(BaseAgent):
    """
    Specialized agent for composite health risk assessment and insurance claim risk scoring.
    """

    def __init__(self):
        super().__init__(
            name="risk_prediction",
            role="Health Risk & Claims Risk Scoring Engine",
            description="Evaluates composite medical risk scores and insurance fraud risk using multi-signal scoring algorithms.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        findings: List[ClinicalFinding] = []

        # 1. Branch A: Insurance Claim Workflow
        if state.workflow_type == WorkflowType.INSURANCE_CLAIM:
            claim_id = state.document_id or (context.get("claim_id") if context else None)
            if db and claim_id:
                fraud_res = await detect_claim_fraud_tool(db=db, claim_id=claim_id)
                state.fraud_result = fraud_res
                fraud_score = fraud_res.get("fraud_score", 0)
                fraud_risk = fraud_res.get("fraud_risk", "LOW")

                if fraud_risk in ["HIGH", "CRITICAL"]:
                    state.escalation_required = True
                    state.escalation_level = EscalationLevel.DOCTOR_REVIEW_REQUIRED
                    state.escalation_reason = f"High insurance fraud risk detected: score {fraud_score}/100."

                findings.append(
                    self.create_finding(
                        title=f"Insurance Claim Risk: {fraud_risk} (Score: {fraud_score}/100)",
                        description=f"Automated claims integrity audit completed. Flags: {'; '.join(fraud_res.get('flags', ['None']))}",
                        category="CLAIMS_RISK",
                        status="CRITICAL" if fraud_risk == "CRITICAL" else ("HIGH" if fraud_risk == "HIGH" else "NORMAL"),
                        is_critical=fraud_risk in ["HIGH", "CRITICAL"],
                        confidence=0.94
                    )
                )

                return AgentResult(
                    success=True,
                    agent_name=self.name,
                    data={"fraud_score": fraud_score, "fraud_risk": fraud_risk},
                    findings=findings
                )

        # 2. Branch B: Health Risk Scoring for Clinical / Lab Reports
        tests = state.lab_results or []
        risk_data = await calculate_health_risk_tool(tests)
        state.risk_result = risk_data

        health_score = risk_data["health_score"]
        risk_score = risk_data["risk_score"]
        risk_level = risk_data["risk_level"]
        abnormal_count = risk_data["abnormal_count"]

        if risk_level in ["HIGH", "CRITICAL"]:
            state.escalation_required = True
            if state.escalation_level != EscalationLevel.DOCTOR_REVIEW_REQUIRED:
                state.escalation_level = EscalationLevel.HIGH if risk_level == "HIGH" else EscalationLevel.DOCTOR_REVIEW_REQUIRED
            if not state.escalation_reason:
                state.escalation_reason = f"Elevated medical risk score: {risk_score}/100 ({risk_level} Risk Level)"

        findings.append(
            self.create_finding(
                title=f"Composite Medical Risk Score: {risk_score}/100 ({risk_level})",
                description=(
                    f"Health score assessed at {health_score}/100 with {abnormal_count} abnormal test parameters. "
                    "This is an algorithmic risk index for clinical decision-support and does not constitute a diagnosis."
                ),
                category="RISK_PREDICTION",
                status="CRITICAL" if risk_level == "CRITICAL" else ("HIGH" if risk_level == "HIGH" else "NORMAL"),
                is_critical=risk_level == "CRITICAL",
                confidence=0.95
            )
        )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "health_score": health_score,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "abnormal_count": abnormal_count,
            },
            findings=findings
        )
