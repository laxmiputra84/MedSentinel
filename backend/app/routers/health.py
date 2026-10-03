from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.document import UserDocument
from app.models.lab_result import LabResult
from app.models.health_score import HealthScore
from app.schemas.health_analysis import HealthScoreResponse, HealthDashboardResponse
from app.schemas.lab_result import LabTestItem
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/health", tags=["Health Intelligence & Trends"])

@router.get("/trends/{patient_id}", response_model=Dict[str, List[Dict[str, Any]]])
def get_patient_laboratory_trends(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FEATURE 6: Retrieve historical laboratory values for trends over time.
    Tracks values such as: Hemoglobin, WBC, Platelets, Blood Glucose, HbA1c, Creatinine, CRP.
    """
    # Resolve patient by ID or patient_code or fallback to current user's patient
    patient = None
    if patient_id.isdigit():
        patient = db.query(Patient).filter(Patient.id == int(patient_id)).first()
    if not patient:
        patient = db.query(Patient).filter(Patient.patient_code == patient_id).first()
    if not patient:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

    if not patient:
        # If no patient record exists yet, return empty trends
        return {}

    # Query all lab results for patient ordered by date
    results = db.query(LabResult).filter(
        LabResult.patient_id == patient.id
    ).order_by(LabResult.test_date.asc()).all()

    trends: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        tname = r.test_name
        if tname not in trends:
            trends[tname] = []
        d_str = r.test_date.strftime("%Y-%m-%d") if r.test_date else datetime.utcnow().strftime("%Y-%m-%d")
        trends[tname].append({
            "date": d_str,
            "value": r.observed_value,
            "status": r.status,
            "unit": r.unit,
            "reference_min": r.reference_min,
            "reference_max": r.reference_max,
        })

    return trends

@router.get("/dashboard", response_model=HealthDashboardResponse)
def get_health_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FEATURE 10 & 11: Medical Dashboard metrics, risk indicators, critical alerts, and laboratory trends.
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

    # Total Documents
    total_docs = db.query(UserDocument).filter(UserDocument.user_id == current_user.id).count()

    # Latest Lab Reports
    lab_docs_count = db.query(UserDocument).filter(
        UserDocument.user_id == current_user.id,
        UserDocument.doc_type == "Lab Report"
    ).count()

    normal_count = 0
    abnormal_count = 0
    critical_count = 0
    critical_alerts: List[LabTestItem] = []
    trends: Dict[str, List[Dict[str, Any]]] = {}

    if patient:
        all_results = db.query(LabResult).filter(LabResult.patient_id == patient.id).order_by(LabResult.test_date.asc()).all()
        for r in all_results:
            st = (r.status or "NORMAL").upper()
            if st == "CRITICAL" or r.is_critical:
                critical_count += 1
                critical_alerts.append(LabTestItem(
                    name=r.test_name,
                    value=r.observed_value,
                    unit=r.unit,
                    reference_min=r.reference_min,
                    reference_max=r.reference_max,
                    status="CRITICAL",
                    is_critical=True,
                ))
            elif st in ["HIGH", "LOW"]:
                abnormal_count += 1
            else:
                normal_count += 1

            # Populate trends
            if r.test_name not in trends:
                trends[r.test_name] = []
            d_str = r.test_date.strftime("%Y-%m-%d") if r.test_date else datetime.utcnow().strftime("%Y-%m-%d")
            trends[r.test_name].append({
                "date": d_str,
                "value": r.observed_value,
                "status": r.status,
                "unit": r.unit,
                "reference_min": r.reference_min,
                "reference_max": r.reference_max,
            })

    # Latest Health & Risk Score
    latest_score_rec = None
    if patient:
        latest_score_rec = db.query(HealthScore).filter(
            HealthScore.patient_id == patient.id
        ).order_by(HealthScore.calculated_at.desc()).first()

    health_score = latest_score_rec.health_score if latest_score_rec else 85
    risk_score = latest_score_rec.risk_score if latest_score_rec else 15
    risk_level = latest_score_rec.risk_level if latest_score_rec else "LOW"
    ai_summary = latest_score_rec.ai_summary if latest_score_rec else (
        "AI HEALTH SUMMARY\n\n"
        "Routine health records indicate stable baseline indicators.\n\n"
        "Important:\n"
        "This analysis is for informational and decision-support purposes only. "
        "It does not provide a medical diagnosis. "
        "Please consult a qualified healthcare professional."
    )

    return HealthDashboardResponse(
        total_documents=total_docs,
        latest_lab_reports_count=lab_docs_count,
        normal_results_count=normal_count,
        abnormal_results_count=abnormal_count,
        critical_results_count=critical_count,
        health_score=health_score,
        risk_score=risk_score,
        risk_level=risk_level,
        critical_alerts=critical_alerts,
        ai_summary=ai_summary,
        trends=trends,
    )

@router.get("/latest-score", response_model=HealthScoreResponse)
def get_latest_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FEATURE 4 & 5: Get latest calculated Health Score, Risk Level, and AI Health Summary.
    """
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return HealthScoreResponse(
            health_score=85,
            risk_score=15,
            risk_level="LOW",
            abnormal_tests=0,
            ai_summary=(
                "AI HEALTH SUMMARY\n\n"
                "No abnormal laboratory markers recorded.\n\n"
                "Important:\n"
                "This analysis is for informational and decision-support purposes only. "
                "It does not provide a medical diagnosis. "
                "Please consult a qualified healthcare professional."
            ),
        )

    score_rec = db.query(HealthScore).filter(
        HealthScore.patient_id == patient.id
    ).order_by(HealthScore.calculated_at.desc()).first()

    if not score_rec:
        return HealthScoreResponse(
            health_score=85,
            risk_score=15,
            risk_level="LOW",
            abnormal_tests=0,
            ai_summary="Upload a laboratory report to generate an automated health analysis.",
        )

    return HealthScoreResponse(
        health_score=score_rec.health_score,
        risk_score=score_rec.risk_score,
        risk_level=score_rec.risk_level,
        abnormal_tests=score_rec.abnormal_tests,
        ai_summary=score_rec.ai_summary,
    )
