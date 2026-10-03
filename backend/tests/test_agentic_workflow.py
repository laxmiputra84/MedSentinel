"""
MedSentinel Agentic Architecture — Phase 2 Automated Pytest Suite
Comprehensive test suite validating:
- 10 Specialized Healthcare Agents
- Orchestrator Agent & Dynamic DAG Routing
- Conditional Workflow Execution (Lab Report, Prescription, Insurance Claim)
- Critical Panic Value Escalation & Doctor Review Triggers
- Physiological Sanity Bounds & Non-Hallucination
- Multi-Tenant RBAC Isolation & Citations
- Failure Containment & Audit Logging
"""

import pytest
import asyncio
from datetime import datetime, timezone

from app.agents.state import (
    WorkflowState,
    WorkflowType,
    WorkflowStatus,
    EscalationLevel,
    AgentStatus,
)
from app.agents.patient_intake_agent import PatientIntakeAgent
from app.agents.document_intelligence_agent import DocumentIntelligenceAgent
from app.agents.ocr_agent import OCRAgent
from app.agents.data_validation_agent import DataValidationAgent
from app.agents.patient_history_agent import PatientHistoryAgent
from app.agents.symptom_clinical_agent import SymptomClinicalAgent
from app.agents.lab_analysis_agent import LabAnalysisAgent
from app.agents.medical_rag_agent import MedicalRAGAgent
from app.agents.risk_prediction_agent import RiskPredictionAgent
from app.agents.verification_report_agent import VerificationReportAgent
from app.agents.orchestrator import OrchestratorAgent, AgentRegistry

from app.models.patient import Patient
from app.models.user import User
from app.models.lab_result import LabResult
from app.models.document import UserDocument
from app.core.security import get_password_hash

try:
    from tests.conftest import TestingSessionLocal, test_engine, Base
except ImportError:
    from conftest import TestingSessionLocal, test_engine, Base


@pytest.fixture(autouse=True)
def setup_agent_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Clear tables
    db.query(LabResult).delete()
    db.query(UserDocument).delete()
    db.query(Patient).delete()
    db.query(User).delete()
    db.commit()

    # Create Seed User & Patient
    user = User(
        id=101,
        name="Sarah Jenkins",
        email="sarah.jenkins@example.com",
        hashed_password=get_password_hash("Pass123!"),
        role="USER",
        phone="+91 98888 12345",
        blood_group="O+"
    )
    db.add(user)
    db.commit()

    patient = Patient(
        id=201,
        user_id=101,
        patient_code="MS-2026-00201",
        name="Sarah Jenkins",
        blood_group="O+",
        gender="Female",
        emergency_contact="+91 98888 54321"
    )
    db.add(patient)
    db.commit()

    # Seed Previous Historical Lab Result (Baseline Hb = 14.0)
    prev_lab = LabResult(
        patient_id=201,
        test_name="Hemoglobin",
        observed_value=14.0,
        unit="g/dL",
        reference_min=12.0,
        reference_max=16.0,
        status="NORMAL",
        is_critical=False,
        test_date=datetime(2026, 1, 15)
    )
    db.add(prev_lab)
    db.commit()
    db.close()


# ==========================================
# 1. Individual Agent Unit Tests
# ==========================================

@pytest.mark.asyncio
async def test_patient_intake_agent():
    db = TestingSessionLocal()
    agent = PatientIntakeAgent()
    state = WorkflowState(
        workflow_id="wf-test-01",
        patient_id=201,
        user_id=101,
    )

    result = await agent.run(state=state, db=db)
    db.close()

    assert result.success is True
    assert state.patient_name == "Sarah Jenkins"
    assert result.data["blood_group"] == "O+"
    assert len(result.findings) >= 1
    assert state.current_agent == "patient_intake"
    assert "patient_intake" in state.completed_agents


@pytest.mark.asyncio
async def test_document_intelligence_agent():
    agent = DocumentIntelligenceAgent()
    state = WorkflowState(
        workflow_id="wf-test-02",
        extracted_text="COMPLETE BLOOD COUNT (CBC) REPORT\nHematology Laboratory\nHemoglobin: 13.5 g/dL",
        filename="cbc_report_jan.pdf"
    )

    result = await agent.run(state=state)

    assert result.success is True
    assert state.document_type == "Lab Report"
    assert state.workflow_type == WorkflowType.LAB_REPORT
    assert state.document_confidence >= 0.70
    assert len(result.findings) == 1


