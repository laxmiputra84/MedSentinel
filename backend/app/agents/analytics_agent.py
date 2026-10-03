from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.analytics_service import AnalyticsService

class AnalyticsAgent:
    """
    Synthesizes aggregated platform metrics exclusively for authorized administrators.
    """
    @staticmethod
    async def get_aggregated_analytics(user_role: str, db: Session) -> Dict[str, Any]:
        if user_role not in ["SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN"]:
            return {"error": "UNAUTHORIZED_ANALYTICS_ACCESS"}

        overview = AnalyticsService.get_platform_analytics(db=db)
        return {
            "total_users": overview.total_users,
            "total_hospitals": overview.total_hospitals,
            "total_claims": overview.total_claims,
            "approved_claims": overview.approved_claims,
            "total_claims_amount": overview.total_claims_amount
        }
