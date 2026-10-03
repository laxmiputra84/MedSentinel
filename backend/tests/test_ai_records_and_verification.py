import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.document_classifier import DocumentClassifier
from app.services.lab_analyzer import LabAnalyzer
from app.services.health_score import HealthScoreEngine
from app.services.document_verifier import DocumentVerifier
from app.services.fraud_detector import FraudDetector
from app.core.security import get_password_hash
from app.models import User
try:
    from tests.conftest import TestingSessionLocal, test_engine, Base
except ImportError:
    from conftest import TestingSessionLocal, test_engine, Base

api_client = TestClient(app)

SAMPLE_LAB_REPORT_TEXT = """
DEPARTMENT OF LABORATORY MEDICINE
Patient Name: Alex Demo Patient
Patient ID: MS-2026-08892
Report Date: 2026-09-01
COMPLETE BLOOD COUNT (CBC) & METABOLIC PANEL

Hemoglobin: 14.8 g/dL (13.5 - 17.5)
WBC: 11400 cells/uL (4000 - 11000)
Platelets: 265000 /uL (150000 - 450000)
Neutrophils: 74 % (40 - 70)
Lymphocytes: 20 % (20 - 40)
Fasting Blood Glucose: 98 mg/dL (70 - 100)
Serum Creatinine: 0.95 mg/dL (0.7 - 1.3)
CRP: 6.8 mg/L (< 3.0)
Potassium: 4.2 mEq/L (3.5 - 5.1)
"""

