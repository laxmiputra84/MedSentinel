from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.document import UserDocument
from app.models.recommendation import Recommendation
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationStatusUpdate,
    RelatedDocumentRecommendationResponse,
    RelatedDocumentItem,
)
from app.dependencies.auth import get_current_user
from app.services.recommendation_engine import RecommendationEngine
from app.services.content_recommender import ContentRecommender
from app.services.recommendation_rules import RELATED_DOCUMENT_RULES

router = APIRouter(prefix="/recommendations", tags=["Hybrid Recommendation System"])

ADMIN_ROLES = {"SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN"}


def _resolve_patient(db: Session, patient_id_param: str) -> Optional[Patient]:
    """Helper to resolve Patient record by id integer or patient_code string."""
    if not patient_id_param or patient_id_param.lower() in ("me", "current", "self", "user"):
        return None
    if patient_id_param.isdigit():
        pat = db.query(Patient).filter(Patient.id == int(patient_id_param)).first()
        if pat:
            return pat
    return db.query(Patient).filter(Patient.patient_code == patient_id_param).first()

@router.get("", response_model=List[RecommendationResponse])
def get_recommendations(
    status: Optional[str] = Query(None, description="ACTIVE, VIEWED, DISMISSED, COMPLETED"),
    recommendation_type: Optional[str] = Query(None, description="Filter by type"),
    priority: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FEATURE 21: Retrieve personalized recommendations for the authenticated user.
    Admins can view all recommendations.
    """
    query = db.query(Recommendation)

    if current_user.role not in ADMIN_ROLES:
        query = query.filter(Recommendation.user_id == current_user.id)

    if status:
        query = query.filter(Recommendation.status == status.upper())
    if recommendation_type:
        query = query.filter(Recommendation.recommendation_type == recommendation_type.upper())
    if priority:
        query = query.filter(Recommendation.priority == priority.upper())

    results = query.order_by(Recommendation.created_at.desc()).all()

    # If user has zero recommendations, trigger automatic hybrid generation
    if not results and current_user.role not in ADMIN_ROLES:
        results = RecommendationEngine.generate_hybrid_recommendations(db, current_user.id)
        if status:
            results = [r for r in results if r.status == status.upper()]

    return results


@router.get("/{patient_id}", response_model=List[RecommendationResponse])
def get_patient_recommendations(
    patient_id: str,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve recommendations for a specific patient.
    Enforces patient ownership and RBAC authorization.
    """
    patient = _resolve_patient(db, patient_id)
    if not patient:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

    if not patient:
        return []

    # Ownership / authorization check
    if current_user.role not in ADMIN_ROLES and patient.user_id != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only access your own patient recommendations.",
        )

    query = db.query(Recommendation).filter(
        (Recommendation.patient_id == patient.id) |
        (Recommendation.user_id == patient.user_id)
    )

    if status:
        query = query.filter(Recommendation.status == status.upper())

    recs = query.order_by(Recommendation.created_at.desc()).all()
    if not recs:
        recs = RecommendationEngine.generate_hybrid_recommendations(
            db, user_id=patient.user_id, patient_id=patient.id
        )
        if status:
            recs = [r for r in recs if r.status == status.upper()]

    return recs


@router.post("/generate", response_model=List[RecommendationResponse])
@router.post("/generate/{patient_id}", response_model=List[RecommendationResponse])
def generate_patient_recommendations(
    patient_id: str = "me",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger on-demand generation of explainable hybrid recommendations for a patient.
    """
    patient = _resolve_patient(db, patient_id) if patient_id != "me" else None
    if not patient:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

    if not patient:
        # Create minimal patient container if user has none
        patient = Patient(
            user_id=current_user.id,
            patient_code=f"MS-2026-{current_user.id:05d}",
            name=current_user.name,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

    # Ownership check: if normal user and resolved patient is not theirs, fallback to their patient
    if current_user.role not in ADMIN_ROLES and patient.user_id != current_user.id:
        user_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if user_patient:
            patient = user_patient
        else:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Cannot generate recommendations for another user's patient profile.",
            )

    return RecommendationEngine.generate_hybrid_recommendations(
        db=db, user_id=patient.user_id, patient_id=patient.id
    )


@router.patch("/{recommendation_id}/status", response_model=RecommendationResponse)
def update_recommendation_status(
    recommendation_id: int,
    payload: RecommendationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update recommendation status: ACTIVE, VIEWED, DISMISSED, or COMPLETED.
    """
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Recommendation record not found",
        )

    # Ownership check
    if current_user.role not in ADMIN_ROLES and rec.user_id != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot modify another user's recommendations.",
        )

    rec.status = payload.status
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/{patient_id}/related-documents", response_model=RelatedDocumentRecommendationResponse)
def get_related_documents_recommendations(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FEATURE 10: Content-based document recommendations via TF-IDF & Cosine Similarity.
    """
    patient = _resolve_patient(db, patient_id)
    target_user_id = patient.user_id if patient else current_user.id

    if current_user.role not in ADMIN_ROLES and target_user_id != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view document linkages for another patient.",
        )

    docs = db.query(UserDocument).filter(UserDocument.user_id == target_user_id).all()
    if not docs:
        return RelatedDocumentRecommendationResponse(
            patient_id=patient.id if patient else None,
            related_documents=[],
        )

    related_items: List[RelatedDocumentItem] = []
    # Rank candidates against each other
    for doc in docs:
        candidates = [d for d in docs if d.id != doc.id]
        ranked = ContentRecommender.get_related_content_scores(doc, candidates)
        if ranked:
            top = ranked[0]
            actions = RELATED_DOCUMENT_RULES.get(doc.doc_type, ["Supporting Medical Record"])
            related_items.append(
                RelatedDocumentItem(
                    document_id=top["document_id"],
                    document_code=top.get("document_code"),
                    original_name=top["original_name"],
                    doc_type=top["doc_type"],
                    similarity=top["similarity"],
                    suggested_actions=actions,
                )
            )

    return RelatedDocumentRecommendationResponse(
        patient_id=patient.id if patient else None,
        related_documents=related_items,
    )
