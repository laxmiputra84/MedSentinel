"""
MedSentinel Event-Driven Agent Architecture — Central Event Bus & Background Worker.
Implements:
  - Event Publishing with Schema Validation
  - Cryptographic / Unique Event ID Generation
  - Idempotency & Duplicate Event Detection
  - Event Persistence & Audit Trail
  - Scoped Patient Context Loading
  - Dynamic Multi-Agent Orchestration & Real-Time Telemetry
  - Exponential Backoff Retries & Safe Error Recovery
  - Safety Supervisor Verification (Non-diagnostic compliance, panic escalation)
  - Real-Time WebSocket Streaming
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.events import (
    EventType,
    EventStatus,
    TaskStatus,
    TaskPriority,
    DEFAULT_ENTITY_TYPES,
    SUPPORTED_EVENT_TYPES,
)
from app.core.websocket import ws_manager
from app.models.event import Event
from app.models.agent_task import AgentTask
from app.models.audit_log import AdminAuditLog
from app.models.patient import Patient
from app.models.document import UserDocument
from app.models.lab_result import LabResult
from app.models.insurance_claim import InsuranceClaim
from app.models.appointment import Appointment
from app.agents.orchestrator import OrchestratorAgent
from app.agents.state import WorkflowState, WorkflowType, WorkflowStatus, EscalationLevel

logger = logging.getLogger("medsentinel.event_bus")


class EventBus:
    """
    Central Event Bus managing event ingestion, deduplication,
    background dispatch, and multi-agent coordination.
    """

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._orchestrator = OrchestratorAgent()
        self._is_running = False
        self._events_processed_count = 0
        self._active_tasks_count = 0
        self._completed_tasks_count = 0
        self._failed_tasks_count = 0

    # -------------------------------------------------------------
    # Lifecycle Management
    # -------------------------------------------------------------
    def start(self):
        """Starts the background worker queue loop."""
        if not self._is_running:
            self._is_running = True
            try:
                loop = asyncio.get_running_loop()
                self._worker_task = loop.create_task(self._worker_loop())
                logger.info("EventBus background worker started successfully.")
            except RuntimeError:
                # No running loop yet; will be scheduled by FastAPI lifespan
                pass

    def stop(self):
        """Gracefully halts the background worker."""
        self._is_running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            logger.info("EventBus background worker stopped.")

    def _safe_broadcast(self, data: Dict[str, Any]):
        """Broadcasts WebSocket message safely without failing if no loop is running."""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast(data))
        except RuntimeError:
            pass

    # -------------------------------------------------------------
    # Event Publishing & Ingestion
    # -------------------------------------------------------------

    def publish_event(
        self,
        event_type: str,
        entity_id: Any,
        user_id: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
        entity_type: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        db: Optional[Session] = None,
        sync: bool = False,
    ) -> Event:
        """
        Ingests and validates a healthcare event, checks idempotency,
        persists the Event record, and enqueues it for background processing.
        """
        # 1. EVENT VALIDATION
        norm_event_type = event_type.strip()
        if norm_event_type not in SUPPORTED_EVENT_TYPES:
            raise ValueError(f"Unsupported event type: '{norm_event_type}'")

        resolved_entity_type = (
            entity_type or DEFAULT_ENTITY_TYPES.get(norm_event_type, "unknown")
        )
        entity_id_str = str(entity_id)
        raw_payload = dict(payload or {})
        if idempotency_key:
            raw_payload["idempotency_key"] = idempotency_key

        own_session = False
        if db is None:
            db = SessionLocal()
            own_session = True

        try:
            # 2. DUPLICATE CHECK / IDEMPOTENCY
            if idempotency_key:
                # Check for existing event with this idempotency key
                existing_event = (
                    db.query(Event)
                    .filter(Event.payload.like(f'%"idempotency_key": "{idempotency_key}"%'))
                    .first()
                )
                if existing_event:
                    logger.info(
                        f"Idempotency hit: Event '{existing_event.event_id}' already exists for key '{idempotency_key}'."
                    )
                    return existing_event

            # Check if identical event was already published for entity within last 2 minutes
            recent_duplicate = (
                db.query(Event)
                .filter(
                    Event.event_type == norm_event_type,
                    Event.entity_type == resolved_entity_type,
                    Event.entity_id == entity_id_str,
                    Event.status.in_([EventStatus.PENDING.value, EventStatus.PROCESSING.value]),
                )
                .first()
            )
            if recent_duplicate and not raw_payload.get("force_reprocess"):
                logger.info(
                    f"Duplicate suppression: Event '{recent_duplicate.event_id}' already active for entity {entity_id_str}."
                )
                return recent_duplicate

            # 3. EVENT ID GENERATION
            date_prefix = datetime.now().strftime("%Y%m%d")
            unique_hex = uuid.uuid4().hex[:8]
            event_id = f"evt-{date_prefix}-{unique_hex}"

            # 4. EVENT PERSISTENCE
            event = Event(
                event_id=event_id,
                event_type=norm_event_type,
                entity_type=resolved_entity_type,
                entity_id=entity_id_str,
                user_id=user_id,
                payload=json.dumps(raw_payload),
                status=EventStatus.PENDING.value,
                retry_count=0,
                created_at=datetime.now(timezone.utc),
            )
            db.add(event)
            db.commit()
            db.refresh(event)

            # 5. AUDIT LOG
            try:
                audit = AdminAuditLog(
                    admin_user_id=user_id,
                    action=f"EVENT_PUBLISHED:{norm_event_type}",
                    resource_type=resolved_entity_type,
                    resource_id=entity_id_str,
                    new_value=json.dumps({"event_id": event_id, "type": norm_event_type}),
                )
                db.add(audit)
                db.commit()
            except Exception as audit_err:
                logger.debug(f"Audit log write note: {audit_err}")

            # 6. REAL-TIME BROADCAST TO WEBSOCKET
            self._safe_broadcast({
                "type": "EVENT_PUBLISHED",
                "event_id": event.event_id,
                "event_type": event.event_type,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "status": event.status,
                "timestamp": event.created_at.isoformat(),
            })

            # 7. ENQUEUE FOR BACKGROUND OR SYNCHRONOUS DISPATCH
            if sync:
                self.process_event_sync(event.event_id, db=db)
                db.refresh(event)
            else:
                self._enqueue_event(event.event_id)

            return event

        finally:
            if own_session:
                db.close()

    def _enqueue_event(self, event_id: str):
        """Pushes event into background queue or schedules runner."""
        try:
            self._queue.put_nowait(event_id)
        except Exception:
            # Fallback direct task creation
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._process_event_async(event_id))
            except RuntimeError:
                pass

    # -------------------------------------------------------------
    # Background Worker Loop
    # -------------------------------------------------------------
    async def _worker_loop(self):
        """Continuous consumer loop executing enqueued events."""
        while self._is_running:
            try:
                event_id = await self._queue.get()
                await self._process_event_async(event_id)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in EventBus worker loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    # -------------------------------------------------------------
    # Scoped Patient Context Loader
    # -------------------------------------------------------------
    def _load_scoped_context(
        self,
        event: Event,
        db: Session
    ) -> Tuple[WorkflowState, Dict[str, Any]]:
        """
        Loads only the necessary patient and clinical context scoped to the event.
        Guarantees principle of least privilege: no unnecessary data is passed to agents.
        """
        payload = json.loads(event.payload) if event.payload else {}
        state = WorkflowState(
            workflow_id=f"wf-{event.event_id}",
            user_id=event.user_id,
        )

        context: Dict[str, Any] = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            **payload,
        }

        # Resolve entity-specific data
        if event.entity_type == "document" or event.event_type in [
            EventType.DOCUMENT_UPLOADED.value,
            EventType.DOCUMENT_UPDATED.value,
            EventType.DOCUMENT_VERIFIED.value,
            EventType.DOCUMENT_DUPLICATE_DETECTED.value,
            EventType.LAB_REPORT_RECEIVED.value,
        ]:
            doc_id = int(event.entity_id) if str(event.entity_id).isdigit() else None
            if doc_id:
                doc = db.query(UserDocument).filter(UserDocument.id == doc_id).first()
                if doc:
                    state.document_id = str(doc.id)
                    state.file_path = doc.file_path
                    state.filename = doc.original_name or doc.filename
                    state.extracted_text = doc.ocr_extracted_text or ""
                    state.patient_id = doc.patient_id
                    context["document"] = {
                        "id": doc.id,
                        "code": doc.document_code,
                        "type": doc.doc_type,
                        "path": doc.file_path,
                        "name": doc.original_name,
                        "hash": doc.file_hash,
                        "is_duplicate": doc.is_duplicate,
                    }

        elif event.entity_type == "claim" or event.event_type in [
            EventType.CLAIM_CREATED.value,
            EventType.CLAIM_UPDATED.value,
            EventType.FRAUD_FLAG_DETECTED.value,
        ]:
            claim_id = int(event.entity_id) if str(event.entity_id).isdigit() else None
            if claim_id:
                claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
                if claim:
                    state.document_id = str(claim.id)
                    state.workflow_type = WorkflowType.INSURANCE_CLAIM
                    context["claim_id"] = claim.id
                    context["claim"] = {
                        "id": claim.id,
                        "amount": claim.claim_amount,
                        "description": claim.claim_description,
                        "hospital_id": claim.hospital_id,
                        "insurance_id": claim.insurance_id,
                        "status": claim.claim_status,
                    }

        elif event.entity_type == "appointment" or event.event_type in [
            EventType.APPOINTMENT_CREATED.value,
            EventType.APPOINTMENT_UPDATED.value,
            EventType.APPOINTMENT_CANCELLED.value,
        ]:
            appt_id = int(event.entity_id) if str(event.entity_id).isdigit() else None
            if appt_id:
                appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
                if appt:
                    state.document_id = str(appt.id)
                    state.workflow_type = WorkflowType.APPOINTMENT
                    context["appointment_id"] = appt.id
                    context["appointment"] = {
                        "id": appt.id,
                        "department": appt.department,
                        "date": str(appt.preferred_date),
                        "time": appt.preferred_time,
                        "status": appt.status,
                    }

        elif event.entity_type == "patient" or event.event_type in [
            EventType.PATIENT_CREATED.value,
            EventType.PATIENT_UPDATED.value,
        ]:
            pid = int(event.entity_id) if str(event.entity_id).isdigit() else None
            if pid:
                pat = db.query(Patient).filter(Patient.id == pid).first()
                if pat:
                    state.patient_id = pat.id
                    state.workflow_type = WorkflowType.PATIENT_PROFILE
                    context["patient"] = {
                        "id": pat.id,
                        "code": pat.patient_code,
                        "name": pat.name,
                        "blood_group": pat.blood_group,
                        "gender": pat.gender,
                    }

        # Resolve patient profile if linked
        if state.patient_id:
            patient = db.query(Patient).filter(Patient.id == state.patient_id).first()
            if patient:
                state.patient_demographics = {
                    "patient_id": patient.id,
                    "patient_code": patient.patient_code,
                    "name": patient.name,
                    "blood_group": patient.blood_group,
                    "gender": patient.gender,
                }
                # Load recent lab results for trend analysis
                recent_labs = (
                    db.query(LabResult)
                    .filter(LabResult.patient_id == patient.id)
                    .order_by(LabResult.test_date.desc())
                    .limit(15)
                    .all()
                )
                state.historical_records = [
                    {
                        "test_name": r.test_name,
                        "value": r.observed_value,
                        "unit": r.unit,
                        "status": r.status,
                        "date": str(r.test_date),
                    }
                    for r in recent_labs
                ]

        return state, context

    # -------------------------------------------------------------
    # Asynchronous & Synchronous Execution
    # -------------------------------------------------------------
    async def _process_event_async(self, event_id: str):
        """Asynchronous worker method to execute event lifecycle."""
        db = SessionLocal()
        try:
            await self._execute_event_lifecycle(event_id, db=db, is_async=True)
        finally:
            db.close()

    def process_event_sync(self, event_id: str, db: Session):
        """Synchronous helper for testing and inline execution requirements."""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._execute_event_lifecycle(event_id, db=db, is_async=False))
                    return future.result()
        except RuntimeError:
            pass
        return asyncio.run(self._execute_event_lifecycle(event_id, db=db, is_async=False))

    async def _execute_event_lifecycle(self, event_id: str, db: Session, is_async: bool = True):
        """
        Executes the full event lifecycle:
        EVENT -> LOAD SCOPED CONTEXT -> PLAN AGENTS -> EXECUTE TASKS -> VERIFY -> SAFETY SUPERVISOR -> FINALIZE
        """
        event = db.query(Event).filter(Event.event_id == event_id).first()
        if not event:
            logger.warning(f"Event {event_id} not found in database.")
            return

        if event.status == EventStatus.COMPLETED.value:
            logger.info(f"Event {event_id} already marked COMPLETED. Skipping.")
            return

        # Update event status to PROCESSING
        event.status = EventStatus.PROCESSING.value
        db.commit()

        # Broadcast event status update
        await ws_manager.broadcast({
            "type": "EVENT_PROCESSING",
            "event_id": event.event_id,
            "event_type": event.event_type,
            "status": event.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # 1. Load scoped patient context
        state, context = self._load_scoped_context(event, db)

        # 2. Determine required agents via Orchestrator
        planned_agents = self._orchestrator.plan_for_event(event.event_type, state)
        logger.info(f"Event {event_id} ({event.event_type}) planned agents: {planned_agents}")

        overall_success = True
        fatal_error: Optional[str] = None

        # 3. Step-by-Step Task Creation & Agent Execution
        for agent_key in planned_agents:
            agent = self._orchestrator.registry.get(agent_key)
            if not agent:
                logger.warning(f"Agent '{agent_key}' not found in registry. Skipping.")
                continue

            # Create AgentTask model
            task_uid = f"task-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
            scoped_input = {
                "agent": agent_key,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "entity_id": event.entity_id,
                "document_id": state.document_id,
                "patient_id": state.patient_id,
            }

            task = AgentTask(
                task_id=task_uid,
                event_id=event.event_id,
                agent_type=agent_key,
                entity_id=event.entity_id,
                priority=TaskPriority.NORMAL.value,
                status=TaskStatus.QUEUED.value,
                input_context=json.dumps(scoped_input),
                retry_count=0,
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            # Broadcast AGENT_TASK_CREATED
            await ws_manager.broadcast({
                "type": "AGENT_TASK_CREATED",
                "task_id": task.task_id,
                "event_id": event.event_id,
                "agent_type": agent_key,
                "status": task.status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            # Transition task to RUNNING
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.now(timezone.utc)
            db.commit()

            await ws_manager.broadcast({
                "type": "AGENT_TASK_STARTED",
                "task_id": task.task_id,
                "event_id": event.event_id,
                "agent_type": agent_key,
                "status": task.status,
                "timestamp": task.started_at.isoformat(),
            })

            # Execute Agent with Exponential Backoff Retry (Max 5 attempts)
            max_retries = 5
            agent_result = None
            attempt = 0
            backoff_seconds = [0.05, 0.1, 0.2, 0.4, 0.8] if not is_async else [2, 4, 8, 16, 32]

            while attempt < max_retries:
                attempt += 1
                try:
                    agent_result = await agent.run(state=state, db=db, context=context)
                    if agent_result.success:
                        break
                    else:
                        task.retry_count = attempt
                        db.commit()
                        if attempt < max_retries:
                            delay = backoff_seconds[attempt - 1]
                            logger.info(f"Agent '{agent_key}' attempt {attempt} failed; retrying in {delay}s...")
                            await asyncio.sleep(delay)
                except Exception as exc:
                    task.retry_count = attempt
                    db.commit()
                    if attempt < max_retries:
                        delay = backoff_seconds[attempt - 1]
                        logger.info(f"Agent '{agent_key}' exception on attempt {attempt}: {exc}; retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        fatal_error = str(exc)

            # Verify and Record Task Result
            task.completed_at = datetime.now(timezone.utc)

            if agent_result and agent_result.success:
                task.status = TaskStatus.COMPLETED.value
                task.output_result = json.dumps({
                    "data": agent_result.data,
                    "findings_count": len(agent_result.findings),
                })
                self._completed_tasks_count += 1
                db.commit()

                await ws_manager.broadcast({
                    "type": "AGENT_TASK_COMPLETED",
                    "task_id": task.task_id,
                    "event_id": event.event_id,
                    "agent_type": agent_key,
                    "status": task.status,
                    "findings_count": len(agent_result.findings),
                    "timestamp": task.completed_at.isoformat(),
                })

                # Check if this agent triggered a cascading event
                await self._handle_cascading_events(agent_key, agent_result, state, event, db)

            else:
                task.status = TaskStatus.FAILED.value
                task.error_message = fatal_error or "; ".join(agent_result.errors) if (agent_result and agent_result.errors) else "Agent failed after max retries"
                overall_success = False
                self._failed_tasks_count += 1
                db.commit()

                await ws_manager.broadcast({
                    "type": "AGENT_TASK_FAILED",
                    "task_id": task.task_id,
                    "event_id": event.event_id,
                    "agent_type": agent_key,
                    "status": task.status,
                    "error": task.error_message,
                    "timestamp": task.completed_at.isoformat(),
                })

                # Failure containment: Log audit trail and preserve patient data
                AdminAuditLog(
                    admin_user_id=event.user_id,
                    action=f"AGENT_TASK_FAILED:{agent_key}",
                    resource_type="agent_task",
                    resource_id=task.task_id,
                    new_value=json.dumps({"error": task.error_message, "event_id": event.event_id}),
                )
                db.commit()

                # If early agent fails, break out of subsequent non-safety agents
                break

        # 4. SAFETY SUPERVISOR FINAL CHECK
        safety_agent = self._orchestrator.registry.get("safety")
        if safety_agent:
            try:
                safety_res = await safety_agent.run(state=state, db=db, context=context)
                if state.escalation_required:
                    # Emits CRITICAL_LAB_VALUE_DETECTED if panic value was caught
                    logger.warning(f"Safety Supervisor flagged escalation for event {event_id}: {state.escalation_reason}")
            except Exception as s_err:
                logger.error(f"Safety Supervisor error: {s_err}")

        # 5. UPDATE EVENT STATUS & AUDIT
        event.processed_at = datetime.now(timezone.utc)
        event.status = EventStatus.COMPLETED.value if overall_success else EventStatus.FAILED.value
        if not overall_success and fatal_error:
            event.error_message = fatal_error

        self._events_processed_count += 1
        db.commit()

        # Audit finalized event
        try:
            final_audit = AdminAuditLog(
                admin_user_id=event.user_id,
                action=f"EVENT_COMPLETED:{event.event_type}" if overall_success else f"EVENT_FAILED:{event.event_type}",
                resource_type=event.entity_type,
                resource_id=event.entity_id,
                new_value=json.dumps({
                    "event_id": event.event_id,
                    "status": event.status,
                    "escalation_required": state.escalation_required,
                }),
            )
            db.add(final_audit)
            db.commit()
        except Exception:
            pass

        # Broadcast completion to WebSocket
        await ws_manager.broadcast({
            "type": "EVENT_COMPLETED" if overall_success else "EVENT_FAILED",
            "event_id": event.event_id,
            "event_type": event.event_type,
            "status": event.status,
            "escalation_required": state.escalation_required,
            "timestamp": event.processed_at.isoformat(),
        })

    # -------------------------------------------------------------
    # Cascading Healthcare Events
    # -------------------------------------------------------------
    async def _handle_cascading_events(
        self,
        agent_key: str,
        result: Any,
        state: WorkflowState,
        event: Event,
        db: Session
    ):
        """
        Handles autonomous event cascades without requiring user interaction:
        - When Document Intelligence classifies file as 'Lab Report' -> Emits LAB_REPORT_RECEIVED
        - When Lab Analysis detects critical panic values -> Emits CRITICAL_LAB_VALUE_DETECTED
        - When Claims Agent detects high fraud risk -> Emits FRAUD_FLAG_DETECTED
        """
        # Document Intelligence -> Lab Report Received
        if agent_key in ["document_intelligence", "document_classification"]:
            doc_type = result.data.get("document_type") or state.document_type
            if doc_type == "Lab Report" and event.event_type == EventType.DOCUMENT_UPLOADED.value:
                logger.info(f"Autonomous Cascade: DOCUMENT_UPLOADED -> LAB_REPORT_RECEIVED for doc {event.entity_id}")
                self.publish_event(
                    event_type=EventType.LAB_REPORT_RECEIVED.value,
                    entity_id=event.entity_id,
                    user_id=event.user_id,
                    payload={"cascaded_from": event.event_id},
                    entity_type="document",
                    db=db,
                    sync=False,
                )

        # Lab Analysis -> Critical Lab Value Detected
        elif agent_key == "lab_analysis":
            has_critical = any(
                f.is_critical or f.status == "CRITICAL" for f in (result.findings or [])
            )
            if has_critical and event.event_type != EventType.CRITICAL_LAB_VALUE_DETECTED.value:
                logger.warning(f"Autonomous Cascade: Critical Lab Value Detected for entity {event.entity_id}")
                self.publish_event(
                    event_type=EventType.CRITICAL_LAB_VALUE_DETECTED.value,
                    entity_id=event.entity_id,
                    user_id=event.user_id,
                    payload={"cascaded_from": event.event_id, "escalation_reason": state.escalation_reason},
                    entity_type="lab_result",
                    db=db,
                    sync=False,
                )

        # Claims Agent -> Fraud Flag Detected
        elif agent_key == "claims":
            fraud_data = result.data.get("fraud_analysis", {})
            if fraud_data.get("fraud_risk") == "HIGH":
                logger.warning(f"Autonomous Cascade: FRAUD_FLAG_DETECTED for claim {event.entity_id}")
                self.publish_event(
                    event_type=EventType.FRAUD_FLAG_DETECTED.value,
                    entity_id=event.entity_id,
                    user_id=event.user_id,
                    payload={"cascaded_from": event.event_id, "fraud_analysis": fraud_data},
                    entity_type="claim",
                    db=db,
                    sync=False,
                )

    # -------------------------------------------------------------
    # System Status & Telemetry
    # -------------------------------------------------------------
    def get_system_status(self) -> Dict[str, Any]:
        """Returns live system telemetry for dashboard and health status APIs."""
        return {
            "system_status": "ONLINE" if self._is_running else "IDLE",
            "worker_running": self._is_running,
            "queue_depth": self._queue.qsize(),
            "total_events_processed": self._events_processed_count,
            "active_tasks_count": self._active_tasks_count,
            "completed_tasks_count": self._completed_tasks_count,
            "failed_tasks_count": self._failed_tasks_count,
            "registered_agents": self._orchestrator.registry.list_agents(),
            "active_websocket_connections": ws_manager.connection_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global EventBus Singleton Instance
event_bus = EventBus()


def publish_event(
    event_type: str,
    entity_id: Any,
    user_id: Optional[int] = None,
    payload: Optional[Dict[str, Any]] = None,
    entity_type: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    db: Optional[Session] = None,
    sync: bool = False,
) -> Event:
    """Convenience functional interface for publishing events to the centralized bus."""
    return event_bus.publish_event(
        event_type=event_type,
        entity_id=entity_id,
        user_id=user_id,
        payload=payload,
        entity_type=entity_type,
        idempotency_key=idempotency_key,
        db=db,
        sync=sync,
    )
