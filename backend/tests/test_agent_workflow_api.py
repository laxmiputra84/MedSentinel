"""
MedSentinel Agentic Architecture — Phase 3 Automated Pytest Suite
Comprehensive test suite validating:
- POST /api/agent-workflow/run (Background Async Workflow Launch)
- GET /api/agent-workflow/{workflow_id} (Structured State Retrieval)
- GET /api/agent-workflow/{workflow_id}/stream (Real-Time SSE Streaming)
- Workflow isolation (Workflow A events do not leak into Workflow B)
- POST /api/agent-workflow/{workflow_id}/review (Human-in-the-Loop Review Approval / Rejection)
- GET /api/agent-workflow/patient/{patient_id}/history (Patient Workflow History)
- RBAC, JWT Authentication, and Tenant Isolation Security
"""

import pytest
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_password_hash
from app.models.patient import Patient
from app.models.user import User
from app.models.lab_result import LabResult
from app.models.document import UserDocument
from app.agents.state import WorkflowState, WorkflowType, WorkflowStatus, EscalationLevel
from app.services.workflow_manager import workflow_manager

try:
    from tests.conftest import TestingSessionLocal, test_engine, Base
except ImportError:
    from conftest import TestingSessionLocal, test_engine, Base

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_api_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Clear tables
    db.query(LabResult).delete()
    db.query(UserDocument).delete()
    db.query(Patient).delete()
    db.query(User).delete()
    db.commit()

    # Create Patient User (User 1)
    patient_user = User(
        name="Elena Rostova",
        email="elena.rostova@example.com",
        hashed_password=get_password_hash("PatientPass123!"),
        role="USER",
        phone="+91 97777 11111",
        blood_group="A+"
    )
    # Create Other Patient User (User 2)
    other_user = User(
        name="Marcus Vance",
        email="marcus.vance@example.com",
        hashed_password=get_password_hash("OtherPass123!"),
        role="USER",
        phone="+91 97777 22222",
        blood_group="B+"
    )
    # Create Hospital Admin / Doctor
    doctor_admin = User(
        name="Dr. Alistair Finch",
        email="dr.finch@apollo.com",
        hashed_password=get_password_hash("DoctorPass123!"),
        role="HOSPITAL_ADMIN",
        hospital_id=1,
        phone="+91 97777 33333"
    )
    # Create Super Admin
    super_admin = User(
        name="Chief Administrator",
        email="superadmin@medsentinel.com",
        hashed_password=get_password_hash("AdminPass123!"),
        role="SUPER_ADMIN",
        phone="+91 97777 44444"
    )

    db.add_all([patient_user, other_user, doctor_admin, super_admin])
    db.commit()
    db.refresh(patient_user)
    db.refresh(other_user)
    db.refresh(doctor_admin)
    db.refresh(super_admin)

    # Create Patient records
    p1 = Patient(
        user_id=patient_user.id,
        patient_code=f"MS-2026-{patient_user.id:05d}",
        name="Elena Rostova",
        blood_group="A+",
        gender="Female",
        emergency_contact="+91 97777 99991"
    )
    p2 = Patient(
        user_id=other_user.id,
        patient_code=f"MS-2026-{other_user.id:05d}",
        name="Marcus Vance",
        blood_group="B+",
        gender="Male",
        emergency_contact="+91 97777 99992"
    )
    db.add_all([p1, p2])
    db.commit()
    db.close()