def get_auth_token():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    existing = db.query(User).filter(User.email == "patient@example.com").first()
    if not existing:
        u = User(
            name="Test Patient",
            email="patient@example.com",
            hashed_password=get_password_hash("patient123"),
            role="USER",
            phone="+91 99999 11111"
        )
        db.add(u)
        db.commit()
    db.close()

    api_client.cookies.clear()
    res = api_client.post("/api/auth/login", json={"email": "patient@example.com", "password": "patient123"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]

def test_document_classification_service():
    # Test Lab Report
    doc_type, conf = DocumentClassifier.classify_text(SAMPLE_LAB_REPORT_TEXT, "cbc_report.pdf")
    assert doc_type == "Lab Report"
    assert conf >= 0.70

    # Test Prescription
    rx_text = "Rx: Paracetamol 650mg tablet once daily after food. Sig: take 1 tab BD for 3 days."
    doc_type, conf = DocumentClassifier.classify_text(rx_text, "rx_doc.pdf")
    assert doc_type == "Prescription"

    # Test Medical Invoice
    inv_text = "Hospital Tax Invoice. Net Amount Payable: ₹45,000. Consultation fee, room charges, GSTIN."
    doc_type, conf = DocumentClassifier.classify_text(inv_text, "bill_invoice.pdf")
    assert doc_type == "Medical Invoice"

    # Test Discharge Summary
    ds_text = "Discharge Summary. Date of Admission: 2026-08-10. Final Diagnosis: Acute Appendicitis."
    doc_type, conf = DocumentClassifier.classify_text(ds_text, "discharge_summary.pdf")
    assert doc_type == "Discharge Summary"

def test_lab_data_extraction_and_abnormal_detection():
    data = LabAnalyzer.extract_laboratory_data(SAMPLE_LAB_REPORT_TEXT)
    assert data["patient_name"] == "Alex Demo Patient"
    assert data["patient_id"] == "MS-2026-08892"
    assert data["report_date"] == "2026-09-01"
    assert len(data["tests"]) >= 7

    # Check Hemoglobin (Normal)
    hb_test = next(t for t in data["tests"] if t["name"] == "Hemoglobin")
    assert hb_test["value"] == 14.8
    assert hb_test["status"] == "NORMAL"
    assert not hb_test["is_critical"]

    # Check WBC (Elevated -> HIGH)
    wbc_test = next(t for t in data["tests"] if t["name"] == "WBC")
    assert wbc_test["value"] == 11400.0
    assert wbc_test["status"] == "HIGH"

    # Check CRP (Elevated -> HIGH)
    crp_test = next(t for t in data["tests"] if t["name"] == "CRP")
    assert crp_test["value"] == 6.8
    assert crp_test["status"] == "HIGH"

def test_critical_value_detection():
    # Critical Potassium (e.g. 6.8 > 6.0 critical high or 2.1 < 2.8 critical low)
    crit_high_status, is_crit = LabAnalyzer.evaluate_status("Potassium", 6.8)
    assert crit_high_status == "CRITICAL"
    assert is_crit is True

    crit_low_status, is_crit2 = LabAnalyzer.evaluate_status("Potassium", 2.2)
    assert crit_low_status == "CRITICAL"
    assert is_crit2 is True

def test_health_score_and_ai_summary():
    extracted = LabAnalyzer.extract_laboratory_data(SAMPLE_LAB_REPORT_TEXT)
    health_score, risk_score, risk_level, abnormal_count = HealthScoreEngine.calculate_scores(extracted["tests"])

    assert 0 <= health_score <= 100
    assert 0 <= risk_score <= 100
    assert risk_level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert abnormal_count >= 1

    summary = HealthScoreEngine.generate_health_summary(extracted["tests"], risk_level)
    assert "AI HEALTH SUMMARY" in summary
    assert "Abnormal Results Detected" in summary
    assert "Important:" in summary
    assert "It does not provide a medical diagnosis" in summary

def test_document_verifier_and_hash():
    sample_bytes = b"MedSentinel cryptographic file integrity test 2026"
    hash1 = DocumentVerifier.calculate_sha256(sample_bytes)
    assert len(hash1) == 64
    # Hashing identical bytes returns identical hash
    hash2 = DocumentVerifier.calculate_sha256(sample_bytes)
    assert hash1 == hash2

    doc_code = DocumentVerifier.generate_document_code()
    assert doc_code.startswith("DOC-")

def test_api_classify_and_trends():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Test POST /documents/classify endpoint
    classify_res = api_client.post(
        "/api/documents/classify",
        data={"text": SAMPLE_LAB_REPORT_TEXT, "filename": "blood_panel.pdf"},
        headers=headers,
    )
    assert classify_res.status_code == 200
    assert classify_res.json()["document_type"] == "Lab Report"
    assert classify_res.json()["confidence"] >= 0.70

    # Test Upload with automatic extraction & duplicate detection
    file_bytes = SAMPLE_LAB_REPORT_TEXT.encode("utf-8")
    upload_res = api_client.post(
        "/api/documents/upload",
        files={"document": ("sample_report.txt", io.BytesIO(file_bytes), "text/plain")},
        data={"docType": "Lab Report"},
        headers=headers,
    )
    assert upload_res.status_code == 201
    up_data = upload_res.json()
    assert up_data["document_code"].startswith("DOC-")
    assert len(up_data["file_hash"]) == 64
    assert up_data["verification_status"] == "VERIFIED"
    assert not up_data["duplicate_detected"]

    # Test duplicate upload of the exact same file
    dup_res = api_client.post(
        "/api/documents/upload",
        files={"document": ("sample_report_copy.txt", io.BytesIO(file_bytes), "text/plain")},
        data={"docType": "Lab Report"},
        headers=headers,
    )
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert dup_data["duplicate_detected"] is True
    assert dup_data["verification_status"] == "FLAGGED"

    # Test GET /health/trends/{patient_id}
    trends_res = api_client.get(
        "/api/health/trends/MS-2026-08892",
        headers=headers,
    )
    assert trends_res.status_code == 200
    trends_data = trends_res.json()
    assert "WBC" in trends_data
    assert len(trends_data["WBC"]) >= 1

    # Test GET /health/dashboard
    dash_res = api_client.get("/api/health/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_documents"] >= 2
    assert dash_data["health_score"] > 0
    assert dash_data["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]

def test_claims_fraud_analysis():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create an insurance claim
    claim_res = api_client.post(
        "/api/insurance-claims",
        json={
            "claim_amount": 75000.0,
            "claim_description": "Patient MS-2026-08892 emergency hospitalization and surgery.",
            "documents": "sample_report.txt",
        },
        headers=headers,
    )
    assert claim_res.status_code == 201
    claim_data = claim_res.json()
    claim_id = claim_data["id"]

    # Fraud analysis should be populated
    assert claim_data["fraud_analysis"] is not None
    assert claim_data["fraud_analysis"]["fraud_risk"] in ["LOW", "MEDIUM", "HIGH"]
    assert isinstance(claim_data["fraud_analysis"]["flags"], list)

    # Test GET /insurance-claims/{claim_id}/fraud-analysis
    fraud_res = api_client.get(f"/api/insurance-claims/{claim_id}/fraud-analysis", headers=headers)
    assert fraud_res.status_code == 200
    assert "fraud_score" in fraud_res.json()
    assert "fraud_risk" in fraud_res.json()
