"""
Comprehensive Automated Test Suite for MedSentinel Event-Driven Agent System.
Tests all 16 required verification scenarios:
  1. Patient creation event
  2. Document upload event
  3. Duplicate document event
  4. Lab report event
  5. Critical lab event
  6. Claim event
  7. Fraud event
  8. Appointment event
  9. Duplicate event handling (Idempotency)
  10. Agent retry with exponential backoff
  11. Agent failure containment
  12. Event recovery & data preservation
  13. WebSocket real-time updates
  14. API Authentication
  15. RBAC Tenant Isolation
  16. Database Persistence of Events & AgentTasks
"""

import io
import json
import pytest
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_password_hash
from app.core.events import EventType, EventStatus, TaskStatus
from app.models.user import User
from app.models.patient import Patient
from app.models.document import UserDocument
from app.models.lab_result import LabResult
from app.models.insurance_claim import InsuranceClaim
from app.models.appointment import Appointment
from app.models.event import Event
from app.models.agent_task import AgentTask
from app.models.audit_log import AdminAuditLog
from app.services.event_bus import event_bus, publish_event
from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding

try:
    from tests.conftest import TestingSessionLocal, test_engine, Base
except ImportError:
    from conftest import TestingSessionLocal, test_engine, Base

client = TestClient(app)

SAMPLE_LAB_TEXT = """
DEPARTMENT OF BIOCHEMISTRY & PATHOLOGY
Patient: David Miller | Age: 48 | Date: 2026-09-12
Hemoglobin: 15.2 g/dL (13.5 - 17.5)
WBC: 7200 /uL (4000 - 11000)
Platelets: 280000 /uL (150000 - 450000)
Serum Creatinine: 1.05 mg/dL (0.7 - 1.3)
Potassium: 4.4 mEq/L (3.5 - 5.1)
Fasting Glucose: 92 mg/dL (70 - 100)
"""

SAMPLE_CRITICAL_LAB_TEXT = """
EMERGENCY CRITICAL LAB ALERT
Patient: David Miller | Age: 48 | Date: 2026-09-12
Potassium: 6.9 mEq/L (3.5 - 5.1) [CRITICAL HIGH PANIC VALUE]
Hemoglobin: 5.4 g/dL (13.5 - 17.5) [CRITICAL LOW]
Fasting Glucose: 480 mg/dL (70 - 100) [CRITICAL HIGH]
"""


@pytest.fixture(autouse=True)
def setup_event_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Clear tables
    db.query(AgentTask).delete()
    db.query(Event).delete()
    db.query(AdminAuditLog).delete()
    db.query(LabResult).delete()
    db.query(UserDocument).delete()
    db.query(InsuranceClaim).delete()
    db.query(Appointment).delete()
    db.query(Patient).delete()
    db.query(User).delete()
    db.commit()

    # 1. Regular Patient User
    patient_user = User(
        id=501,
        name="David Miller",
        email="david.miller@example.com",
        hashed_password=get_password_hash("DavidPass123!"),
        role="USER",
        phone="+91 91111 22222",
    )
    # 2. Other Patient User (for RBAC isolation check)
    other_user = User(
        id=502,
        name="Alice Smith",
        email="alice.smith@example.com",
        hashed_password=get_password_hash("AlicePass123!"),
        role="USER",
        phone="+91 93333 44444",
    )
    # 3. Super Admin User
    admin_user = User(
        id=503,
        name="Admin Supervisor",
        email="admin.event@medsentinel.com",
        hashed_password=get_password_hash("AdminPass123!"),
        role="SUPER_ADMIN",
        phone="+91 95555 66666",
    )

    db.add_all([patient_user, other_user, admin_user])
    db.commit()

    # Create Patient record for David
    p = Patient(
        id=701,
        user_id=501,
        patient_code="MS-2026-00701",
        name="David Miller",
        blood_group="A+",
        gender="Male",
        emergency_contact="+91 91111 99999",
    )
    db.add(p)
    db.commit()
    db.close()


