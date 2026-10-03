from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.insurance_claim import InsuranceClaim
from app.models.claim_history import ClaimStatusHistory
from app.models.user import User
from app.services.notification_service import NotificationService

VALID_STATUSES = [
    "SUBMITTED",
    "UNDER_REVIEW",
    "DOCUMENTS_REQUIRED",
    "APPROVED",
    "REJECTED",
    "COMPLETED"
]

class ClaimService:
    @staticmethod
    def create_claim(
        db: Session,
        user_id: int,
        insurance_id: Optional[int],
        hospital_id: Optional[int],
        claim_amount: float,
        claim_description: Optional[str],
        documents: Optional[str] = None
    ) -> InsuranceClaim:
        new_claim = InsuranceClaim(
            user_id=user_id,
            insurance_id=insurance_id,
            hospital_id=hospital_id,
            claim_amount=claim_amount,
            claim_description=claim_description,
            documents=documents,
            claim_status="SUBMITTED"
        )
        db.add(new_claim)
        db.commit()
        db.refresh(new_claim)

        # Log initial history
        history = ClaimStatusHistory(
            claim_id=new_claim.id,
            previous_status=None,
            new_status="SUBMITTED",
            updated_by_id=user_id,
            comment="Claim submitted by user"
        )
        db.add(history)
        db.commit()

        # Send notification to user
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            title="Insurance Claim Submitted",
            message=f"Your claim #{new_claim.id} for ₹{claim_amount:,.2f} has been submitted and is under processing.",
            type="claim"
        )

        return new_claim

    @staticmethod
    def update_claim_status(
        db: Session,
        claim_id: int,
        new_status: str,
        admin_user: User,
        comment: Optional[str] = None
    ) -> InsuranceClaim:
        norm_status = new_status.upper().strip()
        if norm_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid claim status '{new_status}'. Allowed: {', '.join(VALID_STATUSES)}"
            )

        claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
        if not claim:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")

        prev_status = claim.claim_status
        claim.claim_status = norm_status

        # Create history record
        history = ClaimStatusHistory(
            claim_id=claim.id,
            previous_status=prev_status,
            new_status=norm_status,
            updated_by_id=admin_user.id,
            comment=comment or f"Status changed from {prev_status} to {norm_status}"
        )
        db.add(history)
        db.commit()
        db.refresh(claim)

        # Notify user
        status_messages = {
            "UNDER_REVIEW": f"Your claim #{claim.id} is now under review by the insurer.",
            "DOCUMENTS_REQUIRED": f"Additional documents are required for your claim #{claim.id}. {comment or ''}",
            "APPROVED": f"Congratulations! Your claim #{claim.id} for ₹{claim.claim_amount:,.2f} has been approved.",
            "REJECTED": f"Your claim #{claim.id} was rejected. Reason: {comment or 'Eligibility criteria not met'}.",
            "COMPLETED": f"Your claim #{claim.id} payout has been processed and completed."
        }

        NotificationService.create_notification(
            db=db,
            user_id=claim.user_id,
            title=f"Claim #{claim.id} Status: {norm_status}",
            message=status_messages.get(norm_status, f"Claim status updated to {norm_status}"),
            type="claim"
        )

        return claim

    @staticmethod
    def get_user_claims(db: Session, user_id: int) -> List[InsuranceClaim]:
        return db.query(InsuranceClaim).filter(
            InsuranceClaim.user_id == user_id
        ).order_by(InsuranceClaim.claim_date.desc()).all()

    @staticmethod
    def get_claim_by_id(db: Session, claim_id: int, user_id: Optional[int] = None) -> Optional[InsuranceClaim]:
        query = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id)
        if user_id is not None:
            query = query.filter(InsuranceClaim.user_id == user_id)
        return query.first()

