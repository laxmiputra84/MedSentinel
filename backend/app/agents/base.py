"""
MedSentinel Agentic Architecture — Base Agent Contract
Abstract base class defining standardized execution, lifecycle hooks, error handling,
timing telemetry, confidence scoring, and audit logging for all MedSentinel agents.
"""

import abc
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.state import (
    WorkflowState,
    AgentResult,
    AgentExecutionLog,
    AgentStatus,
    AuditEntry,
    ClinicalFinding,
    EscalationLevel,
)


class BaseAgent(abc.ABC):
    """
    Abstract Base Class for all MedSentinel Specialized Agents.
    Enforces standard execution interface, telemetry, error containment,
    and structured audit logging.
    """

    def __init__(
        self,
        name: str,
        role: str,
        description: str,
        version: str = "1.0.0"
    ):
        self.name = name
        self.role = role
        self.description = description
        self.version = version

    @abc.abstractmethod
    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Specialized agent logic to be implemented by child classes.
        Must return a valid AgentResult.
        """
        pass

    async def run(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Standard execution wrapper:
        - Tracks execution timing
        - Handles errors without crashing pipeline
        - Appends telemetry to state.execution_logs
        - Appends audit events to state.audit_trail
        - Updates workflow state progress
        """
        start_time = time.perf_counter()
        started_at = datetime.now(timezone.utc)
        state.current_agent = self.name

        execution_log = AgentExecutionLog(
            agent_name=self.name,
            status=AgentStatus.RUNNING,
            started_at=started_at,
            inputs_summary={
                "workflow_id": state.workflow_id,
                "document_id": state.document_id,
                "patient_id": state.patient_id,
                "workflow_type": state.workflow_type.value,
            }
        )

        try:
            # Delegate to specialized execute method
            result = await self.execute(state=state, db=db, context=context)

            # Execution timing
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            completed_at = datetime.now(timezone.utc)

            execution_log.status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED
            execution_log.completed_at = completed_at
            execution_log.duration_ms = duration_ms
            execution_log.outputs_summary = {k: str(v)[:200] for k, v in result.data.items()}
            execution_log.confidence = result.data.get("confidence", 0.90)

            result.execution_log = execution_log
            state.add_execution_log(execution_log)

            if result.success:
                state.mark_agent_completed(self.name)
                # Propagate findings into workflow state
                for finding in result.findings:
                    state.add_clinical_finding(finding)

                # Record successful audit entry
                state.add_audit_entry(
                    agent_name=self.name,
                    action=f"Agent '{self.name}' completed successfully",
                    tool_used=execution_log.tool_called,
                    status="SUCCESS",
                    confidence=execution_log.confidence,
                    details={"duration_ms": duration_ms, "keys": list(result.data.keys())}
                )
            else:
                state.mark_agent_failed(self.name)
                error_msg = "; ".join(result.errors) if result.errors else "Unknown agent error"
                execution_log.error_message = error_msg
                state.add_audit_entry(
                    agent_name=self.name,
                    action=f"Agent '{self.name}' failed",
                    status="FAILED",
                    error=error_msg,
                    details={"duration_ms": duration_ms}
                )

            return result

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            completed_at = datetime.now(timezone.utc)
            error_str = f"Unhandled exception in {self.name}: {str(exc)}"

            execution_log.status = AgentStatus.FAILED
            execution_log.completed_at = completed_at
            execution_log.duration_ms = duration_ms
            execution_log.error_message = error_str

            state.add_execution_log(execution_log)
            state.mark_agent_failed(self.name)

            state.add_audit_entry(
                agent_name=self.name,
                action=f"Agent '{self.name}' encountered unhandled exception",
                status="ERROR",
                error=error_str,
                details={"duration_ms": duration_ms}
            )

            return AgentResult(
                success=False,
                agent_name=self.name,
                errors=[error_str],
                execution_log=execution_log
            )

    def create_finding(
        self,
        title: str,
        description: str,
        category: str = "GENERAL",
        parameter_name: Optional[str] = None,
        observed_value: Optional[float] = None,
        reference_range: Optional[str] = None,
        unit: Optional[str] = None,
        status: str = "NORMAL",
        is_critical: bool = False,
        evidence: Optional[str] = None,
        confidence: float = 0.90
    ) -> ClinicalFinding:
        """Helper to create a standard, verified clinical finding."""
        return ClinicalFinding(
            category=category,
            title=title,
            description=description,
            parameter_name=parameter_name,
            observed_value=observed_value,
            reference_range=reference_range,
            unit=unit,
            status=status,
            is_critical=is_critical,
            evidence=evidence,
            confidence=confidence
        )

    async def call_plugin_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        state: Optional[WorkflowState] = None,
        db: Optional[Session] = None,
        permission: Optional[str] = None
    ):
        """
        Dispatches an external or internal tool action through the zero-trust Plugin Gateway.
        Ensures agents never call external APIs directly.
        """
        from app.plugins import ToolRequest, plugin_manager
        req = ToolRequest(
            workflow_id=state.workflow_id if state else None,
            user_id=state.patient_info.user_id if (state and state.patient_info and hasattr(state.patient_info, 'user_id')) else None,
            agent_id=self.name,
            tool_name=tool_name,
            parameters=parameters,
            permission=permission
        )
        return await plugin_manager.execute_tool(req, db=db)
