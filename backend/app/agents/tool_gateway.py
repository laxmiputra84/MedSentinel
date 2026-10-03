"""
MedSentinel Agentic Architecture — Tool Gateway
Enforces zero-trust agent isolation: typed tool execution, RBAC, agent allowlists,
PII redaction, risk classification, and comprehensive audit trails.
"""

import re
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.user import User


class ToolRiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TypedToolDefinition(BaseModel):
    name: str
    description: str
    risk_tier: ToolRiskTier
    required_roles: List[str] = Field(default_factory=lambda: ["USER", "PATIENT", "DOCTOR", "HOSPITAL_ADMIN", "INSURANCE_ADMIN", "SUPER_ADMIN"])
    allowed_agents: List[str] = Field(default_factory=list)


class ToolExecutionResult(BaseModel):
    success: bool
    tool_name: str
    agent_name: str
    data: Dict[str, Any] = Field(default_factory=dict)
    redacted_data: Dict[str, Any] = Field(default_factory=dict)
    risk_tier: str
    duration_ms: float
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Global Agent Tool Allowlist (Security Isolation Matrix)
AGENT_TOOL_ALLOWLIST: Dict[str, Set[str]] = {
    "patient_intake": {"search_patient", "get_patient_timeline"},
    "patient_history": {"search_patient", "get_patient_timeline", "get_lab_results"},
    "document_intelligence": {"classify_document", "search_documents"},
    "ocr": {"extract_ocr"},
    "lab_analysis": {"analyze_lab_results", "get_lab_results"},
    "data_validation": {"validate_clinical_data"},
    "medication_safety": {"check_medication_safety"},
    "medical_rag": {"retrieve_medical_knowledge"},
    "clinical_rag": {"retrieve_medical_knowledge"},
    "risk_prediction": {"calculate_health_risk", "detect_claim_anomaly"},
    "claims": {"analyze_claim", "detect_claim_anomaly"},
    "data_analyst": {"run_healthcare_analytics"},
    "verification_report": {"generate_report", "search_documents"},
    "safety": {"evaluate_safety_policy"},
    "human_review": {"create_review_ticket"},
    "supervisor": {"*"},  # Supervisor has global coordination permission
}


class PIIRedactor:
    """Masks sensitive patient identifiers in tool payloads and logs."""

    EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-])[a-zA-Z0-9_.+-]*@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
    PHONE_REGEX = re.compile(r"(\+?\d{1,4}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}")
    AADHAAR_REGEX = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
    PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

    @classmethod
    def redact_text(cls, text: str) -> str:
        if not isinstance(text, str):
            return text
        text = cls.EMAIL_REGEX.sub(r"\1***@\2", text)
        text = cls.AADHAAR_REGEX.sub(r"****-****-****", text)
        text = cls.PAN_REGEX.sub(r"*****REDACTED*****", text)
        text = cls.PHONE_REGEX.sub(r"***-***-****", text)
        return text

    @classmethod
    def redact_dict(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: cls.redact_dict(v) if k not in ["phone", "email", "ssn", "aadhaar", "pan"] else "***REDACTED***" for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.redact_dict(item) for item in data]
        elif isinstance(data, str):
            return cls.redact_text(data)
        return data


class AgentToolGateway:
    """
    Central mediator through which all specialized agents execute typed tools.
    Never allows an agent to access database queries or external APIs directly.
    """

    def __init__(self):
        self._tools: Dict[str, Tuple[TypedToolDefinition, Callable]] = {}
        self._audit_log: List[Dict[str, Any]] = []

    def register_tool(self, definition: TypedToolDefinition, handler: Callable):
        self._tools[definition.name] = (definition, handler)

    def is_tool_allowed(self, agent_name: str, tool_name: str) -> bool:
        allowed = AGENT_TOOL_ALLOWLIST.get(agent_name, set())
        return ("*" in allowed) or (tool_name in allowed)

    async def execute(
        self,
        agent_name: str,
        tool_name: str,
        parameters: Dict[str, Any],
        user: Optional[User] = None,
        db: Optional[Session] = None
    ) -> ToolExecutionResult:
        start_time = time.perf_counter()

        # 1. Existence Check
        if tool_name not in self._tools:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                agent_name=agent_name,
                risk_tier=ToolRiskTier.LOW.value,
                duration_ms=0.0,
                error=f"Tool '{tool_name}' is not registered in Tool Gateway."
            )

        definition, handler = self._tools[tool_name]

        # 2. Agent Allowlist Check
        if not self.is_tool_allowed(agent_name, tool_name):
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                agent_name=agent_name,
                risk_tier=definition.risk_tier.value,
                duration_ms=0.0,
                error=f"Security Violation: Agent '{agent_name}' is not permitted to call tool '{tool_name}'."
            )

        # 3. RBAC Role Check
        user_role = (user.role if user and user.role else "USER").upper()
        if user_role not in definition.required_roles and user_role != "SUPER_ADMIN":
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                agent_name=agent_name,
                risk_tier=definition.risk_tier.value,
                duration_ms=0.0,
                error=f"RBAC Access Denied: User role '{user_role}' lacks permission for tool '{tool_name}'."
            )

        # 3b. Strict Cross-Patient Isolation Check
        target_patient_id = parameters.get("patient_id")
        if user and user_role in ["USER", "PATIENT"] and target_patient_id and db:
            from app.models.patient import Patient
            target_pt = db.query(Patient).filter(Patient.id == target_patient_id).first()
            if target_pt and target_pt.user_id != user.id:
                return ToolExecutionResult(
                    success=False,
                    tool_name=tool_name,
                    agent_name=agent_name,
                    risk_tier=definition.risk_tier.value,
                    duration_ms=0.0,
                    error=f"Security Violation: Cross-patient data access blocked for patient_id {target_patient_id}."
                )

        # 4. Tool Execution
        try:
            exec_params = dict(parameters)
            import inspect
            sig = inspect.signature(handler)
            if "db" in sig.parameters and "db" not in exec_params and db is not None:
                exec_params["db"] = db
            if "user" in sig.parameters and "user" not in exec_params and user is not None:
                exec_params["user"] = user

            # Check if handler is coroutine
            if inspect.iscoroutinefunction(handler):
                raw_result = await handler(**exec_params)
            else:
                raw_result = handler(**exec_params)

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            redacted = PIIRedactor.redact_dict(raw_result)

            res = ToolExecutionResult(
                success=True,
                tool_name=tool_name,
                agent_name=agent_name,
                data=raw_result if isinstance(raw_result, dict) else {"result": raw_result},
                redacted_data=redacted if isinstance(redacted, dict) else {"result": redacted},
                risk_tier=definition.risk_tier.value,
                duration_ms=duration_ms
            )

            # Record audit entry
            self._audit_log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_name": agent_name,
                "tool_name": tool_name,
                "risk_tier": definition.risk_tier.value,
                "user_id": user.id if user else None,
                "duration_ms": duration_ms,
                "status": "SUCCESS"
            })

            return res

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                agent_name=agent_name,
                risk_tier=definition.risk_tier.value,
                duration_ms=duration_ms,
                error=f"Tool execution exception: {str(e)}"
            )


# Global singleton instance
agent_tool_gateway = AgentToolGateway()
