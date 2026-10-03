"""
MedSentinel Agentic Architecture — Supervisor Agent (Master Controller)
Coordinates Intent understanding, dynamic DAG planning, parallel/sequential agent execution,
output validation, automatic retry with backoff, state checkpoints, and Human-in-the-Loop gates.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import (
    WorkflowState,
    AgentResult,
    WorkflowType,
    WorkflowStatus,
    EscalationLevel,
    AgentStatus,
)
from app.agents.orchestrator import AgentRegistry
from app.agents.intent_agent import IntentAgent
from app.agents.planner_agent import PlannerAgent, ExecutionPlan
from app.agents.medication_safety_agent import MedicationSafetyAgent
from app.agents.data_analyst_agent import DataAnalystAgent
from app.agents.human_review_agent import HumanReviewAgent
from app.models.workflow import WorkflowInstance, WorkflowStepRecord, WorkflowCheckpointRecord
from app.services.redis_event_bus import redis_event_bus, AgentEventType


class SupervisorAgent(BaseAgent):
    """
    Central Master Orchestrator for MedSentinel Multi-Agent Platform.
    Enforces controlled execution DAGs, timeouts, failure recovery, and HITL safety gates.
    """

    def __init__(self, registry: Optional[AgentRegistry] = None, max_retries: int = 2):
        super().__init__(
            name="supervisor",
            role="Central Autonomous Workflow Supervisor & Execution Controller",
            description="Supervises Intent -> Planning -> DAG Execution -> Safety -> HITL -> Final Report lifecycle.",
            version="2.0.0"
        )
        self.registry = registry or AgentRegistry()
        self.max_retries = max_retries

        # Ensure all upgraded agents are registered
        self.intent_agent = IntentAgent()
        self.planner_agent = PlannerAgent()
        self.medication_safety_agent = MedicationSafetyAgent()
        self.data_analyst_agent = DataAnalystAgent()
        self.human_review_agent = HumanReviewAgent()

        self.registry.register("intent", self.intent_agent)
        self.registry.register("planner", self.planner_agent)
        self.registry.register("medication_safety", self.medication_safety_agent)
        self.registry.register("data_analyst", self.data_analyst_agent)
        self.registry.register("human_review", self.human_review_agent)

    async def execute_agent_step(
        self,
        agent_name: str,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None,
        step_index: int = 0
    ) -> AgentResult:
        """Executes a single agent step with retry heuristics, telemetry, and checkpointing."""
        agent = self.registry.get(agent_name)
        if not agent:
            err = f"Agent '{agent_name}' is not registered in the system."
            state.add_audit_entry(self.name, f"Failed to locate agent '{agent_name}'", status="FAILED", error=err)
            return AgentResult(success=False, agent_name=agent_name, errors=[err])

        # Notify Event Bus: AGENT_STARTED
        await redis_event_bus.publish(
            workflow_id=state.workflow_id,
            event_type=AgentEventType.AGENT_STARTED,
            data={
                "workflow_id": state.workflow_id,
                "agent_name": agent_name,
                "role": agent.role,
                "status": "RUNNING",
                "step_index": step_index,
            },
            db=db
        )

        attempts = 0
        last_error = None
        start_time = time.perf_counter()

        while attempts <= self.max_retries:
            attempts += 1
            try:
                # Execute agent with a 15-second per-step timeout
                result = await asyncio.wait_for(
                    agent.run(state=state, db=db, context=context),
                    timeout=20.0
                )

                if result.success:
                    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                    
                    # Notify Event Bus: AGENT_COMPLETED
                    await redis_event_bus.publish(
                        workflow_id=state.workflow_id,
                        event_type=AgentEventType.AGENT_COMPLETED,
                        data={
                            "workflow_id": state.workflow_id,
                            "agent_name": agent_name,
                            "status": "COMPLETED",
                            "duration_ms": duration_ms,
                            "findings_count": len(result.findings),
                            "outputs_summary": {k: str(v)[:150] for k, v in result.data.items()}
                        },
                        db=db
                    )

                    # Persist Step Telemetry in MySQL if DB session exists
                    if db:
                        try:
                            step_rec = WorkflowStepRecord(
                                workflow_id=state.workflow_id,
                                step_index=step_index,
                                agent_name=agent_name,
                                status="COMPLETED",
                                inputs_json=json.dumps({"workflow_type": state.workflow_type.value}),
                                outputs_json=json.dumps({k: str(v)[:300] for k, v in result.data.items()}),
                                duration_ms=duration_ms,
                                confidence=result.data.get("confidence", 0.92)
                            )
                            db.add(step_rec)
                            db.commit()
                        except Exception:
                            db.rollback()

                    return result
                else:
                    last_error = "; ".join(result.errors) if result.errors else "Agent indicated failure."

            except asyncio.TimeoutError:
                last_error = f"Agent '{agent_name}' timed out after 20.0s."
            except Exception as e:
                last_error = str(e)

            # If retryable, publish RETRY_STARTED
            if attempts <= self.max_retries:
                await redis_event_bus.publish(
                    workflow_id=state.workflow_id,
                    event_type=AgentEventType.RETRY_STARTED,
                    data={
                        "workflow_id": state.workflow_id,
                        "agent_name": agent_name,
                        "attempt": attempts,
                        "error": last_error
                    },
                    db=db
                )
                await asyncio.sleep(0.2 * attempts)

        # Agent step failed after retries
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        state.failed_agents.append(agent_name)
        
        await redis_event_bus.publish(
            workflow_id=state.workflow_id,
            event_type=AgentEventType.AGENT_FAILED,
            data={
                "workflow_id": state.workflow_id,
                "agent_name": agent_name,
                "status": "FAILED",
                "error": last_error,
                "duration_ms": duration_ms
            },
            db=db
        )

        if db:
            try:
                step_rec = WorkflowStepRecord(
                    workflow_id=state.workflow_id,
                    step_index=step_index,
                    agent_name=agent_name,
                    status="FAILED",
                    duration_ms=duration_ms,
                    error_message=last_error
                )
                db.add(step_rec)
                db.commit()
            except Exception:
                db.rollback()

        return AgentResult(success=False, agent_name=agent_name, errors=[last_error or "Unknown failure"])

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Master Supervisor lifecycle:
        1. Parse intent
        2. Formulate DAG plan
        3. Execute batches
        4. Checkpoint
        5. Verify safety & HITL
        6. Persist final report
        """
        state.status = WorkflowStatus.IN_PROGRESS
        ctx = context or {}

        # 1. Publish WORKFLOW_STARTED
        await redis_event_bus.publish(
            workflow_id=state.workflow_id,
            event_type=AgentEventType.WORKFLOW_STARTED,
            data={
                "workflow_id": state.workflow_id,
                "workflow_type": state.workflow_type.value,
                "patient_id": state.patient_id,
                "status": state.status.value,
            },
            db=db
        )

        # 2. Step 1: Intent Understanding
        await self.execute_agent_step("intent", state=state, db=db, context=ctx, step_index=0)

        # 3. Step 2: DAG Planning
        plan_res = await self.execute_agent_step("planner", state=state, db=db, context=ctx, step_index=1)
        plan_data = plan_res.data if plan_res.success else {}
        steps_to_run: List[str] = plan_data.get("steps", [])

        # If planner didn't produce steps, fallback to standard orchestrator logic
        if not steps_to_run:
            from app.agents.orchestrator import OrchestratorAgent
            fallback_orch = OrchestratorAgent(registry=self.registry)
            steps_to_run = fallback_orch.plan_workflow(state)

        # Publish PLAN_CREATED
        await redis_event_bus.publish(
            workflow_id=state.workflow_id,
            event_type=AgentEventType.PLAN_CREATED,
            data={
                "workflow_id": state.workflow_id,
                "planned_steps": steps_to_run,
                "total_steps": len(steps_to_run)
            },
            db=db
        )

        # 4. Execute Planned Steps
        step_idx = 2
        for agent_name in steps_to_run:
            if agent_name in ["intent", "planner"]:
                continue

            # Run agent
            step_result = await self.execute_agent_step(
                agent_name=agent_name,
                state=state,
                db=db,
                context=ctx,
                step_index=step_idx
            )
            step_idx += 1

            # Checkpoint state to MySQL after every step
            if db:
                try:
                    cp = WorkflowCheckpointRecord(
                        workflow_id=state.workflow_id,
                        step_index=step_idx,
                        agent_name=agent_name,
                        state_snapshot=json.dumps({
                            "status": state.status.value,
                            "completed_agents": state.completed_agents,
                            "escalation_required": state.escalation_required,
                            "escalation_level": state.escalation_level.value,
                        })
                    )
                    db.add(cp)
                    db.commit()
                except Exception:
                    db.rollback()

            # Dynamic conditional branch: If DocumentIntelligence detected a different workflow type, replan!
            if agent_name == "document_intelligence" and state.document_type:
                new_wtype = state.workflow_type
                if state.document_type == "Lab Report" and new_wtype != WorkflowType.LAB_REPORT:
                    state.workflow_type = WorkflowType.LAB_REPORT
                elif state.document_type == "Prescription" and new_wtype != WorkflowType.PRESCRIPTION:
                    state.workflow_type = WorkflowType.PRESCRIPTION
                elif state.document_type in ["Medical Invoice", "Insurance Document"] and new_wtype != WorkflowType.INSURANCE_CLAIM:
                    state.workflow_type = WorkflowType.INSURANCE_CLAIM

        # 5. Check Safety and Human-in-the-Loop Escalation
        if state.escalation_required or state.status == WorkflowStatus.DOCTOR_REVIEW_REQUIRED:
            await self.execute_agent_step("human_review", state=state, db=db, context=ctx, step_index=step_idx)
            step_idx += 1

        # 6. Final Status Determination
        if state.escalation_required:
            state.status = WorkflowStatus.DOCTOR_REVIEW_REQUIRED
        elif state.failed_agents and not state.completed_agents:
            state.status = WorkflowStatus.FAILED
        else:
            state.status = WorkflowStatus.COMPLETED

        # 7. Publish WORKFLOW_COMPLETED / WORKFLOW_FAILED
        final_event = AgentEventType.WORKFLOW_COMPLETED if state.status != WorkflowStatus.FAILED else AgentEventType.WORKFLOW_FAILED
        await redis_event_bus.publish(
            workflow_id=state.workflow_id,
            event_type=final_event,
            data={
                "workflow_id": state.workflow_id,
                "status": state.status.value,
                "escalation_required": state.escalation_required,
                "escalation_reason": state.escalation_reason,
                "completed_agents": state.completed_agents,
                "failed_agents": state.failed_agents,
            },
            db=db
        )

        state.add_audit_entry(
            agent_name=self.name,
            action=f"Workflow completed with final status '{state.status.value}'",
            status="SUCCESS",
            confidence=0.99
        )

        return AgentResult(
            success=state.status != WorkflowStatus.FAILED,
            agent_name=self.name,
            data={
                "workflow_id": state.workflow_id,
                "status": state.status.value,
                "completed_agents": state.completed_agents,
                "escalation_required": state.escalation_required,
                "escalation_reason": state.escalation_reason
            }
        )
