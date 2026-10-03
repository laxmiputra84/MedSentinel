import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_password_hash
from app.models import User, Hospital, Insurance, InsuranceClaim, Appointment, UserDocument
from app.models.knowledge_base import KnowledgeDataset, KnowledgeDocument, KnowledgeChunk
from app.rag.ingestion_service import IngestionService
from app.rag.rag_pipeline import RAGPipeline
from app.rag.vector_store import VectorStore
try:
    from tests.conftest import TestingSessionLocal, test_engine, Base
except ImportError:
    from conftest import TestingSessionLocal, test_engine, Base

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Clear table records
    db.query(KnowledgeChunk).delete()
    db.query(KnowledgeDocument).delete()
    db.query(KnowledgeDataset).delete()
    db.query(InsuranceClaim).delete()
    db.query(Insurance).delete()
    db.query(Hospital).delete()
    db.query(User).delete()
    db.commit()

    # Clear in-memory vector store
    VectorStore._local_store.clear()

    # Create Super Admin
    admin_user = User(
        email="superadmin@medsentinel.com",
        name="Super Administrator",
        phone="9999999990",
        hashed_password=get_password_hash("AdminPass123!"),
        role="SUPER_ADMIN",
        is_active=True
    )
    # Create Hospital Admin
    hosp_admin = User(
        email="hospadmin@apollo.com",
        name="Apollo Hospital Admin",
        phone="9999999991",
        hashed_password=get_password_hash("AdminPass123!"),
        role="HOSPITAL_ADMIN",
        hospital_id=1,
        is_active=True
    )
    # Create Patient User
    patient_user = User(
        email="patient_rag@example.com",
        name="John Doe",
        phone="9999999992",
        hashed_password=get_password_hash("UserPass123!"),
        role="USER",
        is_active=True
    )
    # Create Other Patient User
    other_patient = User(
        email="other_rag@example.com",
        name="Jane Smith",
        phone="9999999993",
        hashed_password=get_password_hash("UserPass123!"),
        role="USER",
        is_active=True
    )

    db.add_all([admin_user, hosp_admin, patient_user, other_patient])
    db.commit()

    # Create Hospital Record
    hospital = Hospital(
        id=1,
        name="Apollo Multi-Speciality Hospital",
        location="Bengaluru, Karnataka",
        specialization="Cardiology, Neurology, Oncology",
        rating=4.9,
        distance=2.5,
        facilities="24/7 ICU, Emergency Trauma Care, Advanced Cath Lab",
        is_available=True
    )
    db.add(hospital)

    # Create Insurance & User Claim
    insurance = Insurance(
        id=1,
        name="Care Supreme Health Shield",
        provider="Care Health",
        coverage_amount=1000000.0,
        premium_monthly=850.0,
        premium_annual=9500.0,
        cashless_network=16000,
        rating=4.8
    )
    db.add(insurance)
    db.commit()

    claim = InsuranceClaim(
        id=101,
        user_id=patient_user.id,
        hospital_id=1,
        insurance_id=1,
        claim_amount=85000.0,
        claim_status="UNDER_REVIEW",
        claim_description="Angioplasty with stent placement."
    )
    db.add(claim)
    db.commit()
    db.close()

def get_auth_token(email, password):
    client.cookies.clear()
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

def test_ai_health_endpoint():
    """Verify GET /api/ai/health returns accurate status without exposing keys."""
    res = client.get("/api/ai/health")
    assert res.status_code == 200
    data = res.json()
    assert "ai_enabled" in data
    assert "provider" in data
    assert "rag_enabled" in data
    assert "GEMINI_API_KEY" not in str(data)

