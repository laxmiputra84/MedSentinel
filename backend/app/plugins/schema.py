from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.plugin import ActionRiskLevel, ApprovalStatus, PluginStatus

class ToolRequest(BaseModel):
    workflow_id: Optional[str] = Field(None, description="Active multi-agent workflow UUID")
    user_id: Optional[int] = Field(None, description="Patient or actor user ID")
    agent_id: str = Field(..., description="Calling AI agent identifier")
    tool_name: str = Field(..., description="Action or tool verb (e.g. send_whatsapp_message, generate_excel_report)")
    resource_id: Optional[str] = Field(None, description="Target entity ID (e.g. claim_id, document_id, patient_id)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Input arguments for tool execution")
    permission: Optional[str] = Field(None, description="Required permission scope")
    risk_level: Optional[ActionRiskLevel] = Field(None, description="Assigned or inferred risk tier")
    approval_required: Optional[bool] = Field(None, description="Override for human-in-the-loop approval gate")
    idempotency_key: Optional[str] = Field(None, description="Unique key to avoid replay of critical actions")

class ToolResult(BaseModel):
    success: bool = Field(..., description="Whether action executed and verified successfully")
    status: str = Field(..., description="Status: SUCCESS, FAILED, PENDING_APPROVAL, PAUSED, PERMISSION_DENIED, RATE_LIMITED")
    result: Optional[Any] = Field(None, description="Output payload returned by plugin")
    external_id: Optional[str] = Field(None, description="Third-party transaction/message ID")
    error: Optional[str] = Field(None, description="Error message if failed")
    verification_status: str = Field("VERIFIED", description="VERIFIED, UNVERIFIED, or FAILED")
    audit_id: Optional[int] = Field(None, description="ID of the generated audit record")
    execution_time_ms: int = Field(0, description="Execution duration in milliseconds")

class PluginInfo(BaseModel):
    plugin_id: str
    name: str
    category: str
    provider: str
    status: PluginStatus
    is_enabled: bool
    icon: str
    description: str
    capabilities: List[str]
    permissions: List[str]
    rate_limit_rpm: int
    usage_count: int
    error_count: int
    last_used_at: Optional[str] = None
    last_tested_at: Optional[str] = None

class ApprovalRequestSchema(BaseModel):
    id: int
    workflow_id: Optional[str]
    user_id: Optional[int]
    agent_id: str
    plugin_id: str
    tool_name: str
    parameters: Dict[str, Any]
    risk_level: str
    status: str
    requester_notes: Optional[str]
    created_at: str

class ApprovalActionSchema(BaseModel):
    action: str = Field(..., description="APPROVE or REJECT")
    comment: Optional[str] = Field(None, description="Reviewer justification or notes")

class EmergencyToggleSchema(BaseModel):
    scope: str = Field("GLOBAL", description="GLOBAL, PLUGIN, AGENT, OUTBOUND, or EXTERNAL_API")
    target_id: Optional[str] = Field(None, description="Target plugin_id or agent_id if scope is specific")
    pause: bool = Field(..., description="True to pause, False to resume")
    reason: Optional[str] = Field(None, description="Justification for kill switch trigger")

class PluginConnectSchema(BaseModel):
    credentials: Dict[str, Any] = Field(default_factory=dict, description="Provider API keys, tokens, or webhook secrets")

class PluginPermissionsUpdateSchema(BaseModel):
    permissions: List[str] = Field(..., description="Updated list of allowed permission scopes")

class ApprovalDecisionSchema(BaseModel):
    comment: Optional[str] = Field(None, description="Reviewer justification or notes")

class ConfigFieldOption(BaseModel):
    label: str
    value: str

class ConfigFieldSchema(BaseModel):
    name: str
    label: str
    type: str  # text, password, url, select, checkbox, oauth, file
    required: bool = False
    description: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[ConfigFieldOption]] = None
    default: Optional[Any] = None
    button_label: Optional[str] = None
    provider: Optional[str] = None

class ConnectorMetadata(BaseModel):
    id: str
    name: str
    description: str
    category: str
    auth_type: str  # oauth, api_key, credentials, none
    status: str     # NOT CONFIGURED, CONNECTED, MOCK / SANDBOX, ERROR, PAUSED, REVOKED
    required_permissions: List[str]
    capabilities: List[str]
    icon: str = "extension"
    provider: str = ""
    config_schema: List[ConfigFieldSchema] = []
    is_enabled: bool = True
    last_tested_at: Optional[str] = None

class ConnectorStatusResponse(BaseModel):
    id: str
    name: str
    status: str
    is_enabled: bool
    last_tested_at: Optional[str] = None
    provider: Optional[str] = None
    error: Optional[str] = None