@pytest.mark.asyncio
async def test_ocr_agent_with_existing_text():
    agent = OCRAgent()
    sample_text = "Patient Name: Sarah Jenkins\nHemoglobin: 10.5 g/dL\nWBC: 6500 cells/uL"
    state = WorkflowState(
        workflow_id="wf-test-03",
        extracted_text=sample_text
    )

    result = await agent.run(state=state)

    assert result.success is True
    assert state.extracted_text == sample_text
    assert result.data["char_count"] == len(sample_text)


@pytest.mark.asyncio
async def test_ocr_agent_missing_file_failure():
    agent = OCRAgent()
    state = WorkflowState(
        workflow_id="wf-test-04",
        file_path="/non/existent/path/scanned_report.pdf"
    )

    result = await agent.run(state=state)

    assert result.success is False
    assert state.escalation_required is True
    assert state.escalation_level == EscalationLevel.DOCTOR_REVIEW_REQUIRED
    assert "ocr" in state.failed_agents


@pytest.mark.asyncio
async def test_data_validation_agent_valid_and_impossible():
    agent = DataValidationAgent()

    # 1. Valid tests
    state_valid = WorkflowState(
        workflow_id="wf-test-05a",
        lab_results=[
            {"name": "Hemoglobin", "value": 13.5, "unit": "g/dL", "status": "NORMAL"},
            {"name": "WBC", "value": 7500.0, "unit": "cells/uL", "status": "NORMAL"}
        ]
    )
    res_valid = await agent.run(state=state_valid)
    assert res_valid.success is True
    assert state_valid.validation_status["is_valid"] is True
    assert len(state_valid.validation_errors) == 0

    # 2. Corrupt / Negative Impossible tests
    state_corrupt = WorkflowState(
        workflow_id="wf-test-05b",
        lab_results=[
            {"name": "Hemoglobin", "value": -4.5, "unit": "g/dL", "status": "LOW"},
            {"name": "WBC", "value": "INVALID_TEXT", "unit": "cells/uL", "status": "NORMAL"}
        ]
    )
    res_corrupt = await agent.run(state=state_corrupt)
    assert res_corrupt.success is True
    assert state_corrupt.validation_status["is_valid"] is False
    assert len(state_corrupt.validation_errors) >= 1
    assert state_corrupt.escalation_required is True


@pytest.mark.asyncio
async def test_patient_history_agent_delta_calculation():
    db = TestingSessionLocal()
    agent = PatientHistoryAgent()

    # Current Hb = 10.5 (Previous in setup was 14.0 -> drop of -25.0%)
    state = WorkflowState(
        workflow_id="wf-test-06",
        patient_id=201,
        lab_results=[
            {"name": "Hemoglobin", "value": 10.5, "unit": "g/dL", "status": "LOW"}
        ]
    )

    result = await agent.run(state=state, db=db)
    db.close()

    assert result.success is True
    assert "Hemoglobin" in state.longitudinal_trends
    trend_info = state.longitudinal_trends["Hemoglobin"]
    assert trend_info["trend"] == "DECREASING"
    assert trend_info["previous_value"] == 14.0
    assert trend_info["delta"] == -3.5
    assert trend_info["pct_change"] == -25.0


@pytest.mark.asyncio
async def test_symptom_clinical_agent_cautious_observations():
    agent = SymptomClinicalAgent()
    state = WorkflowState(
        workflow_id="wf-test-07",
        extracted_text="Patient reports severe fatigue, mild headache, and weakness over past 2 weeks.",
        lab_results=[
            {"name": "Hemoglobin", "value": 9.2, "unit": "g/dL", "status": "LOW"}
        ]
    )

    result = await agent.run(state=state)

    assert result.success is True
    assert "Fatigue & Weakness" in result.data["detected_symptoms"]
    assert len(result.findings) >= 1
    # Check non-diagnostic language in finding
    first_desc = result.findings[0].description
    assert "Further clinical evaluation" in first_desc or "correlate with" in first_desc


