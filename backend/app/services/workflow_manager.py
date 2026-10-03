"""
MedSentinel Agentic Architecture — Workflow Manager
Asynchronous lifecycle manager for Agentic Workflows.
Coordinates durable MySQL persistence, background supervisor execution,
Redis-backed SSE streaming, and Human-in-the-Loop review actions.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.supervisor_agent import SupervisorAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.state import (
    WorkflowState,
    WorkflowStatus,
    WorkflowType,
    EscalationLevel,
)
from app.models.user import User
from app.models.workflow import WorkflowInstance, HumanReviewRecord
from app.services.redis_event_bus import redis_event_bus, AgentEventType


class WorkflowManager:
    """
    Manager for tracking active and historical workflows with MySQL persistence,
    Redis pub/sub event streaming with replay buffers, and asynchronous background execution.
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowState] = {}
        self._supervisor = SupervisorAgent()
        self._orchestrator = OrchestratorAgent()
        self._lock = asyncio.Lock()

    def generate_workflow_id(self) -> str:
        """Generates unique formatted workflow ID like wf-2026-a1b2c3d4."""
        unique_suffix = uuid.uuid4().hex[:8]
        return f"wf-{datetime.now().strftime('%Y%m%d')}-{unique_suffix}"

    def register_workflow(self, state: WorkflowState, db: Optional[Session] = None) -> WorkflowState:
        """Registers a workflow in memory and persists to MySQL."""
        self._workflows[state.workflow_id] = state

        if db:
            try:
                # Upsert WorkflowInstance in MySQL
                instance = db.query(WorkflowInstance).filter(WorkflowInstance.workflow_id == state.workflow_id).first()
                if not instance:
                    instance = WorkflowInstance(
                        workflow_id=state.workflow_id,
                        workflow_type=state.workflow_type.value if hasattr(state.workflow_type, "value") else str(state.workflow_type),
                        user_id=state.user_id,
                        patient_id=state.patient_id,
                        document_id=state.document_id,
                        status=state.status.value if hasattr(state.status, "value") else str(state.status),
                        current_step=state.current_agent,
                        escalation_required=state.escalation_required,
                        escalation_reason=state.escalation_reason,
                        state_json=state.model_dump_json() if hasattr(state, "model_dump_json") else json.dumps(state.dict()),
                    )
                    db.add(instance)
                else:
                    instance.status = state.status.value if hasattr(state.status, "value") else str(state.status)
                    instance.state_json = state.model_dump_json() if hasattr(state, "model_dump_json") else json.dumps(state.dict())
                db.commit()
            except Exception:
                db.rollback()

        return state

    def get_workflow(self, workflow_id: str, db: Optional[Session] = None) -> Optional[WorkflowState]:
        """Retrieves a workflow by ID from memory, or restores from MySQL if server restarted."""
        if workflow_id in self._workflows:
            return self._workflows[workflow_id]

        if db:
            try:
                instance = db.query(WorkflowInstance).filter(WorkflowInstance.workflow_id == workflow_id).first()
                if instance and instance.state_json:
                    state_dict = json.loads(instance.state_json)
                    state = WorkflowState(**state_dict)
                    self._workflows[workflow_id] = state
                    return state
            except Exception:
                pass

        return None

    def list_workflows_for_patient(self, patient_id: int, db: Optional[Session] = None) -> List[WorkflowState]:
        """Retrieves all workflows associated with a given patient ID (memory + DB)."""
        active = [w for w in self._workflows.values() if w.patient_id == patient_id]
        if db:
            try:
                instances = db.query(WorkflowInstance).filter(WorkflowInstance.patient_id == patient_id).all()
                active_ids = {w.workflow_id for w in active}
                for inst in instances:
                    if inst.workflow_id not in active_ids and inst.state_json:
                        try:
                            s = WorkflowState(**json.loads(inst.state_json))
                            active.append(s)
                        except Exception:
                            pass
            except Exception:
                pass
        return active

    def list_workflows_for_user(self, user_id: int, db: Optional[Session] = None) -> List[WorkflowState]:
        """Retrieves all workflows associated with a given user ID (memory + DB)."""
        active = [w for w in self._workflows.values() if w.user_id == user_id]
        if db:
            try:
                instances = db.query(WorkflowInstance).filter(WorkflowInstance.user_id == user_id).all()
                active_ids = {w.workflow_id for w in active}
                for inst in instances:
                    if inst.workflow_id not in active_ids and inst.state_json:
                        try:
                            s = WorkflowState(**json.loads(inst.state_json))
                            active.append(s)
                        except Exception:
                            pass
            except Exception:
                pass
        return active

    async def emit_event(self, workflow_id: str, event_type: str, data: Dict[str, Any], db: Optional[Session] = None) -> None:
        """Publishes an event via the Redis/asyncio Event Bus."""
        await redis_event_bus.publish(workflow_id, event_type, data, db=db)

    async def subscribe(self, workflow_id: str) -> AsyncGenerator[str, None]:
        """Subscribes to live SSE events for a specific workflow."""
        async for msg in redis_event_bus.subscribe(workflow_id):
            yield msg

    def start_background_workflow(
        self,
        state: WorkflowState,
        context: Optional[Dict[str, Any]] = None,
        db_session_factory=None
    ) -> str:
        """
        Spawns non-blocking asynchronous execution of the workflow in the background.
        Uses SupervisorAgent with durable state persistence.
        """
        db_init = db_session_factory() if db_session_factory else None
        self.register_workflow(state, db=db_init)
        if db_init:
            db_init.close()

        ctx = dict(context or {})

        async def _run_task():
            db_session = db_session_factory() if db_session_factory else None
            try:
                # Wire event callback
                async def _on_event(event_type: str, data: Dict[str, Any]):
                    await self.emit_event(state.workflow_id, event_type, data, db=db_session)

                ctx["on_event"] = _on_event

                # Execute through SupervisorAgent
                await self._supervisor.run(state=state, db=db_session, context=ctx)

                # Persist completed state to MySQL
                if db_session:
                    try:
                        instance = db_session.query(WorkflowInstance).filter(WorkflowInstance.workflow_id == state.workflow_id).first()
                        if instance:
                            instance.status = state.status.value
                            instance.state_json = state.model_dump_json() if hasattr(state, "model_dump_json") else json.dumps(state.dict())
                            instance.escalation_required = state.escalation_required
                            instance.escalation_reason = state.escalation_reason
                            instance.completed_at = datetime.now(timezone.utc)
                            db_session.commit()
                    except Exception:
                        db_session.rollback()

            except Exception as exc:
                err_str = f"Fatal workflow execution failure: {str(exc)}"
                state.status = WorkflowStatus.FAILED
                state.escalation_required = True
                state.escalation_reason = err_str
                await self.emit_event(state.workflow_id, AgentEventType.WORKFLOW_FAILED.value, {
                    "workflow_id": state.workflow_id,
                    "error": err_str,
                }, db=db_session)
            finally:
                if db_session:
                    db_session.close()

        asyncio.create_task(_run_task())
        return state.workflow_id

    async def review_workflow(
        self,
        workflow_id: str,
        decision: str,
        reviewer_user: User,
        notes: Optional[str] = None,
        db: Optional[Session] = None
    ) -> WorkflowState:
        """Processes human-in-the-loop doctor/reviewer decision."""
        state = self.get_workflow(workflow_id, db=db)
        if not state:
            raise ValueError(f"Workflow '{workflow_id}' does not exist.")

        norm_decision = decision.upper().strip()
        if norm_decision not in ["APPROVE", "REJECT", "REQUEST_MORE_INFORMATION"]:
            raise ValueError("Decision must be one of: APPROVE, REJECT, REQUEST_MORE_INFORMATION")

        if state.final_report:
            state.final_report.reviewer_id = reviewer_user.id
            state.final_report.doctor_review_notes = notes
            state.final_report.review_status = norm_decision

        if norm_decision == "APPROVE":
            state.status = WorkflowStatus.COMPLETED
            state.escalation_required = False
        elif norm_decision == "REJECT":
            state.status = WorkflowStatus.FAILED
        elif norm_decision == "REQUEST_MORE_INFORMATION":
            state.status = WorkflowStatus.DOCTOR_REVIEW_REQUIRED

        # Record in audit trail
        state.add_audit_entry(
            agent_name="human_reviewer",
            action=f"Doctor/Reviewer {reviewer_user.name} ({reviewer_user.role}) decided: {norm_decision}",
            status="SUCCESS",
            details={"reviewer_id": reviewer_user.id, "decision": norm_decision, "notes": notes}
        )

        # Update MySQL records if db session provided
        if db:
            try:
                # Update WorkflowInstance
                instance = db.query(WorkflowInstance).filter(WorkflowInstance.workflow_id == workflow_id).first()
                if instance:
                    instance.status = state.status.value
                    instance.state_json = state.model_dump_json() if hasattr(state, "model_dump_json") else json.dumps(state.dict())
                    db.commit()

                # Update HumanReviewRecord
                review = db.query(HumanReviewRecord).filter(HumanReviewRecord.workflow_id == workflow_id).first()
                if review:
                    review.status = "APPROVED" if norm_decision == "APPROVE" else ("REJECTED" if norm_decision == "REJECT" else "MODIFIED")
                    review.decision = norm_decision
                    review.reviewer_id = reviewer_user.id
                    review.reviewer_notes = notes
                    review.decided_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception:
                db.rollback()

        # Broadcast review event
        await self.emit_event(workflow_id, "decision", {
            "workflow_id": workflow_id,
            "action": "HUMAN_REVIEW_COMPLETED",
            "decision": norm_decision,
            "reviewer_name": reviewer_user.name,
            "new_status": state.status.value,
            "notes": notes
        }, db=db)

        return state


# Global Singleton instance
workflow_manager = WorkflowManager()