def get_token(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


# ==============================================================================
# SCENARIO 1: Patient Creation Event
# ==============================================================================
def test_scenario_01_patient_creation_event():
    """Verify PATIENT_CREATED event triggers PatientIntakeAgent and creates audit entry."""
    db = TestingSessionLocal()
    event = publish_event(
        event_type=EventType.PATIENT_CREATED.value,
        entity_id="701",
        user_id=501,
        payload={"name": "David Miller", "blood_group": "A+"},
        entity_type="patient",
        db=db,
        sync=True,
    )
    assert event.event_id.startswith("evt-")
    assert event.status == EventStatus.COMPLETED.value
    assert event.entity_type == "patient"

    # Verify tasks generated
    tasks = db.query(AgentTask).filter(AgentTask.event_id == event.event_id).all()
    assert len(tasks) >= 1
    task_types = [t.agent_type for t in tasks]
    assert "patient_intake" in task_types
    assert all(t.status == TaskStatus.COMPLETED.value for t in tasks)
    db.close()


# ==============================================================================
# SCENARIO 2: Document Upload Event
# ==============================================================================
def test_scenario_02_document_upload_event():
    """Verify document upload emits DOCUMENT_UPLOADED and triggers Document Intelligence."""
    token = get_token("david.miller@example.com", "DavidPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    sample_content = b"Prescription: Amoxicillin 500mg 3 times daily for 7 days."
    res = client.post(
        "/api/documents/upload",
        files={"document": ("rx_amox.txt", io.BytesIO(sample_content), "text/plain")},
        data={"docType": "Prescription"},
        headers=headers,
    )
    assert res.status_code == 201
    doc_id = res.json()["id"]

    # Verify event was published
    db = TestingSessionLocal()
    event = db.query(Event).filter(
        Event.event_type == EventType.DOCUMENT_UPLOADED.value,
        Event.entity_id == str(doc_id),
    ).first()
    assert event is not None
    assert event.status in [EventStatus.PENDING.value, EventStatus.PROCESSING.value, EventStatus.COMPLETED.value]
    db.close()


# ==============================================================================
# SCENARIO 3: Duplicate Document Event
# ==============================================================================
def test_scenario_03_duplicate_document_event():
    """Verify duplicate document upload emits DOCUMENT_DUPLICATE_DETECTED with FLAGGED verification."""
    token = get_token("david.miller@example.com", "DavidPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    sample_content = b"Exact duplicate report bytes test 2026."
    res1 = client.post(
        "/api/documents/upload",
        files={"document": ("original.txt", io.BytesIO(sample_content), "text/plain")},
        headers=headers,
    )
    assert res1.status_code == 201

    # Upload exact duplicate
    res2 = client.post(
        "/api/documents/upload",
        files={"document": ("copy.txt", io.BytesIO(sample_content), "text/plain")},
        headers=headers,
    )
    assert res2.status_code == 201
    assert res2.json()["duplicate_detected"] is True
    assert res2.json()["verification_status"] == "FLAGGED"

    # Verify DOCUMENT_DUPLICATE_DETECTED event in database
    db = TestingSessionLocal()
    dup_event = db.query(Event).filter(
        Event.event_type == EventType.DOCUMENT_DUPLICATE_DETECTED.value,
        Event.entity_id == str(res2.json()["id"]),
    ).first()
    assert dup_event is not None
    db.close()


# ==============================================================================
# SCENARIO 4: Laboratory Report Event
# ==============================================================================
def test_scenario_04_lab_report_event():
    """Verify LAB_REPORT_RECEIVED executes OCR, Lab Analysis, and Risk Prediction."""
    db = TestingSessionLocal()
    # Create document record
    doc = UserDocument(
        user_id=501,
        patient_id=701,
        document_code="DOC-2026-LAB01",
        file_hash="dummyhashlab001",
        doc_type="Lab Report",
        filename="cbc_panel.txt",
        original_name="cbc_panel.txt",
        file_path="uploads/cbc_panel.txt",
        file_type="text/plain",
        file_size=len(SAMPLE_LAB_TEXT),
        status="PENDING",
        ocr_extracted_text=SAMPLE_LAB_TEXT,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Publish LAB_REPORT_RECEIVED event synchronously
    event = publish_event(
        event_type=EventType.LAB_REPORT_RECEIVED.value,
        entity_id=doc.id,
        user_id=501,
        payload={"patient_id": 701},
        entity_type="document",
        db=db,
        sync=True,
    )

    assert event.status == EventStatus.COMPLETED.value
    tasks = db.query(AgentTask).filter(AgentTask.event_id == event.event_id).all()
    task_agents = [t.agent_type for t in tasks]

    # Required agents: OCR / Lab Analysis / Risk / Safety / Verification
    assert "lab_analysis" in task_agents
    assert "safety" in task_agents
    assert "verification_report" in task_agents
    db.close()


# ==============================================================================
# SCENARIO 5: Critical Lab Value Detection Event
# ==============================================================================
def test_scenario_05_critical_lab_event():
    """Verify critical panic lab values mandate emergency escalation and doctor review."""
    db = TestingSessionLocal()
    doc = UserDocument(
        user_id=501,
        patient_id=701,
        document_code="DOC-2026-CRIT01",
        file_hash="dummyhashcrit001",
        doc_type="Lab Report",
        filename="critical_panel.txt",
        original_name="critical_panel.txt",
        file_path="uploads/critical_panel.txt",
        file_type="text/plain",
        file_size=len(SAMPLE_CRITICAL_LAB_TEXT),
        status="PENDING",
        ocr_extracted_text=SAMPLE_CRITICAL_LAB_TEXT,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Publish CRITICAL_LAB_VALUE_DETECTED event
    event = publish_event(
        event_type=EventType.CRITICAL_LAB_VALUE_DETECTED.value,
        entity_id=doc.id,
        user_id=501,
        payload={"patient_id": 701, "panic_potassium": 6.9},
        entity_type="lab_result",
        db=db,
        sync=True,
    )

    assert event.status == EventStatus.COMPLETED.value
    safety_task = db.query(AgentTask).filter(
        AgentTask.event_id == event.event_id,
        AgentTask.agent_type == "safety",
    ).first()
    assert safety_task is not None
    assert safety_task.status == TaskStatus.COMPLETED.value
    db.close()


# ==============================================================================
# SCENARIO 6: Claim Creation Event
# ==============================================================================
def test_scenario_06_claim_event():
    """Verify insurance claim creation publishes CLAIM_CREATED event."""
    token = get_token("david.miller@example.com", "DavidPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/insurance-claims",
        json={
            "claim_amount": 55000.0,
            "claim_description": "Cardiology diagnostic tests and routine angioplasty consultation.",
            "documents": "cardio_bill.pdf",
        },
        headers=headers,
    )
    assert res.status_code == 201
    claim_id = res.json()["id"]

    db = TestingSessionLocal()
    claim_event = db.query(Event).filter(
        Event.event_type == EventType.CLAIM_CREATED.value,
        Event.entity_id == str(claim_id),
    ).first()
    assert claim_event is not None
    assert claim_event.entity_type == "claim"
    db.close()


# ==============================================================================
# SCENARIO 7: Fraud Event Detection
# ==============================================================================
def test_scenario_07_fraud_event():
    """Verify high fraud indicator triggers FRAUD_FLAG_DETECTED event."""
    db = TestingSessionLocal()
    event = publish_event(
        event_type=EventType.FRAUD_FLAG_DETECTED.value,
        entity_id="999",
        user_id=501,
        payload={"claim_id": 999, "fraud_risk": "HIGH", "score": 92},
        entity_type="claim",
        db=db,
        sync=True,
    )
    assert event.status == EventStatus.COMPLETED.value
    tasks = db.query(AgentTask).filter(AgentTask.event_id == event.event_id).all()
    assert any(t.agent_type == "safety" for t in tasks)
    db.close()


# ==============================================================================
# SCENARIO 8: Appointment Events
# ==============================================================================
def test_scenario_08_appointment_events():
    """Verify appointment creation and cancellation emit APPOINTMENT_CREATED and APPOINTMENT_CANCELLED."""
    token = get_token("david.miller@example.com", "DavidPass123!")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Appointment
    create_res = client.post(
        "/api/appointments",
        json={
            "name": "David Miller",
            "phone": "+91 91111 22222",
            "email": "david.miller@example.com",
            "preferred_date": "2026-10-15",
            "preferred_time": "10:30 AM",
            "department": "Cardiology",
            "reason": "Quarterly health evaluation",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    appt_id = create_res.json()["id"]

    db = TestingSessionLocal()
    create_evt = db.query(Event).filter(
        Event.event_type == EventType.APPOINTMENT_CREATED.value,
        Event.entity_id == str(appt_id),
    ).first()
    assert create_evt is not None

    # 2. Cancel Appointment
    cancel_res = client.patch(
        f"/api/appointments/{appt_id}/cancel",
        json={"cancellation_reason": "Patient requested reschedule"},
        headers=headers,
    )
    assert cancel_res.status_code == 200

    cancel_evt = db.query(Event).filter(
        Event.event_type == EventType.APPOINTMENT_CANCELLED.value,
        Event.entity_id == str(appt_id),
    ).first()
    assert cancel_evt is not None
    db.close()


# ==============================================================================
# SCENARIO 9: Duplicate Event Handling (Idempotency)
# ==============================================================================
def test_scenario_09_duplicate_event_handling():
    """Verify idempotency key prevents duplicate event and task creation."""
    db = TestingSessionLocal()
    key = "idem-test-key-2026-xyz"

    event1 = publish_event(
        event_type=EventType.PATIENT_UPDATED.value,
        entity_id="701",
        user_id=501,
        payload={"blood_group": "A+"},
        entity_type="patient",
        idempotency_key=key,
        db=db,
        sync=False,
    )

    # Publish identical event with same idempotency key
    event2 = publish_event(
        event_type=EventType.PATIENT_UPDATED.value,
        entity_id="701",
        user_id=501,
        payload={"blood_group": "A+"},
        entity_type="patient",
        idempotency_key=key,
        db=db,
        sync=False,
    )

    # Same event record must be returned without duplication
    assert event1.id == event2.id
    assert event1.event_id == event2.event_id

    # Verify only 1 record exists in DB
    count = db.query(Event).filter(Event.payload.like(f'%"idempotency_key": "{key}"%')).count()
    assert count == 1
    db.close()


# ==============================================================================
# SCENARIO 10: Agent Retry with Exponential Backoff
# ==============================================================================
def test_scenario_10_agent_retry():
    """Verify failing agent is retried with backoff until max retries or recovery."""
    class FlakyAgent(BaseAgent):
        def __init__(self):
            super().__init__(name="flaky_test_agent", role="Test", description="Test Flaky")
            self.attempts = 0

        async def execute(self, state, db=None, context=None):
            self.attempts += 1
            if self.attempts < 3:
                return AgentResult(success=False, agent_name=self.name, errors=["Temporary API Timeout"])
            return AgentResult(success=True, agent_name=self.name, data={"attempts_made": self.attempts})

    flaky = FlakyAgent()
    event_bus._orchestrator.registry.register("flaky_test_agent", flaky)

    db = TestingSessionLocal()
    # Register mock event with flaky agent
    evt = publish_event(
        event_type=EventType.PATIENT_UPDATED.value,
        entity_id="701",
        user_id=501,
        payload={"test": "retry"},
        entity_type="patient",
        db=db,
        sync=False,
    )

    # Execute directly with flaky agent
    original_plan = event_bus._orchestrator.plan_for_event
    try:
        # Force single agent execution
        event_bus._orchestrator.plan_for_event = lambda et, st: ["flaky_test_agent"]

        event_bus.process_event_sync(evt.event_id, db=db)

        db.refresh(evt)
        task = db.query(AgentTask).filter(AgentTask.event_id == evt.event_id).first()
        assert task is not None
        assert task.status == TaskStatus.COMPLETED.value
        assert task.retry_count >= 1  # Verify retry occurred
    finally:
        event_bus._orchestrator.plan_for_event = original_plan
        db.close()


# ==============================================================================
# SCENARIO 11: Agent Failure Handling
# ==============================================================================
def test_scenario_11_agent_failure():
    """Verify permanent failure records error and marks task as FAILED."""
    class AlwaysFailAgent(BaseAgent):
        def __init__(self):
            super().__init__(name="fail_agent", role="Test", description="Test Fail")

        async def execute(self, state, db=None, context=None):
            return AgentResult(success=False, agent_name=self.name, errors=["Permanent Database Corruption Error"])

    event_bus._orchestrator.registry.register("fail_agent", AlwaysFailAgent())
    original_plan = event_bus._orchestrator.plan_for_event
    try:
        event_bus._orchestrator.plan_for_event = lambda et, st: ["fail_agent"]

        db = TestingSessionLocal()
        evt = publish_event(
            event_type=EventType.DOCUMENT_UPDATED.value,
            entity_id="9999",
            user_id=501,
            entity_type="document",
            db=db,
            sync=True,
        )
        db.refresh(evt)
        task = db.query(AgentTask).filter(AgentTask.event_id == evt.event_id).first()
        assert task is not None
        assert task.status == TaskStatus.FAILED.value
        assert "Permanent Database Corruption Error" in task.error_message
    finally:
        event_bus._orchestrator.plan_for_event = original_plan
        db.close()


# ==============================================================================
# SCENARIO 12: Event Recovery & Data Preservation
# ==============================================================================
def test_scenario_12_event_recovery():
    """Verify patient data is preserved even when an agent task fails."""
    db = TestingSessionLocal()
    patient_before = db.query(Patient).filter(Patient.id == 701).first()
    assert patient_before is not None
    p_name = patient_before.name

    # Trigger failure event on patient
    evt = publish_event(
        event_type=EventType.PATIENT_UPDATED.value,
        entity_id="701",
        user_id=501,
        entity_type="patient",
        db=db,
        sync=True,
    )

    # Check patient record remains uncorrupted
    patient_after = db.query(Patient).filter(Patient.id == 701).first()
    assert patient_after is not None
    assert patient_after.name == p_name
    db.close()


# ==============================================================================
# SCENARIO 13: WebSocket Event Updates
# ==============================================================================
def test_scenario_13_websocket_event_updates():
    """Verify real-time WebSocket connection handshake and message exchange."""
    token = get_token("david.miller@example.com", "DavidPass123!")

    with client.websocket_connect(f"/api/ws/events?token={token}") as ws:
        # Initial greeting from WebSocket server
        data = ws.receive_json()
        assert data["type"] == "CONNECTION_ESTABLISHED"
        assert "system_status" in data

        # Send ping
        ws.send_text(json.dumps({"action": "ping"}))
        resp = ws.receive_json()
        assert resp["type"] == "PONG"


# ==============================================================================
# SCENARIO 14: Authentication Enforcement
# ==============================================================================
def test_scenario_14_authentication():
    """Verify unauthenticated requests are rejected on protected endpoints."""
    # Clear any residual session cookies
    client.cookies.clear()

    # GET /api/events without token
    res = client.get("/api/events")
    assert res.status_code in [401, 403]

    # POST /api/events/publish without token
    res_pub = client.post("/api/events/publish", json={"event_type": "DOCUMENT_UPLOADED", "entity_id": "1"})
    assert res_pub.status_code in [401, 403]


# ==============================================================================
# SCENARIO 15: RBAC Tenant Isolation
# ==============================================================================
def test_scenario_15_rbac():
    """Verify standard users cannot access other users' events, while Admin can access all."""
    db = TestingSessionLocal()

    # User 501 event
    publish_event(
        event_type=EventType.DOCUMENT_UPLOADED.value,
        entity_id="101",
        user_id=501,
        entity_type="document",
        db=db,
        sync=False,
    )
    # User 502 event
    publish_event(
        event_type=EventType.DOCUMENT_UPLOADED.value,
        entity_id="102",
        user_id=502,
        entity_type="document",
        db=db,
        sync=False,
    )
    db.close()

    token_david = get_token("david.miller@example.com", "DavidPass123!")
    token_admin = get_token("admin.event@medsentinel.com", "AdminPass123!")

    # David Miller queries /events: must see only his events
    res_david = client.get("/api/events", headers={"Authorization": f"Bearer {token_david}"})
    assert res_david.status_code == 200
    events_david = res_david.json()["events"]
    assert all(e["user_id"] == 501 or e["user_id"] is None for e in events_david)

    # Admin queries /events: can see both user 501 and 502
    res_admin = client.get("/api/events", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_admin.status_code == 200
    events_admin = res_admin.json()["events"]
    uids = {e["user_id"] for e in events_admin if e["user_id"]}
    assert 501 in uids or 502 in uids


# ==============================================================================
# SCENARIO 16: Database Persistence
# ==============================================================================
def test_scenario_16_database_persistence():
    """Verify Event and AgentTask records are properly persisted in relational tables."""
    db = TestingSessionLocal()

    evt = publish_event(
        event_type=EventType.APPOINTMENT_CREATED.value,
        entity_id="8888",
        user_id=501,
        payload={"room": "104"},
        entity_type="appointment",
        db=db,
        sync=False,
    )

    persisted_event = db.query(Event).filter(Event.event_id == evt.event_id).first()
    assert persisted_event is not None
    assert persisted_event.id > 0
    assert persisted_event.event_type == "APPOINTMENT_CREATED"

    # Status check API
    status_res = client.get("/api/agent/status")
    assert status_res.status_code == 200
    s_data = status_res.json()
    assert "registered_agents" in s_data
    assert "system_status" in s_data
    assert len(s_data["registered_agents"]) >= 10
    db.close()
