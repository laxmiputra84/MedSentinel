from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.models.plugin import ActionRiskLevel

class ToolDefinition(BaseModel):
    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Human and agent readable tool description")
    plugin_id: str = Field(..., description="Plugin connector providing this tool")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema defining input parameters")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema defining output structure")
    risk_level: ActionRiskLevel = Field(default=ActionRiskLevel.LOW, description="Risk tier: LOW, MEDIUM, HIGH, CRITICAL")
    required_permissions: List[str] = Field(default_factory=list, description="Plugin permission scopes required")
    allowed_roles: List[str] = Field(
        default=["super_admin", "admin", "hospital_admin", "insurance_admin", "doctor", "staff", "patient"],
        description="User roles permitted to invoke this tool"
    )
    approval_required: bool = Field(default=False, description="Whether human administrator authorization is required")
    audit_required: bool = Field(default=True, description="Whether execution must be logged in tamper-evident audit ledger")
    idempotency_required: bool = Field(default=False, description="Whether duplicate calls within 5m window are deduped")

class ToolRegistry:
    """
    Central Tool Registry for MedSentinel Agentic AI.
    Catalogues every capability across all 18 plugin connectors,
    enforcing schemas, risk classifications, RBAC roles, and approval rules.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._bootstrap_tools()

    def register_tool(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self, plugin_id: Optional[str] = None) -> List[ToolDefinition]:
        if plugin_id:
            return [t for t in self._tools.values() if t.plugin_id == plugin_id]
        return list(self._tools.values())

    def _bootstrap_tools(self) -> None:
        # Communication Tools
        self.register_tool(ToolDefinition(
            name="send_whatsapp_message",
            description="Sends a WhatsApp message to a patient phone number.",
            plugin_id="whatsapp",
            input_schema={"phone": "string", "message": "string"},
            output_schema={"success": "boolean", "message_id": "string"},
            risk_level=ActionRiskLevel.MEDIUM,
            required_permissions=["whatsapp.send"],
            allowed_roles=["super_admin", "admin", "hospital_admin", "doctor"],
            approval_required=False,
            idempotency_required=True
        ))
        self.register_tool(ToolDefinition(
            name="send_whatsapp_template",
            description="Sends a pre-approved WhatsApp Business template.",
            plugin_id="whatsapp",
            input_schema={"phone": "string", "template_name": "string", "parameters": "dict"},
            output_schema={"success": "boolean", "message_id": "string"},
            risk_level=ActionRiskLevel.MEDIUM,
            required_permissions=["whatsapp.template"],
            allowed_roles=["super_admin", "admin", "hospital_admin"],
            approval_required=False,
            idempotency_required=True
        ))
        self.register_tool(ToolDefinition(
            name="send_sms",
            description="Dispatches an SMS notification to a verified mobile number.",
            plugin_id="sms",
            input_schema={"phone": "string", "message": "string"},
            output_schema={"success": "boolean", "message_id": "string"},
            risk_level=ActionRiskLevel.MEDIUM,
            required_permissions=["sms.send"],
            allowed_roles=["super_admin", "admin", "hospital_admin", "doctor"],
            approval_required=False,
            idempotency_required=True
        ))
        self.register_tool(ToolDefinition(
            name="send_otp",
            description="Sends a cryptographic one-time passcode for patient verification.",
            plugin_id="sms",
            input_schema={"phone": "string"},
            output_schema={"success": "boolean", "otp_sent": "boolean"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["sms.otp"],
            allowed_roles=["super_admin", "admin", "doctor", "staff", "patient"],
            approval_required=False,
            idempotency_required=False
        ))
        self.register_tool(ToolDefinition(
            name="verify_otp",
            description="Validates a cryptographic one-time passcode entered by a user.",
            plugin_id="sms",
            input_schema={"phone": "string", "otp": "string"},
            output_schema={"valid": "boolean"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["sms.otp"],
            allowed_roles=["super_admin", "admin", "doctor", "staff", "patient"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="read_email",
            description="Fetches and inspects an authorized email thread from Gmail.",
            plugin_id="gmail",
            input_schema={"query": "string"},
            output_schema={"messages": "list"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["gmail.read"],
            allowed_roles=["super_admin", "admin"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="create_email_draft",
            description="Creates an email draft in Gmail without sending.",
            plugin_id="gmail",
            input_schema={"recipient": "string", "subject": "string", "body": "string"},
            output_schema={"draft_id": "string"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["gmail.draft"],
            allowed_roles=["super_admin", "admin", "doctor"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="send_email",
            description="Sends an email via universal email connector.",
            plugin_id="email",
            input_schema={"to": "string", "subject": "string", "body": "string"},
            output_schema={"success": "boolean", "message_id": "string"},
            risk_level=ActionRiskLevel.MEDIUM,
            required_permissions=["email.send"],
            allowed_roles=["super_admin", "admin"],
            approval_required=False,
            idempotency_required=True
        ))

        # Files & Data Tools
        self.register_tool(ToolDefinition(
            name="upload_file",
            description="Uploads a medical document with MIME validation and malware scan.",
            plugin_id="files",
            input_schema={"filename": "string", "content": "bytes", "mime_type": "string"},
            output_schema={"success": "boolean", "sha256": "string", "file_path": "string"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["file.upload"],
            allowed_roles=["super_admin", "admin", "doctor", "staff", "patient"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="read_excel",
            description="Reads and validates spreadsheet records.",
            plugin_id="excel",
            input_schema={"content": "string"},
            output_schema={"rows": "list", "headers": "list"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["excel.read"],
            allowed_roles=["super_admin", "admin", "doctor", "staff"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="clean_csv",
            description="Cleans whitespace and removes duplicate records from CSV data.",
            plugin_id="csv",
            input_schema={"content": "string", "key_columns": "list"},
            output_schema={"duplicates_removed": "int", "cleaned_csv_preview": "list"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["csv.clean"],
            allowed_roles=["super_admin", "admin", "doctor", "staff"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="analyze_image",
            description="Performs OCR and visual classification on medical images.",
            plugin_id="images",
            input_schema={"filename": "string"},
            output_schema={"ocr_text": "string", "findings": "list", "clinical_disclaimer": "string"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["image.ocr"],
            allowed_roles=["super_admin", "admin", "doctor"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="generate_pdf",
            description="Synthesizes structured PDF document with cryptographic hash.",
            plugin_id="pdf",
            input_schema={"title": "string", "content": "string"},
            output_schema={"sha256": "string", "pdf_bytes": "bytes"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["pdf.generate"],
            allowed_roles=["super_admin", "admin", "doctor", "staff"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="generate_docx",
            description="Synthesizes administrative DOCX report or patient letter.",
            plugin_id="word",
            input_schema={"title": "string", "content": "string"},
            output_schema={"sha256": "string", "file_path": "string"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["document.generate"],
            allowed_roles=["super_admin", "admin", "doctor", "staff"],
            approval_required=False
        ))

        # Storage & Productivity Tools
        self.register_tool(ToolDefinition(
            name="cloud_upload",
            description="Stores a document in configured S3 or Cloud Storage.",
            plugin_id="storage",
            input_schema={"path": "string", "content": "string"},
            output_schema={"url": "string", "storage_tier": "string"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["storage.write"],
            allowed_roles=["super_admin", "admin"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="create_appointment",
            description="Schedules a clinical appointment with conflict detection.",
            plugin_id="calendar",
            input_schema={"doctor_id": "string", "patient_id": "string", "start_time": "string"},
            output_schema={"appointment_id": "string", "confirmed": "boolean"},
            risk_level=ActionRiskLevel.MEDIUM,
            required_permissions=["calendar.write"],
            allowed_roles=["super_admin", "admin", "doctor", "staff", "patient"],
            approval_required=False,
            idempotency_required=True
        ))

        # Healthcare & High-Impact Tools (Mandatory Human Approval)
        self.register_tool(ToolDefinition(
            name="search_hospitals",
            description="Searches hospitals and doctor availability in the network.",
            plugin_id="hospital",
            input_schema={"query": "string", "specialty": "string"},
            output_schema={"hospitals": "list"},
            risk_level=ActionRiskLevel.LOW,
            required_permissions=["hospital.read"],
            allowed_roles=["super_admin", "admin", "doctor", "staff", "patient"],
            approval_required=False
        ))
        self.register_tool(ToolDefinition(
            name="submit_claim",
            description="Submits an insurance claim to TPA/payer FHIR gateway. HIGH RISK.",
            plugin_id="insurance",
            input_schema={"claim_id": "string", "amount": "float", "diagnosis_code": "string"},
            output_schema={"claim_reference": "string", "status": "string"},
            risk_level=ActionRiskLevel.HIGH,
            required_permissions=["insurance.claim"],
            allowed_roles=["super_admin", "insurance_admin"],
            approval_required=True, # MANDATORY HUMAN APPROVAL
            idempotency_required=True
        ))
        self.register_tool(ToolDefinition(
            name="refund_payment",
            description="Executes a financial refund transaction. HIGH RISK.",
            plugin_id="payment",
            input_schema={"transaction_id": "string", "amount": "float", "reason": "string"},
            output_schema={"refund_id": "string", "status": "string"},
            risk_level=ActionRiskLevel.HIGH,
            required_permissions=["payment.refund"],
            allowed_roles=["super_admin"],
            approval_required=True, # MANDATORY HUMAN APPROVAL
            idempotency_required=True
        ))
        self.register_tool(ToolDefinition(
            name="custom_api_request",
            description="Dispatches a secure HTTP request to a whitelisted external API.",
            plugin_id="custom_api",
            input_schema={"url": "string", "method": "string", "headers": "dict", "body": "any"},
            output_schema={"status_code": "int", "data": "any"},
            risk_level=ActionRiskLevel.MEDIUM,
            required_permissions=["api.request"],
            allowed_roles=["super_admin", "admin"],
            approval_required=False,
            idempotency_required=False
        ))

tool_registry = ToolRegistry()