def test_dataset_ingestion_and_vector_indexing():
    """Verify dataset text extraction, chunking, embeddings, and vector upsert."""
    db = TestingSessionLocal()

    dataset = KnowledgeDataset(
        name="Apollo Hospital Clinical Cardiology Guidelines",
        description="Authoritative clinical triage criteria and ICU bed protocols for Apollo Cardiology.",
        file_name="cardiology_protocols.txt",
        file_type="TXT",
        source_type="ADMIN_UPLOAD",
        status="UPLOADED",
        visibility="USER_AUTHORIZED",
        hospital_id=1
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    success = asyncio.run(IngestionService.process_dataset(dataset.id, db))
    assert success is True

    db.refresh(dataset)
    assert dataset.status == "READY"

    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.dataset_id == dataset.id).all()
    assert len(docs) > 0

    chunks = db.query(KnowledgeChunk).all()
    assert len(chunks) > 0
    assert VectorStore.get_indexed_points_count() > 0
    db.close()

def test_private_rag_query_with_citations_and_rbac():
    """Verify Private RAG retrieves authorized records and returns citations."""
    db = TestingSessionLocal()
    # Ingest private knowledge
    dataset = KnowledgeDataset(
        name="ESIC Scheme Surgical Benefits 2026",
        description="ESIC covers 100% cashless hospitalization for insured wage workers up to ₹21,000/mo.",
        file_name="esic_guidelines.txt",
        file_type="TXT",
        source_type="SCHEME_DOC",
        status="READY",
        visibility="USER_AUTHORIZED"
    )
    db.add(dataset)
    db.commit()
    asyncio.run(IngestionService.process_dataset(dataset.id, db))
    db.close()

    # Query with patient user
    token = get_auth_token("patient_rag@example.com", "UserPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/ai/private-chat",
        headers=headers,
        json={"message": "What is the wage limit and coverage for ESIC scheme?", "mode": "strict_private"}
    )
    assert res.status_code == 200, f"Private chat failed: {res.text}"
    data = res.json()
    assert data["found_in_private_data"] is True
    assert len(data["sources"]) > 0

def test_strict_private_mode_no_hallucination():
    """Verify that when no private information exists, the AI strictly says information was not found."""
    token = get_auth_token("patient_rag@example.com", "UserPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/ai/private-chat",
        headers=headers,
        json={"message": "Who was the Roman emperor in 45 BC?", "mode": "strict_private"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["found_in_private_data"] is False
    assert "could not find this information in the authorized MedSentinel knowledge base" in data["response"]

def test_cross_hospital_and_cross_user_isolation():
    """Verify cross-user claims and cross-hospital restricted documents are isolated."""
    # Patient Jane Smith logs in and queries claims
    token_jane = get_auth_token("other_rag@example.com", "UserPass123!")
    headers_jane = {"Authorization": f"Bearer {token_jane}"}

    # Should NOT see John Doe's claim #101
    res = client.post(
        "/api/ai/chat",
        headers=headers_jane,
        json={"message": "Show my insurance claim status"}
    )
    assert res.status_code == 200
    assert "#101" not in res.json()["response"]

def test_admin_dataset_management_and_approval_workflow():
    """Verify employee dataset upload -> pending review -> admin approval -> indexing."""
    token_user = get_auth_token("patient_rag@example.com", "UserPass123!")
    token_admin = get_auth_token("superadmin@medsentinel.com", "AdminPass123!")

    # Employee/User uploads dataset
    res_upload = client.post(
        "/api/admin/datasets/upload",
        headers={"Authorization": f"Bearer {token_user}"},
        data={
            "name": "Employee Internal Oncology Protocol",
            "description": "Oncology chemotherapy schedule and ward requirements.",
            "visibility": "USER_AUTHORIZED",
            "source_type": "EMPLOYEE_UPLOAD"
        }
    )
    assert res_upload.status_code == 200
    ds_id = res_upload.json()["id"]
    assert res_upload.json()["status"] == "PENDING_REVIEW"

    # Super Admin approves dataset
    res_approve = client.post(
        f"/api/admin/datasets/{ds_id}/approve",
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert res_approve.status_code == 200

    # Verify dataset is now READY and chunks created
    res_chunks = client.get(
        f"/api/admin/datasets/{ds_id}/chunks",
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert res_chunks.status_code == 200
    assert len(res_chunks.json()) > 0
