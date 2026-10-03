from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import require_super_admin
from app.models import User, Hospital, InsuranceClaim, Appointment, UserDocument
from app.ai.agent import AIAgentService

router = APIRouter(prefix="/admin/ai-insights", tags=["Admin - AI Insights"])

@router.get("")
async def get_admin_ai_insights(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """
    Generates AI operational summaries and bottleneck detection based on aggregated platform data.
    Ensures no raw patient PII or restricted credentials are transmitted.
    """
    # Aggregate platform performance metrics
    total_users = db.query(User).count()
    total_hospitals = db.query(Hospital).count()
    total_claims = db.query(InsuranceClaim).count()
    approved_claims = db.query(InsuranceClaim).filter(InsuranceClaim.claim_status == "APPROVED").count()
    rejected_claims = db.query(InsuranceClaim).filter(InsuranceClaim.claim_status == "REJECTED").count()
    pending_claims = db.query(InsuranceClaim).filter(InsuranceClaim.claim_status.in_(["SUBMITTED", "UNDER_REVIEW", "DOCUMENTS_REQUIRED"])).count()
    total_appointments = db.query(Appointment).count()
    pending_documents = db.query(UserDocument).filter(UserDocument.status == "PENDING").count()

    stats = {
        "total_users": total_users,
        "total_hospitals": total_hospitals,
        "total_claims": total_claims,
        "approved_claims": approved_claims,
        "rejected_claims": rejected_claims,
        "pending_claims": pending_claims,
        "total_appointments": total_appointments,
        "pending_documents": pending_documents
    }

    summary = await AIAgentService.generate_admin_insights(stats)

    return {
        "summary": summary,
        "aggregated_metrics": stats,
        "generated_at": "Just now",
        "badge": "AI-Generated Operational Summary"
    }
