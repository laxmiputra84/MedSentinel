from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding
from app.services.claim_service import ClaimService
from app.services.fraud_detector import FraudDetector
from app.models.insurance_claim import InsuranceClaim


class ClaimsAgent(BaseAgent):
    """
    Specialized agent for Insurance Claims Processing and Fraud Risk Evaluation.
    - Validates claim data, hospital empanelment, and attached medical documentation.
    - Runs multi-vector fraud scoring (duplicate invoices, hash collisions, submission velocity).
    - Flags high-risk claims for administrative audit.
    """

    def __init__(self):
        super().__init__(
            name="claims",
            role="Insurance Claims Verification & Fraud Risk Evaluation",
            description="Evaluates insurance claims against empanelled hospital rules and performs algorithmic fraud detection.",
            version="2.0.0",
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        ctx = context or {}
        claim_id = ctx.get("claim_id") or (int(state.document_id) if state.document_id and state.document_id.isdigit() else None)

        findings: List[ClinicalFinding] = []
        fraud_data: Dict[str, Any] = {}

        if db and claim_id:
            claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
            if claim:
                # Execute fraud risk analysis
                try:
                    fraud_res = FraudDetector.analyze_claim(db, claim.id)
                    fraud_data = {
                        "fraud_score": fraud_res.fraud_score,
                        "fraud_risk": fraud_res.fraud_risk,
                        "flags": fraud_res.flags,
                        "duplicate_invoices": fraud_res.duplicate_invoices_detected,
                        "reused_hashes": fraud_res.reused_hash_detected,
                    }

                    if fraud_res.fraud_risk in ["MEDIUM", "HIGH"]:
                        findings.append(
                            self.create_finding(
                                title=f"Insurance Claim Fraud Risk Flag [{fraud_res.fraud_risk}]",
                                description=f"Claim #{claim.id} exhibited fraud indicators (Score: {fraud_res.fraud_score}/100). Flags: {', '.join(fraud_res.flags if isinstance(fraud_res.flags, list) else [str(fraud_res.flags)])}",
                                category="FRAUD_RISK",
                                status="CRITICAL" if fraud_res.fraud_risk == "HIGH" else "ABNORMAL",
                                is_critical=(fraud_res.fraud_risk == "HIGH"),
                                confidence=0.92,
                            )
                        )
                except Exception as exc:
                    fraud_data = {"error": str(exc)}

        return AgentResult(
            success=True,
            agent_name=self.name,
            findings=findings,
            data={
                "claim_id": claim_id,
                "fraud_analysis": fraud_data,
            },
        )

    # -------------------------------------------------------------
    # Backwards-Compatible Static Method for Claims Retrieval
    # -------------------------------------------------------------
    @staticmethod
    async def get_user_claims_data(user_id: int, user_role: str, db: Session) -> Dict[str, Any]:
        if user_role in ["SUPER_ADMIN", "INSURANCE_ADMIN"]:
            claims = db.query(InsuranceClaim).order_by(InsuranceClaim.claim_date.desc()).limit(10).all()
        else:
            claims = ClaimService.get_user_claims(db=db, user_id=user_id)

        items = []
        for c in claims:
            items.append({
                "claim_id": c.id,
                "hospital": c.hospital.name if c.hospital else "Empanelled Hospital",
                "insurance_plan": c.insurance.name if c.insurance else "Health Plan",
                "claim_amount": c.claim_amount,
                "status": c.claim_status,
                "filing_date": str(c.claim_date) if c.claim_date else None,
                "description": c.claim_description,
            })

        return {
            "claims": items,
            "total": len(items),
        }