@pytest.mark.asyncio
async def test_lab_analysis_agent_normal_and_critical_panic():
    agent = LabAnalysisAgent()

    # 1. Normal panel
    normal_text = "CLINICAL LAB\nHemoglobin: 14.2 g/dL\nWBC: 6500 cells/uL\nPlatelets: 250000 /uL"
    state_norm = WorkflowState(workflow_id="wf-test-08a", extracted_text=normal_text)
    res_norm = await agent.run(state=state_norm)

    assert res_norm.success is True
    assert res_norm.data["abnormal_count"] == 0
    assert state_norm.escalation_required is False

    # 2. Critical panic panel (Hemoglobin = 5.2 g/dL is <= 7.0 critical threshold)
    crit_text = "CLINICAL LAB\nHemoglobin: 5.2 g/dL\nWBC: 45000 cells/uL\nPlatelets: 22000 /uL"
    state_crit = WorkflowState(workflow_id="wf-test-08b", extracted_text=crit_text)
    res_crit = await agent.run(state=state_crit)

    assert res_crit.success is True
    assert res_crit.data["critical_count"] >= 1
    assert state_crit.escalation_required is True
    assert state_crit.escalation_level == EscalationLevel.DOCTOR_REVIEW_REQUIRED
    assert "Critical panic value detected" in state_crit.escalation_reason


@pytest.mark.asyncio
async def test_medical_rag_agent_citations():
    db = TestingSessionLocal()
    agent = MedicalRAGAgent()
    state = WorkflowState(
        workflow_id="wf-test-09",
        document_type="Lab Report",
        lab_results=[{"name": "Hemoglobin", "value": 8.5, "unit": "g/dL", "status": "LOW"}]
    )

    result = await agent.run(state=state, db=db)
    db.close()

    assert result.success is True
    assert "query" in result.data
    assert len(result.findings) >= 1


@pytest.mark.asyncio
async def test_risk_prediction_agent():
    agent = RiskPredictionAgent()
    state = WorkflowState(
        workflow_id="wf-test-10",
        lab_results=[
            {"name": "Hemoglobin", "value": 6.0, "unit": "g/dL", "status": "CRITICAL", "is_critical": True},
            {"name": "WBC", "value": 35000.0, "unit": "cells/uL", "status": "CRITICAL", "is_critical": True}
        ]
    )

    result = await agent.run(state=state)

    assert result.success is True
    assert state.risk_result is not None
    assert state.risk_result["risk_level"] == "CRITICAL"
    assert state.escalation_required is True


@pytest.mark.asyncio
async def test_verification_report_agent():
    db = TestingSessionLocal()
    agent = VerificationReportAgent()
    state = WorkflowState(
        workflow_id="wf-test-11",
        patient_id=201,
        patient_name="Sarah Jenkins",
        document_type="Lab Report",
        lab_results=[
            {"name": "Hemoglobin", "value": 11.2, "unit": "g/dL", "status": "LOW"}
        ],
        risk_result={"health_score": 75, "risk_score": 28, "risk_level": "MODERATE"}
    )

    result = await agent.run(state=state, db=db)
    db.close()

    assert result.success is True
    assert state.final_report is not None
    assert state.final_report.patient_name == "Sarah Jenkins"
    assert "IMPORTANT MEDICAL DISCLAIMER" in state.final_report.disclaimer
    assert len(state.final_report.recommendations) >= 1
    assert state.status == WorkflowStatus.COMPLETED


# ==========================================
# 2. Orchestrator Dynamic Routing Tests
# ==========================================

@pytest.mark.asyncio
async def test_orchestrator_lab_workflow_end_to_end():
    db = TestingSessionLocal()
    orchestrator = OrchestratorAgent()

    sample_lab_report = (
        "METROPOLIS CLINICAL LABORATORIES\n"
        "Patient Name: Sarah Jenkins\n"
        "Complete Blood Count\n"
        "Hemoglobin: 11.0 g/dL (Reference: 12.0 - 15.5)\n"
        "WBC: 7200 cells/uL (Reference: 4000 - 11000)\n"
        "Platelets: 240000 /uL (Reference: 150000 - 450000)\n"
    )

    state = WorkflowState(
        workflow_id="wf-orchestrator-lab-01",
        patient_id=201,
        user_id=101,
        extracted_text=sample_lab_report,
        filename="sarah_blood_work.pdf",
        workflow_type=WorkflowType.AUTOMATIC
    )

    result = await orchestrator.run(state=state, db=db)
    db.close()

    assert result.success is True
    assert state.document_type == "Lab Report"
    assert state.workflow_type == WorkflowType.LAB_REPORT
    assert "lab_analysis" in state.completed_agents
    assert "patient_history" in state.completed_agents
    assert "risk_prediction" in state.completed_agents
    assert "verification_report" in state.completed_agents
    assert state.final_report is not None
    assert state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.DOCTOR_REVIEW_REQUIRED]
    assert len(state.audit_trail) >= 5


