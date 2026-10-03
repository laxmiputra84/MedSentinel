from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.eligibility_service import EligibilityService
from app.schemas.eligibility import EligibilityRecommendationRequest

class EligibilityAgent:
    """
    Executes deterministic government scheme rules engine.
    LLM only explains results and provides guidance — LLM NEVER makes final qualification decisions.
    """
    @staticmethod
    async def evaluate_schemes(
        db: Session,
        annual_income: float = 200000.0,
        bpl_card: bool = True,
        state: str = "Karnataka",
        disability: bool = False
    ) -> Dict[str, Any]:
        income_tier = "bpl" if bpl_card or annual_income <= 250000 else "medium"
        req = EligibilityRecommendationRequest(
            income=income_tier,
            annual_income_inr=annual_income,
            has_bpl_card=bpl_card,
            state=state,
            has_critical_illness=disability
        )
        result = EligibilityService.evaluate_scheme_recommendations(
            db=db,
            data=req
        )
        return {
            "eligible_schemes": [
                {"name": s.scheme_name, "coverage": s.coverage, "match_score": s.match_score, "reason": s.reason}
                for s in result.eligible
            ],
            "ineligible_schemes": [
                {"name": s.scheme_name, "reason": s.reason}
                for s in result.not_eligible
            ],
            "evaluation_engine": result.evaluation_engine
        }
