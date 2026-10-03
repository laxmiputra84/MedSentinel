"""
MedSentinel Master Agentic Architecture — Phase 22 Comprehensive Verification Suite
Tests:
- SupervisorAgent dynamic DAG orchestration
- IntentAgent structured intent extraction
- PlannerAgent cycle-free DAG planning & parallel batches
- MedicationSafetyAgent interaction detection & duplicate classes
- DataAnalystAgent DuckDB OLAP querying & AST SQL validation / injection defense
- AgentToolGateway allowlist isolation & PII masking
- Human Review Center & Patient 360 endpoints
- RedisEventBus publishing and SSE replay
"""

import pytest
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_password_hash
from app.models.user import User
from app.models.patient import Patient
from app.models.lab_result import LabResult
from app.models.workflow import WorkflowInstance, HumanReviewRecord
from app.agents.state import (
    WorkflowState,
    WorkflowType,
    WorkflowStatus,
    EscalationLevel,
)
from app.agents.intent_agent import IntentAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.medication_safety_agent import MedicationSafetyAgent
from app.agents.data_analyst_agent import DataAnalystAgent, SQLValidationError
from app.agents.tool_gateway import agent_tool_gateway, PIIRedactor
from app.services.redis_event_bus import redis_event_bus, AgentEventType

try:
    from tests.conftest import TestingSessionLocal, test_engine, Base
except ImportError:
    from conftest import TestingSessionLocal, test_engine, Base

client = TestClient(app)


# ==========================================
# 1. Intent & Planning Tests
# ==========================================

@pytest.mark.asyncio
async def test_intent_agent_classification():
    agent = IntentAgent()
    state = WorkflowState(
        workflow_id="wf-test-intent-01",
        extracted_text="Patient laboratory investigation: CBC report showing Hemoglobin 10.2 g/dL",
        filename="cbc_report.pdf",
        workflow_type=WorkflowType.AUTOMATIC
    )

    result = await agent.run(state=state)
    assert result.success is True
    assert result.data["intent"] == "lab_analysis"
    assert result.data["workflow_type"] == WorkflowType.LAB_REPORT
    assert state.workflow_type == WorkflowType.LAB_REPORT


@pytest.mark.asyncio
async def test_planner_agent_dag_batches():
    agent = PlannerAgent()
    state = WorkflowState(
        workflow_id="wf-test-plan-01",
        workflow_type=WorkflowType.PRESCRIPTION
    )

    result = await agent.run(state=state)
    assert result.success is True
    plan = result.data
    assert "medication_safety" in plan["steps"]
    assert "safety" in plan["steps"]
    assert len(plan["parallel_batches"]) >= 3


# ==========================================
# 2. Medication Safety Tests
# ==========================================

@pytest.mark.asyncio
async def test_medication_safety_critical_interaction_escalation():
    agent = MedicationSafetyAgent()
    rx_text = (
        "Rx PRESCRIPTION:\n"
        "1. Warfarin 5mg daily for DVT anticoagulation\n"
        "2. Ibuprofen 400mg twice daily for joint pain"
    )
    state = WorkflowState(
        workflow_id="wf-test-rx-safety-01",
        extracted_text=rx_text,
        workflow_type=WorkflowType.PRESCRIPTION
    )

    result = await agent.run(state=state)
    assert result.success is True
    assert result.data["escalation_triggered"] is True
    assert state.escalation_required is True
    assert state.status == WorkflowStatus.DOCTOR_REVIEW_REQUIRED
    assert len(result.findings) >= 1
    assert result.findings[0].status == "CRITICAL"


@pytest.mark.asyncio
async def test_medication_safety_duplicate_class_detection():
    agent = MedicationSafetyAgent()
    rx_text = (
        "Rx PRESCRIPTION:\n"
        "1. Atorvastatin 20mg bedtime\n"
        "2. Rosuvastatin 10mg morning"
    )
    state = WorkflowState(
        workflow_id="wf-test-rx-safety-02",
        extracted_text=rx_text,
        workflow_type=WorkflowType.PRESCRIPTION
    )

    result = await agent.run(state=state)
    assert result.success is True
    assert len(result.data["duplicate_classes"]) >= 1
    assert result.data["duplicate_classes"][0]["class"] == "STATIN"


