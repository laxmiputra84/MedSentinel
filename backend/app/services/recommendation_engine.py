"""
MedSentinel Hybrid Recommendation Engine
Combines Rule-Based, Trend-Based, Claim Support, Data Quality, and Content-Based signals
into explainable, non-diagnostic clinical & administrative recommendations.
"""

import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.recommendation import Recommendation
from app.models.document import UserDocument
from app.models.lab_result import LabResult
from app.models.insurance_claim import InsuranceClaim
from app.models.notification import Notification
from app.models.patient import Patient
from app.services.recommendation_rules import (
    RELATED_DOCUMENT_RULES,
    MONITORED_LAB_TESTS,
    SCORE_WEIGHTS,
    RECOMMENDATION_DISCLAIMER,
)
from app.services.content_recommender import ContentRecommender


class RecommendationEngine:
    """Hybrid Recommendation Engine for MedSentinel records."""

    @staticmethod
    def _normalize_sources(sources_list: List[str]) -> str:
        """Encode sources list into JSON string."""
        return json.dumps(sources_list)

    @classmethod
    def get_missing_document_recommendations(
        cls, db: Session, user_id: int, patient_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Identify missing baseline documents or sparse records."""
        recs: List[Dict[str, Any]] = []

        query = db.query(UserDocument).filter(UserDocument.user_id == user_id)
        if patient_id:
            query = query.filter((UserDocument.patient_id == patient_id) | (UserDocument.patient_id.is_(None)))
        docs = query.all()

        lab_reports = [d for d in docs if d.doc_type == "Lab Report"]
        prescriptions = [d for d in docs if d.doc_type == "Prescription"]
        invoices = [d for d in docs if d.doc_type == "Medical Invoice"]

        # Rule 1: Sparse lab records (only 1 lab report)
        if len(lab_reports) == 1:
            recs.append({
                "recommendation_type": "MISSING_RECORD",
                "priority": "MEDIUM",
                "title": "Upload Previous Laboratory Reports",
                "description": "Previous laboratory reports may improve historical trend analysis.",
                "reason": "Only one recent laboratory record is currently available, which limits historical baseline evaluation.",
                "confidence": 0.91,
                "sources": ["RULE_BASED", "TREND_ANALYSIS"],
                "related_document_id": lab_reports[0].id,
            })

        # Rule 2: Prescription exists without supporting invoice
        if prescriptions and not invoices:
            recs.append({
                "recommendation_type": "MISSING_RECORD",
                "priority": "LOW",
                "title": "Consider Uploading Pharmacy Invoices",
                "description": "Uploaded prescriptions are present without corresponding pharmacy invoices.",
                "reason": "Adding medical invoices can help consolidate health expenditure tracking.",
                "confidence": 0.72,
                "sources": ["RULE_BASED"],
                "related_document_id": prescriptions[0].id,
            })

        # Rule 3: Zero medical records
        if len(docs) == 0:
            recs.append({
                "recommendation_type": "MISSING_RECORD",
                "priority": "LOW",
                "title": "Upload Initial Medical Records",
                "description": "Your medical vault is currently empty.",
                "reason": "Consider uploading recent laboratory panels or consultation summaries if available.",
                "confidence": 0.80,
                "sources": ["RULE_BASED"],
            })

        return recs

    @classmethod
    def get_related_document_recommendations(
        cls, db: Session, user_id: int, patient_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Identify complementary documents based on relationship rules and content similarity."""
        recs: List[Dict[str, Any]] = []

        query = db.query(UserDocument).filter(UserDocument.user_id == user_id)
        if patient_id:
            query = query.filter((UserDocument.patient_id == patient_id) | (UserDocument.patient_id.is_(None)))
        docs = query.all()

        existing_types = {d.doc_type for d in docs}

        for doc in docs:
            expected_complementary = RELATED_DOCUMENT_RULES.get(doc.doc_type, [])
            for rel_type in expected_complementary:
                if rel_type not in existing_types and rel_type != "Previous Lab Report":
                    # Content similarity enrichment
                    content_sim = 0.5
                    candidates = [d for d in docs if d.id != doc.id]
                    if candidates:
                        sim_ranks = ContentRecommender.get_related_content_scores(doc, candidates)
                        if sim_ranks:
                            content_sim = max(content_sim, sim_ranks[0]["similarity"])

                    recs.append({
                        "recommendation_type": "RELATED_RECORD",
                        "priority": "LOW",
                        "title": f"Consider Linking {rel_type}",
                        "description": f"Records of type '{doc.doc_type}' often benefit from accompanying {rel_type}.",
                        "reason": f"No {rel_type} found associated with {doc.original_name}. Complementary records improve record continuity.",
                        "confidence": round(min(0.85, 0.65 + (content_sim * 0.2)), 2),
                        "sources": ["RULE_BASED", "CONTENT_SIMILARITY"],
                        "related_document_id": doc.id,
                    })
                    break  # Suggest one related type per document to avoid flooding

        return recs

    @classmethod
    def get_trend_recommendations(
        cls, db: Session, user_id: int, patient_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Analyze longitudinal changes in monitored laboratory values."""
        recs: List[Dict[str, Any]] = []

        if not patient_id:
            return recs

        # Fetch chronological lab results
        lab_results = (
            db.query(LabResult)
            .filter(LabResult.patient_id == patient_id)
            .order_by(LabResult.test_name.asc(), LabResult.test_date.asc())
            .all()
        )

        grouped: Dict[str, List[LabResult]] = {}
        for r in lab_results:
            grouped.setdefault(r.test_name, []).append(r)

        for test_name, results in grouped.items():
            if len(results) < 2:
                # Check for single abnormal/critical test
                if results and (results[0].status in ["HIGH", "LOW", "CRITICAL"]):
                    priority = "HIGH" if results[0].status == "CRITICAL" else "MEDIUM"
                    recs.append({
                        "recommendation_type": "TREND_REVIEW",
                        "priority": priority,
                        "title": f"Review {test_name} Value",
                        "description": f"Observed {test_name} ({results[0].observed_value} {results[0].unit}) is outside standard interval.",
                        "reason": f"Value status is {results[0].status}. Consider reviewing this record with a qualified healthcare professional.",
                        "confidence": 0.89 if priority == "HIGH" else 0.84,
                        "sources": ["TREND_ANALYSIS"],
                        "related_document_id": results[0].document_id,
                    })
                continue

            earliest = results[0]
            latest = results[-1]

            # Detect notable fluctuation (>15% or status change)
            pct_change = 0.0
            if earliest.observed_value > 0:
                pct_change = abs(latest.observed_value - earliest.observed_value) / earliest.observed_value

            has_status_shift = earliest.status != latest.status
            is_critical = latest.is_critical or latest.status == "CRITICAL"

            if pct_change >= 0.15 or has_status_shift or is_critical:
                priority = "HIGH" if is_critical else "MEDIUM"
                recs.append({
                    "recommendation_type": "TREND_REVIEW",
                    "priority": priority,
                    "title": f"Review {test_name} Trend",
                    "description": f"A notable variation is visible across available {test_name} records ({earliest.observed_value} -> {latest.observed_value} {latest.unit}).",
                    "reason": (
                        f"Longitudinal records indicate a change in {test_name} levels over time. "
                        "Consider reviewing this trend with a qualified healthcare professional if you have symptoms or questions."
                    ),
                    "confidence": 0.93 if is_critical else 0.87,
                    "sources": ["TREND_ANALYSIS", "RULE_BASED"],
                    "related_document_id": latest.document_id,
                })

        return recs

    @classmethod
    def get_claim_recommendations(
        cls, db: Session, user_id: int, patient_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Identify missing supporting documentation for submitted or active insurance claims."""
        recs: List[Dict[str, Any]] = []

        query = db.query(InsuranceClaim).filter(InsuranceClaim.user_id == user_id)
        claims = query.all()

        for claim in claims:
            if claim.claim_status in ["SUBMITTED", "UNDER_REVIEW", "DOCUMENTS_REQUIRED"]:
                # Check patient documents for invoice
                invoices = (
                    db.query(UserDocument)
                    .filter(
                        UserDocument.user_id == user_id,
                        UserDocument.doc_type == "Medical Invoice"
                    )
                    .all()
                )

                priority = "HIGH" if claim.claim_status == "DOCUMENTS_REQUIRED" else "MEDIUM"

                if not invoices:
                    recs.append({
                        "recommendation_type": "CLAIM_SUPPORT",
                        "priority": priority,
                        "title": "Attach Itemized Medical Invoices",
                        "description": f"Claim #{claim.id} for ₹{claim.claim_amount:,.0f} is {claim.claim_status}.",
                        "reason": "Attaching itemized hospital invoices and payment receipts may accelerate claim settlement.",
                        "confidence": 0.94,
                        "sources": ["CLAIM_ANALYSIS", "RULE_BASED"],
                        "related_claim_id": claim.id,
                    })
                else:
                    recs.append({
                        "recommendation_type": "CLAIM_SUPPORT",
                        "priority": "LOW",
                        "title": "Review Claim Supporting Records",
                        "description": f"Review supporting records associated with Claim #{claim.id}.",
                        "reason": "Verification documents are attached; ensure all discharge summaries are up to date.",
                        "confidence": 0.85,
                        "sources": ["CLAIM_ANALYSIS"],
                        "related_claim_id": claim.id,
                    })

        return recs

    @classmethod
    def get_data_quality_recommendations(
        cls, db: Session, user_id: int, patient_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Detect unverified, duplicate, or incomplete document records."""
        recs: List[Dict[str, Any]] = []

        query = db.query(UserDocument).filter(UserDocument.user_id == user_id)
        if patient_id:
            query = query.filter((UserDocument.patient_id == patient_id) | (UserDocument.patient_id.is_(None)))
        docs = query.all()

        for doc in docs:
            # 1. Duplicate detection
            if doc.is_duplicate:
                recs.append({
                    "recommendation_type": "DATA_QUALITY",
                    "priority": "MEDIUM",
                    "title": "Duplicate Document Flagged",
                    "description": f"'{doc.original_name}' has a matching cryptographic hash with an existing record.",
                    "reason": "This file matches an existing record in your vault. Consider verifying whether this is an intentional duplicate.",
                    "confidence": 0.95,
                    "sources": ["DATA_QUALITY", "RULE_BASED"],
                    "related_document_id": doc.id,
                })

            # 2. Unverified document
            if doc.verification_status in ["PENDING", "FLAGGED"]:
                priority = "HIGH" if doc.verification_status == "FLAGGED" else "LOW"
                recs.append({
                    "recommendation_type": "DATA_QUALITY",
                    "priority": priority,
                    "title": "Document Verification Pending",
                    "description": f"Cryptographic integrity check for '{doc.original_name}' is currently {doc.verification_status}.",
                    "reason": "The uploaded file has not yet completed full verification. Run hash verification to ensure tamper-evident storage.",
                    "confidence": 0.88,
                    "sources": ["DATA_QUALITY"],
                    "related_document_id": doc.id,
                })

        return recs

    @classmethod
    def generate_hybrid_recommendations(
        cls, db: Session, user_id: int, patient_id: Optional[int] = None
    ) -> List[Recommendation]:
        """
        Generate explainable hybrid recommendations across rule-based, trend-based,
        claim support, data quality, and content similarity signals.
        Deduplicates against active records, persists new items, and notifies on HIGH priority.
        """
        # Resolve patient_id if not provided
        if not patient_id:
            pat = db.query(Patient).filter(Patient.user_id == user_id).first()
            if pat:
                patient_id = pat.id

        raw_candidates: List[Dict[str, Any]] = []
        raw_candidates.extend(cls.get_missing_document_recommendations(db, user_id, patient_id))
        raw_candidates.extend(cls.get_related_document_recommendations(db, user_id, patient_id))
        raw_candidates.extend(cls.get_trend_recommendations(db, user_id, patient_id))
        raw_candidates.extend(cls.get_claim_recommendations(db, user_id, patient_id))
        raw_candidates.extend(cls.get_data_quality_recommendations(db, user_id, patient_id))

        # Existing active recommendations to avoid re-inserting duplicates
        existing_active = (
            db.query(Recommendation)
            .filter(
                Recommendation.user_id == user_id,
                Recommendation.status == "ACTIVE"
            )
            .all()
        )
        existing_keys = {(r.recommendation_type, r.title) for r in existing_active}

        new_recs: List[Recommendation] = []
        for cand in raw_candidates:
            key = (cand["recommendation_type"], cand["title"])
            if key in existing_keys:
                continue

            # Normalized confidence 0.0 - 1.0
            base_conf = cand.get("confidence", 0.75)
            normalized_conf = round(min(1.0, max(0.1, base_conf)), 2)

            rec = Recommendation(
                user_id=user_id,
                patient_id=patient_id,
                recommendation_type=cand["recommendation_type"],
                priority=cand.get("priority", "LOW"),
                title=cand["title"],
                description=cand.get("description", ""),
                reason=cand.get("reason", ""),
                confidence=normalized_conf,
                sources=cls._normalize_sources(cand.get("sources", ["RULE_BASED"])),
                status="ACTIVE",
                related_document_id=cand.get("related_document_id"),
                related_claim_id=cand.get("related_claim_id"),
            )
            db.add(rec)
            db.flush()
            new_recs.append(rec)
            existing_keys.add(key)

            # High priority notification integration
            if rec.priority == "HIGH":
                notif = Notification(
                    user_id=user_id,
                    title="MedSentinel Recommendation",
                    message=f"A high-priority record review recommendation is available in your Health Dashboard: {rec.title}.",
                    type="recommendation",
                    is_read=False,
                )
                db.add(notif)

        db.commit()

        # Return all currently active recommendations for user/patient
        query = db.query(Recommendation).filter(Recommendation.user_id == user_id)
        if patient_id:
            query = query.filter((Recommendation.patient_id == patient_id) | (Recommendation.patient_id.is_(None)))
        return query.order_by(Recommendation.created_at.desc()).all()
