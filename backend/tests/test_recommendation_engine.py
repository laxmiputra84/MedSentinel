import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.patient import Patient
from app.models.document import UserDocument
from app.models.lab_result import LabResult
from app.models.insurance_claim import InsuranceClaim
from app.models.recommendation import Recommendation
from app.models.notification import Notification
from app.services.recommendation_engine import RecommendationEngine
from app.core.security import create_access_token
from fastapi.testclient import TestClient
from app.main import app

api_client = TestClient(app)


def _get_auth_headers(user: User):
    token = create_access_token(subject=str(user.id), role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def setup_patient(db_session):
    uid = uuid.uuid4().hex[:8]
    user = User(
        name=f"John Doe {uid}",
        email=f"john.{uid}@test.com",
        hashed_password="hashed_pwd",
        role="USER",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    patient = Patient(
        user_id=user.id,
        patient_code=f"MS-2026-{uid}",
        name=user.name,
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(patient)
    return user, patient


def test_missing_document_recommendation(db_session, setup_patient):
    """1. Single lab report triggers MISSING_RECORD recommendation."""
    user, patient = setup_patient

    doc = UserDocument(
        user_id=user.id,
        patient_id=patient.id,
        document_code=f"DOC-{uuid.uuid4().hex[:6]}",
        file_hash="hash1",
        doc_type="Lab Report",
        filename="cbc.pdf",
        original_name="Complete_Blood_Count.pdf",
        file_path="/uploads/cbc.pdf",
        file_type="application/pdf",
        status="APPROVED",
        verification_status="VERIFIED",
    )
    db_session.add(doc)
    db_session.commit()

    recs = RecommendationEngine.get_missing_document_recommendations(db_session, user.id, patient.id)
    assert len(recs) >= 1
    missing_rec = next(r for r in recs if r["recommendation_type"] == "MISSING_RECORD")
    assert missing_rec["title"] == "Upload Previous Laboratory Reports"
    assert missing_rec["priority"] == "MEDIUM"
    assert "RULE_BASED" in missing_rec["sources"]
    assert missing_rec["confidence"] >= 0.8


def test_related_document_recommendation(db_session, setup_patient):
    """2. Lab Report without prescription triggers RELATED_RECORD recommendation."""
    user, patient = setup_patient

    doc = UserDocument(
        user_id=user.id,
        patient_id=patient.id,
        document_code=f"DOC-{uuid.uuid4().hex[:6]}",
        file_hash="hash2",
        doc_type="Lab Report",
        filename="metabolic.pdf",
        original_name="Comprehensive_Metabolic_Panel.pdf",
        file_path="/uploads/metabolic.pdf",
        file_type="application/pdf",
        status="APPROVED",
        verification_status="VERIFIED",
    )
    db_session.add(doc)
    db_session.commit()

    recs = RecommendationEngine.get_related_document_recommendations(db_session, user.id, patient.id)
    assert len(recs) >= 1
    rel_rec = next(r for r in recs if r["recommendation_type"] == "RELATED_RECORD")
    assert "Prescription" in rel_rec["title"] or "Consultation" in rel_rec["title"]
    assert "RULE_BASED" in rel_rec["sources"]


def test_lab_trend_recommendation(db_session, setup_patient):
    """3. Longitudinal variation in WBC (>15%) triggers TREND_REVIEW with safe non-diagnostic advice."""
    user, patient = setup_patient

    now = datetime.now(timezone.utc)
    res1 = LabResult(
        patient_id=patient.id,
        test_name="WBC",
        observed_value=8400.0,
        unit="cells/uL",
        reference_min=4000.0,
        reference_max=11000.0,
        status="NORMAL",
        test_date=now - timedelta(days=90),
    )
    res2 = LabResult(
        patient_id=patient.id,
        test_name="WBC",
        observed_value=11400.0,
        unit="cells/uL",
        reference_min=4000.0,
        reference_max=11000.0,
        status="HIGH",
        test_date=now,
    )
    db_session.add_all([res1, res2])
    db_session.commit()

    recs = RecommendationEngine.get_trend_recommendations(db_session, user.id, patient.id)
    assert len(recs) >= 1
    trend_rec = next(r for r in recs if r["recommendation_type"] == "TREND_REVIEW")
    assert "WBC" in trend_rec["title"]
    assert "healthcare professional" in trend_rec["reason"].lower()
    # Confirm safe non-diagnostic wording (no disease claims)
    assert "infection" not in trend_rec["reason"].lower()
    assert "disease" not in trend_rec["reason"].lower()


def test_claim_support_recommendation(db_session, setup_patient):
    """4. Claim under review without invoice triggers CLAIM_SUPPORT recommendation."""
    user, patient = setup_patient

    claim = InsuranceClaim(
        user_id=user.id,
        patient_id=patient.id,
        claim_amount=45000.0,
        claim_status="UNDER_REVIEW",
        claim_description="Appendectomy procedure",
    )
    db_session.add(claim)
    db_session.commit()

    recs = RecommendationEngine.get_claim_recommendations(db_session, user.id, patient.id)
    assert len(recs) >= 1
    claim_rec = next(r for r in recs if r["recommendation_type"] == "CLAIM_SUPPORT")
    assert claim_rec["related_claim_id"] == claim.id
    assert "Invoices" in claim_rec["title"] or "Supporting" in claim_rec["title"]


def test_data_quality_recommendation(db_session, setup_patient):
    """5. Pending verification status triggers DATA_QUALITY recommendation."""
    user, patient = setup_patient

    doc = UserDocument(
        user_id=user.id,
        patient_id=patient.id,
        document_code=f"DOC-{uuid.uuid4().hex[:6]}",
        file_hash="hash3",
        doc_type="Discharge Summary",
        filename="discharge.pdf",
        original_name="Discharge_Summary.pdf",
        file_path="/uploads/discharge.pdf",
        file_type="application/pdf",
        status="PENDING",
        verification_status="PENDING",
    )
    db_session.add(doc)
    db_session.commit()

    recs = RecommendationEngine.get_data_quality_recommendations(db_session, user.id, patient.id)
    assert len(recs) >= 1
    quality_rec = next(r for r in recs if r["recommendation_type"] == "DATA_QUALITY")
    assert "Verification" in quality_rec["title"] or "Pending" in quality_rec["title"]


def test_hybrid_confidence_scoring(db_session, setup_patient):
    """6. Multi-signal hybrid generator produces normalized confidence 0.0 - 1.0 and notifies on HIGH."""
    user, patient = setup_patient

    # Create critical lab result to produce a HIGH priority recommendation
    now = datetime.now(timezone.utc)
    crit_res = LabResult(
        patient_id=patient.id,
        test_name="Potassium",
        observed_value=6.4,
        unit="mEq/L",
        reference_min=3.5,
        reference_max=5.1,
        status="CRITICAL",
        is_critical=True,
        test_date=now,
    )
    db_session.add(crit_res)
    db_session.commit()

    results = RecommendationEngine.generate_hybrid_recommendations(db_session, user.id, patient.id)
    assert len(results) >= 1
    for r in results:
        assert 0.0 <= r.confidence <= 1.0
        assert r.status == "ACTIVE"

    # Check notification generation for HIGH priority
    high_recs = [r for r in results if r.priority == "HIGH"]
    if high_recs:
        notif = db_session.query(Notification).filter(Notification.user_id == user.id).first()
        assert notif is not None
        assert "Recommendation" in notif.title


def test_recommendation_status_update(db_session, setup_patient):
    """7. Updating status to VIEWED, COMPLETED, or DISMISSED via PATCH."""
    user, patient = setup_patient
    headers = _get_auth_headers(user)

    rec = Recommendation(
        user_id=user.id,
        patient_id=patient.id,
        recommendation_type="MISSING_RECORD",
        priority="LOW",
        title=f"Upload Previous Records {uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        confidence=0.85,
        sources='["RULE_BASED"]',
    )
    db_session.add(rec)
    db_session.commit()

    # Update to VIEWED
    res = api_client.patch(
        f"/api/recommendations/{rec.id}/status",
        json={"status": "VIEWED"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "VIEWED"

    # Update to COMPLETED
    res = api_client.patch(
        f"/api/recommendations/{rec.id}/status",
        json={"status": "COMPLETED"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"


def test_user_authorization_and_rbac(db_session, setup_patient):
    """8. User cannot access another patient's recommendations; Admin can."""
    user1, patient1 = setup_patient
    u2_id = uuid.uuid4().hex[:8]
    adm_id = uuid.uuid4().hex[:8]

    user2 = User(
        name=f"Jane Smith {u2_id}",
        email=f"jane.{u2_id}@test.com",
        hashed_password="hashed_pwd",
        role="USER",
        is_active=True,
    )
    admin = User(
        name=f"Admin User {adm_id}",
        email=f"admin.{adm_id}@test.com",
        hashed_password="hashed_pwd",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db_session.add_all([user2, admin])
    db_session.commit()

    headers_user2 = _get_auth_headers(user2)
    headers_admin = _get_auth_headers(admin)

    # User 2 tries to access Patient 1 recommendations -> 403 Forbidden
    res = api_client.get(f"/api/recommendations/{patient1.id}", headers=headers_user2)
    assert res.status_code == 403

    # Admin accesses Patient 1 recommendations -> 200 OK
    res = api_client.get(f"/api/recommendations/{patient1.id}", headers=headers_admin)
    assert res.status_code == 200


def test_empty_records_handling(db_session, setup_patient):
    """9. Empty vault records generate graceful initial missing record recommendation."""
    user, patient = setup_patient

    recs = RecommendationEngine.get_missing_document_recommendations(db_session, user.id, patient.id)
    assert len(recs) >= 1
    assert recs[0]["recommendation_type"] == "MISSING_RECORD"
    assert "Initial" in recs[0]["title"]


def test_duplicate_document_handling(db_session, setup_patient):
    """10. Duplicate document generates DATA_QUALITY recommendation."""
    user, patient = setup_patient

    doc = UserDocument(
        user_id=user.id,
        patient_id=patient.id,
        document_code=f"DOC-{uuid.uuid4().hex[:6]}",
        file_hash="dup_hash",
        doc_type="Medical Invoice",
        filename="invoice_copy.pdf",
        original_name="Pharmacy_Bill_Copy.pdf",
        file_path="/uploads/invoice_copy.pdf",
        file_type="application/pdf",
        status="PENDING",
        verification_status="PENDING",
        is_duplicate=True,
    )
    db_session.add(doc)
    db_session.commit()

    recs = RecommendationEngine.get_data_quality_recommendations(db_session, user.id, patient.id)
    assert any(r["recommendation_type"] == "DATA_QUALITY" and "Duplicate" in r["title"] for r in recs)