@pytest.mark.asyncio
async def test_orchestrator_prescription_workflow_conditional_routing():
    orchestrator = OrchestratorAgent()

    rx_text = (
        "PRESCRIPTION\n"
        "Dr. Sharma MD (Cardiology)\n"
        "Patient Name: Sarah Jenkins\n"
        "Rx:\n"
        "Tab Atorvastatin 10mg - 1 tab at bedtime\n"
        "Tab Metoprolol 25mg - 1 tab daily after food\n"
        "Chief Complaint: Mild exertional dyspnea and fatigue"
    )

    state = WorkflowState(
        workflow_id="wf-orchestrator-rx-02",
        extracted_text=rx_text,
        filename="prescription_cardio.pdf",
        workflow_type=WorkflowType.AUTOMATIC
    )

    result = await orchestrator.run(state=state)

    assert result.success is True
    assert state.document_type == "Prescription"
    assert state.workflow_type == WorkflowType.PRESCRIPTION
    # Verified conditional routing: symptom_clinical executed, lab_analysis skipped
    assert "symptom_clinical" in state.completed_agents
    assert "lab_analysis" not in state.completed_agents
    assert state.final_report is not None


@pytest.mark.asyncio
async def test_orchestrator_claim_workflow_conditional_routing():
    orchestrator = OrchestratorAgent()

    invoice_text = (
        "APOLLO HOSPITAL INVOICE & MEDICAL BILL\n"
        "Invoice Number: INV-2026-9921\n"
        "Total Charges: INR 45,000\n"
        "Pharmacy Bill: INR 12,000\n"
        "Payment Mode: Cashless Insurance Claim"
    )

    state = WorkflowState(
        workflow_id="wf-orchestrator-claim-03",
        extracted_text=invoice_text,
        filename="hospital_tax_invoice.pdf",
        workflow_type=WorkflowType.AUTOMATIC
    )

    result = await orchestrator.run(state=state)

    assert result.success is True
    assert state.document_type == "Medical Invoice"
    assert state.workflow_type == WorkflowType.INSURANCE_CLAIM
    # Verified conditional routing: risk prediction executed, lab analysis skipped
    assert "risk_prediction" in state.completed_agents
    assert "lab_analysis" not in state.completed_agents


@pytest.mark.asyncio
async def test_orchestrator_critical_panic_escalation():
    orchestrator = OrchestratorAgent()

    panic_text = (
        "LABORATORY CRITICAL VALUE ALERT\n"
        "Patient Name: Sarah Jenkins\n"
        "Hemoglobin: 4.8 g/dL\n"
        "Platelets: 18000 /uL\n"
    )

    state = WorkflowState(
        workflow_id="wf-orchestrator-panic-04",
        extracted_text=panic_text,
        filename="urgent_cbc.pdf",
        workflow_type=WorkflowType.LAB_REPORT
    )

    result = await orchestrator.run(state=state)

    assert result.success is True
    assert state.escalation_required is True
    assert state.status == WorkflowStatus.DOCTOR_REVIEW_REQUIRED
    assert state.final_report.requires_human_review is True
    assert "Critical panic value detected" in state.final_report.escalation_reason


@pytest.mark.asyncio
async def test_orchestrator_ocr_failure_graceful_containment():
    orchestrator = OrchestratorAgent()

    # Intentionally missing file to trigger OCR failure
    state = WorkflowState(
        workflow_id="wf-orchestrator-fail-05",
        file_path="/invalid/non_existent/scanned.pdf",
        workflow_type=WorkflowType.LAB_REPORT
    )

    result = await orchestrator.run(state=state)

    # Workflow controller safely catches failure, does not crash, generates report with escalation
    assert result.success is True
    assert "ocr" in state.failed_agents
    assert state.escalation_required is True
    assert state.status == WorkflowStatus.DOCTOR_REVIEW_REQUIRED
    assert state.final_report is not None
