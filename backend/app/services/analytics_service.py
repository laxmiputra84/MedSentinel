from datetime import datetime, timezone, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.hospital import Hospital
from app.models.appointment import Appointment
from app.models.insurance import Insurance
from app.models.user_insurance import UserInsurance
from app.models.insurance_claim import InsuranceClaim
from app.schemas.analytics import (
    PlatformAnalyticsResponse,
    HospitalAnalyticsResponse,
    InsuranceAnalyticsResponse,
)

class AnalyticsService:
    @staticmethod
    def get_platform_analytics(db: Session) -> PlatformAnalyticsResponse:
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_hospitals = db.query(func.count(Hospital.id)).scalar() or 0
        total_appointments = db.query(func.count(Appointment.id)).scalar() or 0
        total_insurance_policies = db.query(func.count(UserInsurance.id)).scalar() or 0
        
        # Claims metrics
        total_claims = db.query(func.count(InsuranceClaim.id)).scalar() or 0
        approved_claims = db.query(func.count(InsuranceClaim.id)).filter(InsuranceClaim.claim_status == "APPROVED").scalar() or 0
        rejected_claims = db.query(func.count(InsuranceClaim.id)).filter(InsuranceClaim.claim_status == "REJECTED").scalar() or 0
        under_review_claims = db.query(func.count(InsuranceClaim.id)).filter(InsuranceClaim.claim_status.in_(["SUBMITTED", "UNDER_REVIEW", "DOCUMENTS_REQUIRED"])).scalar() or 0
        total_claims_amount = db.query(func.sum(InsuranceClaim.claim_amount)).scalar() or 0.0

        return PlatformAnalyticsResponse(
            total_users=total_users,
            total_hospitals=total_hospitals,
            total_appointments=total_appointments,
            total_insurance_policies=total_insurance_policies,
            total_claims=total_claims,
            approved_claims=approved_claims,
            rejected_claims=rejected_claims,
            under_review_claims=under_review_claims,
            total_claims_amount=float(total_claims_amount),
            recent_users_count=total_users
        )

    @staticmethod
    def get_hospital_analytics(db: Session, hospital_id: int) -> HospitalAnalyticsResponse:
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        hospital_name = hospital.name if hospital else f"Hospital #{hospital_id}"

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        base_query = db.query(Appointment)
        if hospital_id:
            base_query = base_query.filter(Appointment.hospital_id == hospital_id)

        today_appointments = base_query.filter(Appointment.preferred_date == today_str).count()
        upcoming_appointments = base_query.filter(Appointment.status == "CONFIRMED").count()
        completed_appointments = base_query.filter(Appointment.status == "COMPLETED").count()
        cancelled_appointments = base_query.filter(Appointment.status == "CANCELLED").count()

        # Department distribution
        dept_counts = db.query(
            Appointment.department, func.count(Appointment.id)
        ).group_by(Appointment.department).all()

        dept_dist = {dept: count for dept, count in dept_counts if dept}

        return HospitalAnalyticsResponse(
            hospital_id=hospital_id,
            hospital_name=hospital_name,
            today_appointments=today_appointments,
            upcoming_appointments=upcoming_appointments,
            completed_appointments=completed_appointments,
            cancelled_appointments=cancelled_appointments,
            department_distribution=dept_dist
        )

    @staticmethod
    def get_insurance_analytics(db: Session) -> InsuranceAnalyticsResponse:
        total_plans = db.query(func.count(Insurance.id)).scalar() or 0
        total_enrolled = db.query(func.count(UserInsurance.id)).scalar() or 0
        total_claims = db.query(func.count(InsuranceClaim.id)).scalar() or 0

        under_review = db.query(func.count(InsuranceClaim.id)).filter(InsuranceClaim.claim_status == "UNDER_REVIEW").scalar() or 0
        approved = db.query(func.count(InsuranceClaim.id)).filter(InsuranceClaim.claim_status == "APPROVED").scalar() or 0
        rejected = db.query(func.count(InsuranceClaim.id)).filter(InsuranceClaim.claim_status == "REJECTED").scalar() or 0
        doc_req = db.query(func.count(InsuranceClaim.id)).filter(InsuranceClaim.claim_status == "DOCUMENTS_REQUIRED").scalar() or 0

        total_payout = db.query(func.sum(InsuranceClaim.claim_amount)).filter(InsuranceClaim.claim_status.in_(["APPROVED", "COMPLETED"])).scalar() or 0.0

        return InsuranceAnalyticsResponse(
            total_plans=total_plans,
            total_active_enrolled_policies=total_enrolled,
            total_claims=total_claims,
            claims_under_review=under_review,
            approved_claims=approved,
            rejected_claims=rejected,
            documents_required_claims=doc_req,
            total_payout_amount=float(total_payout)
        )