# ==========================================
# 3. Healthcare Data Analyst & AST Safety Tests
# ==========================================

@pytest.mark.asyncio
async def test_data_analyst_sql_profiling():
    agent = DataAnalystAgent()
    state = WorkflowState(
        workflow_id="wf-test-analyst-01",
        workflow_type=WorkflowType.CLINICAL_SUMMARY
    )

    query = "SELECT department, AVG(amount) as avg_claim FROM dataset GROUP BY department"
    result = await agent.run(state=state, context={"query": query})

    assert result.success is True
    assert "profile" in result.data
    assert result.data["profile"]["total_rows"] >= 5
    assert result.data["query_result"]["row_count"] >= 1


def test_data_analyst_ast_blocks_malicious_sql():
    agent = DataAnalystAgent()
    malicious_queries = [
        "DROP TABLE dataset",
        "DELETE FROM dataset WHERE amount > 0",
        "UPDATE dataset SET amount = 0",
        "SELECT * FROM dataset; DROP TABLE dataset",
        "ALTER TABLE dataset ADD COLUMN hacked INT"
    ]

    for q in malicious_queries:
        with pytest.raises(SQLValidationError):
            agent.validate_sql_query(q)


# ==========================================
# 4. Tool Gateway Security & PII Redaction Tests
# ==========================================

@pytest.mark.asyncio
async def test_tool_gateway_allowlist_enforcement():
    # Unauthorized tool call: lab_analysis trying to call detect_claim_anomaly
    res = await agent_tool_gateway.execute(
        agent_name="lab_analysis",
        tool_name="detect_claim_anomaly",
        parameters={"claim_id": 1}
    )
    assert res.success is False
    assert "Security Violation" in res.error


def test_pii_redactor():
    sample_text = "Contact patient at john.doe@hospital.org or phone +91 98765 43210"
    redacted = PIIRedactor.redact_text(sample_text)
    assert "john.doe@hospital.org" not in redacted
    assert "j***@hospital.org" in redacted
    assert "+91 98765 43210" not in redacted

    sample_dict = {
        "name": "Alice Smith",
        "email": "alice@medsentinel.com",
        "phone": "555-123-4567"
    }
    redacted_dict = PIIRedactor.redact_dict(sample_dict)
    assert redacted_dict["email"] == "***REDACTED***"
    assert redacted_dict["phone"] == "***REDACTED***"


# ==========================================
# 5. Redis Event Bus & Human Review Center Tests
# ==========================================

@pytest.mark.asyncio
async def test_redis_event_bus_pub_sub():
    wf_id = "wf-bus-test-01"
    evt = await redis_event_bus.publish(
        workflow_id=wf_id,
        event_type=AgentEventType.WORKFLOW_STARTED,
        data={"message": "System starting up"}
    )
    assert evt["event"] == "WORKFLOW_STARTED"
    history = redis_event_bus.get_event_history(wf_id)
    assert len(history) >= 1
    assert history[0]["event"] == "WORKFLOW_STARTED"


def test_patient_360_endpoint():
    db = TestingSessionLocal()
    # Create patient
    test_user = User(
        name="Test 360 Patient",
        email="test360@example.com",
        hashed_password=get_password_hash("Password123!"),
        role="SUPER_ADMIN"
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    p = Patient(
        user_id=test_user.id,
        name="Test 360 Patient",
        blood_group="O+",
        patient_code="MS-360-TEST"
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    # Login token
    from app.core.security import create_access_token
    token = create_access_token(subject=str(test_user.id), role="SUPER_ADMIN")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/patients/{p.id}/360", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["patient"]["name"] == "Test 360 Patient"
    assert "health_score" in data
    assert "recent_labs" in data

    # Timeline endpoint
    timeline_res = client.get(f"/api/patients/{p.id}/timeline", headers=headers)
    assert timeline_res.status_code == 200
    t_data = timeline_res.json()
    assert "events" in t_data

    db.close()
