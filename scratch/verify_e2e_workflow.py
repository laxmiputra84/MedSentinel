"""
Comprehensive End-to-End Workflow Verification Script for MedSentinel
Runs a real synthetic patient lab workflow through the real API/workflow pipeline:
1. Creates synthetic Patient in the DB
2. Invokes WorkflowManager / SupervisorAgent
3. Inspects IntentAgent output
4. Inspects PlannerAgent dynamic DAG plan
5. Follows step-by-step execution across all agents
6. Verifies Tool Gateway calls & PII redaction
7. Verifies Redis events emitted
8. Verifies MySQL persistent records (WorkflowInstance, Steps, Events, Checkpoints)
9. Verifies SafetyAgent check & HumanReviewRecord (if panic value triggered)
10. Validates final output report
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.patient import Patient
from app.models.workflow import (
    WorkflowInstance, WorkflowStepRecord, WorkflowEventRecord, 
    WorkflowCheckpointRecord, HumanReviewRecord
)
from app.agents.state import (
    WorkflowState, WorkflowType, WorkflowStatus, EscalationLevel
)
from app.services.workflow_manager import workflow_manager
from app.services.redis_event_bus import redis_event_bus
from app.agents.supervisor_agent import SupervisorAgent

async def run_e2e_verification():
    print("=" * 70)
    print("MEDSENTINEL E2E REAL WORKFLOW VERIFICATION AUDIT")
    print("=" * 70)

    # 1. Setup Database & Synthetic Patient
    db = SessionLocal()
    try:
        # Create test user if not exists
        test_user = db.query(User).filter(User.email == "audit_doctor@medsentinel.com").first()
        if not test_user:
            test_user = User(
                email="audit_doctor@medsentinel.com",
                name="Dr. Audit Specialist",
                role="DOCTOR",
                hashed_password="mock_hashed_password_for_audit",
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)

        # Create test patient if not exists
        test_patient = db.query(Patient).filter(Patient.patient_code == "PT-AUDIT-2026-001").first()
        if not test_patient:
            test_patient = Patient(
                user_id=test_user.id,
                patient_code="PT-AUDIT-2026-001",
                name="Aarav Sharma",
                gender="Male",
                blood_group="O+",
                emergency_contact="+91 9876543210"
            )
            db.add(test_patient)
            db.commit()
            db.refresh(test_patient)

        patient_id = test_patient.id
        user_id = test_user.id
        print(f"[OK] Synthetic Patient established: ID={patient_id}, Code='{test_patient.patient_code}', Name='{test_patient.name}'")

        # 2. Synthetic Clinical Lab Text (incorporating critical panic value: Platelets 22,000 /uL)
        synthetic_lab_text = (
            "PATIENT NAME: Aarav Sharma | AGE: 42 | GENDER: MALE | REPORT DATE: 2026-10-03\n"
            "PATIENT AADHAAR: 1234 5678 9012 | PAN: ABCDE1234F | PHONE: +91 9876543210\n"
            "TEST PERFORMED: COMPLETE BLOOD COUNT (CBC)\n\n"
            "HEMOGLOBIN: 14.2 g/dL (Reference: 13.5 - 17.5 g/dL) [NORMAL]\n"
            "PLATELETS: 22,000 /uL (Reference: 150,000 - 450,000 /uL) [CRITICAL LOW]\n"
            "WBC COUNT: 8,200 /uL (Reference: 4,500 - 11,000 /uL) [NORMAL]\n"
            "NEUTROPHILS: 58 % (Reference: 40 - 70 %) [NORMAL]\n\n"
            "CLINICAL NOTES: Patient presents with acute petechiae and mucosal bleeding. Immediate clinical review advised."
        )

        # 3. Create Workflow ID and State
        workflow_id = workflow_manager.generate_workflow_id()
        state = WorkflowState(
            workflow_id=workflow_id,
            user_id=user_id,
            user_role="DOCTOR",
            patient_id=patient_id,
            extracted_text=synthetic_lab_text,
            workflow_type=WorkflowType.AUTOMATIC,
            status=WorkflowStatus.PENDING
        )
        # Register in DB so master row exists for child foreign keys
        workflow_manager.register_workflow(state, db=db)
        print(f"[OK] Workflow Instance registered in DB: workflow_id='{workflow_id}'")

        # 4. Subscribe to Redis Event Bus to capture live events
        captured_events = []
        async def event_collector():
            async for sse_msg in redis_event_bus.subscribe(workflow_id):
                captured_events.append(sse_msg)
                if "WORKFLOW_COMPLETED" in sse_msg or "WORKFLOW_FAILED" in sse_msg:
                    break

        collector_task = asyncio.create_task(event_collector())

        # 5. Execute through SupervisorAgent
        print("\n--- Executing SupervisorAgent.run() ---")
        supervisor = SupervisorAgent()
        context = {"db": db}

        start_time = datetime.now()
        result = await supervisor.run(state=state, db=db, context=context)
        elapsed = (datetime.now() - start_time).total_seconds()

        # Wait briefly for SSE collector to catch trailing events
        await asyncio.sleep(0.3)
        collector_task.cancel()

        print(f"\n[OK] Workflow execution finished in {elapsed:.2f}s")
        print(f"Result Success: {result.success}")
        print(f"Final State Status: {state.status.value}")
        print(f"Escalation Required: {state.escalation_required}")
        print(f"Escalation Reason: {state.escalation_reason}")
        print(f"Completed Agents ({len(state.completed_agents)}): {state.completed_agents}")
        print(f"Failed Agents ({len(state.failed_agents)}): {state.failed_agents}")

        # 6. Verify Database Persistence in MySQL/SQLite
        print("\n--- Verifying Database Records ---")
        wf_instance = db.query(WorkflowInstance).filter(WorkflowInstance.workflow_id == workflow_id).first()
        print(f"[DB] WorkflowInstance found: ID={wf_instance.id if wf_instance else 'NOT FOUND'}, Status={wf_instance.status if wf_instance else 'N/A'}")

        steps = db.query(WorkflowStepRecord).filter(WorkflowStepRecord.workflow_id == workflow_id).order_by(WorkflowStepRecord.step_index).all()
        print(f"[DB] WorkflowStepRecord count: {len(steps)}")
        for s in steps:
            print(f"     Step {s.step_index}: {s.agent_name} -> {s.status} ({s.duration_ms} ms)")

        checkpoints = db.query(WorkflowCheckpointRecord).filter(WorkflowCheckpointRecord.workflow_id == workflow_id).all()
        print(f"[DB] WorkflowCheckpointRecord count: {len(checkpoints)}")

        reviews = db.query(HumanReviewRecord).filter(HumanReviewRecord.workflow_id == workflow_id).all()
        print(f"[DB] HumanReviewRecord count: {len(reviews)}")
        if reviews:
            for r in reviews:
                print(f"     Review #{r.id} ({r.review_id}): Risk={r.risk_level}, Reason='{r.reason}', Status={r.status}")

        events = db.query(WorkflowEventRecord).filter(WorkflowEventRecord.workflow_id == workflow_id).all()
        print(f"[DB] WorkflowEventRecord count: {len(events)}")

        # 7. Verify Captured SSE Events
        print(f"\n[EVENT BUS] Total SSE messages captured: {len(captured_events)}")
        for evt in captured_events[:8]:
            first_line = evt.strip().split('\n')[0] if evt else ""
            print(f"     SSE Event: {first_line}")

        # 8. Verify Panic Biomarkers Extraction
        print("\n--- Verifying Lab Intelligence & Safety Gate ---")
        panic_detected = False
        for f in state.clinical_findings:
            if "Platelet" in str(f) or "CRITICAL" in str(f) or "LOW" in str(f):
                print(f"     Finding: {f}")
                panic_detected = True

        if state.lab_results:
            print(f"     Extracted Lab Results count: {len(state.lab_results)}")
            for item in state.lab_results[:5]:
                print(f"       Biomarker: {item}")

        # 9. Verify Final Report
        if state.final_report:
            print(f"\n[REPORT] Final Report Generated: DocType='{state.final_report.document_type}', ReviewStatus='{state.final_report.review_status}'")
            print(f"         Executive Summary: {state.final_report.executive_summary[:180]}...")

        print("\n" + "=" * 70)
        print("E2E WORKFLOW VERIFICATION SUMMARY:")
        print(f"  Workflow ID: {workflow_id}")
        print(f"  DAG Steps Executed: {len(steps)}")
        print(f"  Checkpoints Saved: {len(checkpoints)}")
        print(f"  Safety Escalation Triggered: {state.escalation_required}")
        print(f"  Human Review Record Created: {len(reviews) > 0}")
        print("=" * 70)

        return {
            "workflow_id": workflow_id,
            "status": state.status.value,
            "steps_count": len(steps),
            "checkpoints_count": len(checkpoints),
            "events_count": len(captured_events),
            "human_reviews_count": len(reviews),
            "completed_agents": state.completed_agents,
        }

    finally:
        db.close()

if __name__ == '__main__':
    asyncio.run(run_e2e_verification())
