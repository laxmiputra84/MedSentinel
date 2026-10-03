from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.claim_service import ClaimService
from app.models.insurance_claim import InsuranceClaim

class ClaimsAgent:
    """
    Retrieves and summarizes insurance claims strictly authorized for the authenticated user.
    Prevents cross-user claim data leakage.
    """
    @staticmethod
    async def get_user_claims_data(user_id: int, user_role: str, db: Session) -> Dict[str, Any]:
        if user_role == "SUPER_ADMIN" or user_role == "INSURANCE_ADMIN":
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
                "description": c.claim_description
            })

        return {
            "claims": items,
            "total": len(items)
        }
