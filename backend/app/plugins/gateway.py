import time
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models import User
from app.models.plugin import PluginActionAudit, PluginApprovalRequest, ActionRiskLevel, ApprovalStatus
from app.plugins.schema import ToolRequest, ToolResult
from app.plugins.policy import PolicyEngine
from app.plugins.emergency import emergency_controller
from app.plugins.base import BasePlugin

logger = logging.getLogger("medsentinel.plugins.gateway")

class ToolGateway:
    """
    Central Zero-Trust Tool Gateway.
    All external plugin actions must flow through this gateway.
    Never allows an AI agent to call external services directly.
    """

    def __init__(self, policy_engine: Optional[PolicyEngine] = None):
        self.policy_engine = policy_engine or PolicyEngine()
        self._rate_limits: Dict[str, list] = {}

    def _check_rate_limit(self, plugin: BasePlugin) -> bool:
        now = time.time()
        window = 60.0 # 1 minute
        history = self._rate_limits.setdefault(plugin.plugin_id, [])
        # Prune old timestamps
        history[:] = [ts for ts in history if now - ts < window]
        if len(history) >= plugin.rate_limit_rpm:
            return False
        history.append(now)
        return True

    async def execute_tool(
        self,
        request: ToolRequest,
        plugin: BasePlugin,
        db: Optional[Session] = None,
        current_user: Optional[User] = None
    ) -> ToolResult:
        t0 = time.time()
        agent_id = request.agent_id
        plugin_id = plugin.plugin_id
        tool_name = request.tool_name

        # 1. EMERGENCY KILL SWITCH CHECK
        allowed, kill_reason = emergency_controller.is_action_allowed(agent_id, plugin_id, tool_name)
        if not allowed:
            result = ToolResult(
                success=False,
                status="PAUSED",
                error=kill_reason,
                verification_status="FAILED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )
            self._record_audit(db, request, plugin_id, result, decision="BLOCKED_BY_KILL_SWITCH", risk_level=ActionRiskLevel.CRITICAL)
            return result

        # 2. PLUGIN STATUS & ENABLED CHECK
        if not plugin.is_enabled or plugin.status.value in ["PAUSED", "DISCONNECTED", "REVOKED"]:
            result = ToolResult(
                success=False,
                status="PAUSED" if plugin.status.value == "PAUSED" else "FAILED",
                error=f"Plugin '{plugin.name}' is currently {plugin.status.value} (is_enabled={plugin.is_enabled}).",
                verification_status="FAILED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )
            self._record_audit(db, request, plugin_id, result, decision="BLOCKED_INACTIVE_PLUGIN", risk_level=ActionRiskLevel.LOW)
            return result

        # 3. RATE LIMITING CHECK
        if not self._check_rate_limit(plugin):
            result = ToolResult(
                success=False,
                status="RATE_LIMITED",
                error=f"Plugin '{plugin.name}' rate limit of {plugin.rate_limit_rpm} requests/min exceeded. Please throttle requests.",
                verification_status="FAILED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )
            self._record_audit(db, request, plugin_id, result, decision="RATE_LIMITED", risk_level=ActionRiskLevel.LOW)
            return result

        # 4. PERMISSION SCOPE CHECK
        if not plugin.validate_permissions(request.permission):
            result = ToolResult(
                success=False,
                status="PERMISSION_DENIED",
                error=f"Plugin '{plugin.name}' does not hold required permission: {request.permission}",
                verification_status="FAILED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )
            self._record_audit(db, request, plugin_id, result, decision="PERMISSION_DENIED", risk_level=ActionRiskLevel.HIGH)
            return result

        # 5. ZERO-TRUST POLICY & RISK EVALUATION
        is_permitted, risk_tier, approval_required, policy_reason = self.policy_engine.evaluate(request)

        # 6. HUMAN-IN-THE-LOOP APPROVAL GATE
        if approval_required:
            # Create a pending approval request in database
            approval_id = None
            if db:
                try:
                    approval_req = PluginApprovalRequest(
                        workflow_id=request.workflow_id,
                        user_id=request.user_id or (current_user.id if current_user else None),
                        agent_id=request.agent_id,
                        plugin_id=plugin_id,
                        tool_name=tool_name,
                        parameters=plugin.mask_pii(request.parameters),
                        risk_level=risk_tier.value,
                        status=ApprovalStatus.PENDING.value,
                        requester_notes=f"Action '{tool_name}' triggered by {agent_id} flagged for mandatory human review."
                    )
                    db.add(approval_req)
                    db.commit()
                    db.refresh(approval_req)
                    approval_id = approval_req.id
                except Exception as e:
                    logger.error(f"Error persisting approval request: {e}")
                    db.rollback()

            result = ToolResult(
                success=False,
                status="PENDING_APPROVAL",
                error=f"Action requires human authorization before execution. Approval Request #{approval_id} queued.",
                result={"approval_request_id": approval_id, "risk_level": risk_tier.value, "gate": "HUMAN_IN_THE_LOOP"},
                verification_status="UNVERIFIED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )
            self._record_audit(
                db, request, plugin_id, result,
                decision="QUEUED_FOR_HUMAN_APPROVAL",
                risk_level=risk_tier,
                approval_status="PENDING"
            )
            return result

        # 7. EXECUTE VIA SECURE PLUGIN DISPATCH
        try:
            plugin_context = {
                "user_id": request.user_id or (current_user.id if current_user else None),
                "workflow_id": request.workflow_id,
                "agent_id": request.agent_id,
            }
            tool_result = await plugin.execute(tool_name, request.parameters, plugin_context)
            tool_result.execution_time_ms = int((time.time() - t0) * 1000)

            # 8. AUDIT LOGGING
            audit_id = self._record_audit(
                db, request, plugin_id, tool_result,
                decision="EXECUTED_SUCCESSFULLY" if tool_result.success else "EXECUTION_FAILED",
                risk_level=risk_tier,
                approval_status="NOT_REQUIRED"
            )
            tool_result.audit_id = audit_id
            return tool_result

        except Exception as ex:
            logger.error(f"Plugin execution failure in {plugin_id}: {ex}", exc_info=True)
            plugin.error_count += 1
            err_result = ToolResult(
                success=False,
                status="FAILED",
                error=f"Connector error in {plugin.name}: {str(ex)}",
                verification_status="FAILED",
                execution_time_ms=int((time.time() - t0) * 1000)
            )
            audit_id = self._record_audit(
                db, request, plugin_id, err_result,
                decision="EXCEPTION_THROWN",
                risk_level=risk_tier,
                approval_status="NOT_REQUIRED",
                error_msg=str(ex)
            )
            err_result.audit_id = audit_id
            return err_result

    def _record_audit(
        self,
        db: Optional[Session],
        request: ToolRequest,
        plugin_id: str,
        result: ToolResult,
        decision: str,
        risk_level: ActionRiskLevel,
        approval_status: str = "NOT_REQUIRED",
        error_msg: Optional[str] = None
    ) -> Optional[int]:
        if not db:
            return None
        try:
            audit = PluginActionAudit(
                workflow_id=request.workflow_id,
                user_id=request.user_id,
                agent_id=request.agent_id,
                plugin_id=plugin_id,
                tool_name=request.tool_name,
                resource_id=request.resource_id,
                risk_level=risk_level.value,
                parameters_masked=BasePlugin.mask_pii(request.parameters),
                decision=decision,
                policy_evaluation="PASSED" if result.success or result.status == "PENDING_APPROVAL" else "BLOCKED",
                approval_status=approval_status,
                external_transaction_id=result.external_id,
                result_summary=str(result.result)[:500] if result.result else None,
                verification_status=result.verification_status,
                error_message=error_msg or result.error,
                latency_ms=result.execution_time_ms
            )
            db.add(audit)
            db.commit()
            db.refresh(audit)
            return audit.id
        except Exception as e:
            logger.error(f"Failed to record plugin audit log: {e}")
            db.rollback()
            return None
