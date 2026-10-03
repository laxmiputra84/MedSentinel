from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import User, Insurance, UserInsurance

def search_insurance_plans_tool(
    db: Session,
    user: User,
    provider: Optional[str] = None,
    coverage_type: Optional[str] = None,
    max_monthly_premium: Optional[float] = None
) -> Dict[str, Any]:
    """Search and compare active insurance plans and benefits."""
    query = db.query(Insurance)
    if provider:
        query = query.filter(Insurance.provider.ilike(f"%{provider}%"))
    if coverage_type:
        query = query.filter(Insurance.coverage_type.ilike(f"%{coverage_type}%"))
    if max_monthly_premium:
        query = query.filter(Insurance.premium_monthly <= max_monthly_premium)

    plans = query.all()

    items = []
    for p in plans:
        items.append({
            "id": p.id,
            "name": p.name,
            "provider": p.provider,
            "coverage_amount": p.coverage_amount,
            "premium_monthly": p.premium_monthly,
            "premium_annual": p.premium_annual,
            "cashless_network_hospitals": p.cashless_network,
            "claim_settlement_days": p.claim_settlement_days,
            "rating": p.rating,
            "features": p.features,
            "inclusions": p.inclusions,
            "exclusions": p.exclusions
        })

    # Also check if user has active policies
    user_policies = db.query(UserInsurance).filter(UserInsurance.user_id == user.id).all()
    enrolled = [
        {
            "policy_number": up.policy_number,
            "plan_name": up.insurance.name if up.insurance else "Custom Policy",
            "sum_insured": up.sum_insured,
            "status": up.status
        }
        for up in user_policies
    ]

    return {
        "available_plans_count": len(items),
        "plans": items,
        "user_active_enrolled_policies": enrolled
    }