def _login_token(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


# ==========================================
# 1. Start Workflow Endpoint Tests
# ==========================================

def test_start_workflow_endpoint():
    token = _login_token("elena.rostova@example.com", "PatientPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    sample_report = (
        "METROPOLIS HEALTH\n"
        "Patient Name: Elena Rostova\n"
        "Hemoglobin: 12.8 g/dL\n"
        "WBC: 6800 cells/uL\n"
        "Platelets: 210000 /uL"
    )

    db = TestingSessionLocal()
    elena = db.query(User).filter(User.email == "elena.rostova@example.com").first()
    patient = db.query(Patient).filter(Patient.user_id == elena.id).first()
    db.close()

    payload = {
        "patient_id": patient.id if patient else None,
        "filename": "elena_cbc.pdf",
        "extracted_text": sample_report,
        "workflow_type": "AUTOMATIC"
    }

    response = client.post("/api/agent-workflow/run", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "workflow_id" in data
    assert data["status"] == "STARTED"
    assert data["workflow_id"].startswith("wf-")


def test_start_workflow_unauthorized_patient_access():
    # Marcus (User 2) trying to start workflow for Elena's patient ID (Patient 1)
    db = TestingSessionLocal()
    elena = db.query(User).filter(User.email == "elena.rostova@example.com").first()
    elena_patient = db.query(Patient).filter(Patient.user_id == elena.id).first()
    db.close()

    marcus_token = _login_token("marcus.vance@example.com", "OtherPass123!")
    headers = {"Authorization": f"Bearer {marcus_token}"}

    payload = {
        "patient_id": elena_patient.id,
        "extracted_text": "Sample text",
    }

    response = client.post("/api/agent-workflow/run", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


# ==========================================
# 2. Workflow Status & State Tests
# ==========================================

@pytest.mark.asyncio
async def test_get_workflow_status():
    token = _login_token("elena.rostova@example.com", "PatientPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    elena = db.query(User).filter(User.email == "elena.rostova@example.com").first()
    db.close()

    # Register workflow in manager
    wf_id = "wf-test-status-01"
    state = WorkflowState(
        workflow_id=wf_id,
        user_id=elena.id,
        patient_name="Elena Rostova",
        document_type="Lab Report",
        workflow_type=WorkflowType.LAB_REPORT,
        status=WorkflowStatus.COMPLETED
    )
    workflow_manager.register_workflow(state)

    response = client.get(f"/api/agent-workflow/{wf_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == wf_id
    assert data["patient_name"] == "Elena Rostova"
    assert data["status"] == "COMPLETED"


def test_get_invalid_workflow_404():
    token = _login_token("elena.rostova@example.com", "PatientPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/agent-workflow/wf-non-existent-999", headers=headers)
    assert response.status_code == 404


def test_cross_user_workflow_isolation():
    db = TestingSessionLocal()
    elena = db.query(User).filter(User.email == "elena.rostova@example.com").first()
    db.close()

    token_marcus = _login_token("marcus.vance@example.com", "OtherPass123!")

    # Workflow belongs to Elena, Marcus tries to read it
    wf_id = "wf-test-isolation-01"
    state = WorkflowState(
        workflow_id=wf_id,
        user_id=elena.id,
        status=WorkflowStatus.COMPLETED
    )
    workflow_manager.register_workflow(state)

    headers_marcus = {"Authorization": f"Bearer {token_marcus}"}
    response = client.get(f"/api/agent-workflow/{wf_id}", headers=headers_marcus)
    assert response.status_code == 403


# ==========================================
# 3. Real-Time SSE Stream Tests
# ==========================================

@pytest.mark.asyncio
async def test_workflow_sse_streaming():
    wf_id = "wf-test-stream-01"
    state = WorkflowState(
        workflow_id=wf_id,
        user_id=1,
        status=WorkflowStatus.IN_PROGRESS
    )
    workflow_manager.register_workflow(state)

    # Emit events including completion
    await workflow_manager.emit_event(wf_id, "workflow_started", {"workflow_id": wf_id, "status": "IN_PROGRESS"})
    await workflow_manager.emit_event(wf_id, "agent_started", {"agent": "patient_intake", "status": "RUNNING"})
    await workflow_manager.emit_event(wf_id, "agent_completed", {"agent": "patient_intake", "status": "COMPLETED", "duration_ms": 5.2})
    await workflow_manager.emit_event(wf_id, "workflow_completed", {"workflow_id": wf_id, "status": "COMPLETED"})

    # Connect SSE stream via subscription generator
    stream_gen = workflow_manager.subscribe(wf_id)
    collected_events = []

    async for chunk in stream_gen:
        collected_events.append(chunk)

    combined_output = "".join(collected_events)
    assert "event: workflow_started" in combined_output
    assert "event: agent_started" in combined_output
    assert "event: agent_completed" in combined_output
    assert "event: workflow_completed" in combined_output


@pytest.mark.asyncio
async def test_workflow_stream_isolation():
    wf_a = "wf-test-stream-a"
    wf_b = "wf-test-stream-b"

    state_a = WorkflowState(workflow_id=wf_a, user_id=1)
    state_b = WorkflowState(workflow_id=wf_b, user_id=2)

    workflow_manager.register_workflow(state_a)
    workflow_manager.register_workflow(state_b)

    await workflow_manager.emit_event(wf_a, "workflow_started", {"tag": "ONLY_IN_A"})
    await workflow_manager.emit_event(wf_a, "workflow_completed", {"tag": "DONE_A"})

    await workflow_manager.emit_event(wf_b, "workflow_started", {"tag": "ONLY_IN_B"})
    await workflow_manager.emit_event(wf_b, "workflow_completed", {"tag": "DONE_B"})

    # Check subscriber for WF A
    events_a = []
    async for chunk in workflow_manager.subscribe(wf_a):
        events_a.append(chunk)

    str_a = "".join(events_a)
    assert "ONLY_IN_A" in str_a
    assert "ONLY_IN_B" not in str_a


# ==========================================
# 4. Human-in-the-Loop Review Tests
# ==========================================

def test_human_review_approval_flow():
    # Setup critical escalated workflow
    wf_id = "wf-test-review-01"
    state = WorkflowState(
        workflow_id=wf_id,
        patient_name="Elena Rostova",
        status=WorkflowStatus.DOCTOR_REVIEW_REQUIRED,
        escalation_required=True,
        escalation_reason="Critical panic value: Hemoglobin (5.1 g/dL)"
    )
    workflow_manager.register_workflow(state)

    # 1. Doctor approves the review
    doc_token = _login_token("dr.finch@apollo.com", "DoctorPass123!")
    headers = {"Authorization": f"Bearer {doc_token}"}

    payload = {
        "decision": "APPROVE",
        "notes": "Verified critical anemia pattern. Patient contacted for urgent transfusion evaluation."
    }

    response = client.post(f"/api/agent-workflow/{wf_id}/review", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "APPROVE"
    assert data["status"] == "COMPLETED"
    assert "Dr. Alistair Finch" in data["reviewer_name"]

    # Verify state in manager is now COMPLETED
    updated_state = workflow_manager.get_workflow(wf_id)
    assert updated_state.status == WorkflowStatus.COMPLETED
    assert updated_state.escalation_required is False
    assert len(updated_state.audit_trail) >= 1


def test_human_review_unauthorized_user():
    wf_id = "wf-test-review-02"
    state = WorkflowState(
        workflow_id=wf_id,
        status=WorkflowStatus.DOCTOR_REVIEW_REQUIRED
    )
    workflow_manager.register_workflow(state)

    # Regular USER tries to review/approve workflow
    user_token = _login_token("elena.rostova@example.com", "PatientPass123!")
    headers = {"Authorization": f"Bearer {user_token}"}

    payload = {"decision": "APPROVE"}
    response = client.post(f"/api/agent-workflow/{wf_id}/review", json=payload, headers=headers)
    assert response.status_code == 403


# ==========================================
# 5. Patient Workflow History Tests
# ==========================================

def test_patient_workflow_history_endpoint():
    token = _login_token("elena.rostova@example.com", "PatientPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    db = TestingSessionLocal()
    elena = db.query(User).filter(User.email == "elena.rostova@example.com").first()
    patient = db.query(Patient).filter(Patient.user_id == elena.id).first()
    db.close()
    assert patient is not None

    # Register 2 workflows for Elena's patient ID
    wf1 = WorkflowState(
        workflow_id="wf-hist-01",
        patient_id=patient.id,
        user_id=elena.id,
        document_type="Lab Report",
        workflow_type=WorkflowType.LAB_REPORT,
        status=WorkflowStatus.COMPLETED
    )
    wf2 = WorkflowState(
        workflow_id="wf-hist-02",
        patient_id=patient.id,
        user_id=elena.id,
        document_type="Prescription",
        workflow_type=WorkflowType.PRESCRIPTION,
        status=WorkflowStatus.DOCTOR_REVIEW_REQUIRED,
        escalation_required=True
    )
    workflow_manager.register_workflow(wf1)
    workflow_manager.register_workflow(wf2)

    response = client.get(f"/api/agent-workflow/patient/{patient.id}/history", headers=headers)
    assert response.status_code == 200
    hist = response.json()
    assert len(hist) >= 2
    wf_ids = [item["workflow_id"] for item in hist]
    assert "wf-hist-01" in wf_ids
    assert "wf-hist-02" in wf_ids
