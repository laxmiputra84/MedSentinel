from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import User, InsuranceClaim, ClaimStatusHistory
from app.services.claim_service import ClaimService

def get_user_claims_tool(
    db: Session,
    user: User,
    claim_id: Optional[int] = None
) -> Dict[str, Any]:
    """Retrieve insurance claims belonging exclusively to the authenticated user."""
    query = db.query(InsuranceClaim).filter(InsuranceClaim.user_id == user.id)
    if claim_id:
        query = query.filter(InsuranceClaim.id == claim_id)

    claims = query.order_by(InsuranceClaim.claim_date.desc()).all()

    results = []
    for c in claims:
        # Fetch status timeline
        timeline = db.query(ClaimStatusHistory).filter(
            ClaimStatusHistory.claim_id == c.id
        ).order_by(ClaimStatusHistory.created_at.desc()).all()

        timeline_events = [
            {
                "new_status": h.new_status,
                "previous_status": h.previous_status,
                "comment": h.comment,
                "timestamp": h.created_at.isoformat() if h.created_at else None
            }
            for h in timeline
        ]

        results.append({
            "claim_id": c.id,
            "amount": c.claim_amount,
            "status": c.claim_status,
            "date": c.claim_date.isoformat() if c.claim_date else None,
            "description": c.claim_description,
            "hospital_name": c.hospital.name if c.hospital else "Unspecified Hospital",
            "insurance_plan": c.insurance.name if c.insurance else "Unspecified Insurance",
            "timeline_history": timeline_events,
            "status_explanation": _get_status_guidance(c.claim_status)
        })

    return {
        "user_email": user.email,
        "claims_count": len(results),
        "claims": results
    }

def _get_status_guidance(status: str) -> str:
    guidance_map = {
        "SUBMITTED": "Your claim has been securely received and is awaiting initial medical underwriter assignment.",
        "UNDER_REVIEW": "Insurance underwriters and medical auditors are evaluating the clinical diagnostics and hospital invoices.",
        "DOCUMENTS_REQUIRED": "Additional documentation (e.g. original discharge summary, diagnostic reports, or pharmacy receipts) is required.",
        "APPROVED": "Your claim has been authorized for direct cashless settlement or reimbursement disbursement.",
        "REJECTED": "The claim was denied based on policy waiting periods, excluded procedures, or non-covered consumables.",
        "COMPLETED": "Financial transfer and settlement completed to the hospital/patient account."
    }
    return guidance_map.get(status, "Status is being processed.")
