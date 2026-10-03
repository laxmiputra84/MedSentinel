from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import User
from app.schemas.eligibility import EligibilityEvaluationRequest
from app.services.eligibility_service import EligibilityService

def check_scheme_eligibility_tool(
    db: Session,
    user: User,
    income_level: Optional[str] = None,
    annual_income: Optional[float] = None,
    has_bpl_card: bool = False,
    is_formally_employed: bool = False,
    state: Optional[str] = None,
    age: Optional[int] = None
) -> Dict[str, Any]:
    """Evaluates user eligibility using the authoritative deterministic rules engine and returns structured rationales."""
    # Convert income to standardized level if annual income is given
    level = income_level or "medium"
    if annual_income is not None:
        if annual_income <= 250000:
            level = "low"
        elif annual_income <= 800000:
            level = "medium"
        else:
            level = "high"

    req = EligibilityEvaluationRequest(
        income=level,
        annual_income=annual_income,
        has_bpl_card=has_bpl_card,
        is_formally_employed=is_formally_employed,
        state=state,
        age=age
    )

    result = EligibilityService.evaluate_eligibility(db=db, request=req)

    return {
        "evaluation_summary": f"Found {len(result['eligible'])} pre-qualified schemes and {len(result['not_eligible'])} non-qualifying schemes.",
        "eligible_schemes": result["eligible"],
        "ineligible_schemes": result["not_eligible"],
        "user_parameters": {
            "income_level": level,
            "has_bpl_card": has_bpl_card,
            "is_formally_employed": is_formally_employed,
            "state": state
        },
        "authoritative_notice": "Determined via official government scheme criteria rules."
    }
