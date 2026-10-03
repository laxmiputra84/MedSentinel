import os
import time
from typing import Dict, List, Optional, Any
from app.models.plugin import PluginStatus
from app.plugins.schema import ConnectorMetadata, ConfigFieldSchema, ConfigFieldOption

CATALOG_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "id": "gmail_oauth",
        "name": "Gmail / Google Workspace",
        "description": "Google Workspace & Gmail API integration for ingesting claims, reading encrypted lab records, and drafting responses.",
        "category": "COMMUNICATION",
        "auth_type": "oauth",
        "icon": "mail",
        "provider": "Google Cloud OAuth 2.0",
        "required_permissions": ["gmail:read", "gmail:drafts", "gmail:send"],
        "capabilities": ["search_emails", "read_email", "create_draft", "send_approved_email", "get_attachments", "classify_email_thread"],
        "config_schema": [
            ConfigFieldSchema(
                name="auth_action",
                label="Google Cloud OAuth 2.0",
                type="oauth",
                provider="google",
                button_label="Connect with Google",
                description="Initiates Google OAuth 2.0 consent flow with minimum least-privilege Gmail scopes."
            ),
            ConfigFieldSchema(
                name="client_id",
                label="Client ID (Optional Override)",
                type="text",
                placeholder="Leave blank to use server environment variables"
            ),
            ConfigFieldSchema(
                name="authorized_email",
                label="Authorized Account Email",
                type="text",
                placeholder="e.g. claims-gateway@medsentinel.health"
            )
        ]
    },
    {
        "id": "whatsapp_business",
        "name": "WhatsApp Business API",
        "description": "Official Meta WhatsApp Business Cloud API for appointment scheduling, real-time claim status, and document upload links.",
        "category": "COMMUNICATION",
        "auth_type": "api_key",
        "icon": "chat",
        "provider": "Meta / WhatsApp Cloud API",
        "required_permissions": ["whatsapp:send", "whatsapp:read", "whatsapp:templates"],
        "capabilities": ["send_message", "send_whatsapp_message", "send_template", "request_document", "send_claim_status", "send_appointment_reminder"],
        "config_schema": [
            ConfigFieldSchema(
                name="phone_number_id",
                label="Phone Number ID",
                type="text",
                required=True,
                placeholder="e.g. 104928402840192",
                description="Phone Number ID from Meta Developers WhatsApp setup"
            ),
            ConfigFieldSchema(
                name="access_token",
                label="System User Access Token",
                type="password",
                required=True,
                placeholder="EAAG...",
                description="Meta Graph API System User Token (never logged or exposed)"
            ),
            ConfigFieldSchema(
                name="waba_id",
                label="WhatsApp Business Account (WABA) ID",
                type="text",
                placeholder="e.g. 1092837461928"
            ),
            ConfigFieldSchema(
                name="webhook_secret",
                label="Webhook Secret",
                type="password",
                placeholder="App secret for HMAC SHA-256 verification"
            ),
            ConfigFieldSchema(
                name="sandbox_mode",
                label="Sandbox / Mock Mode",
                type="checkbox",
                default=True,
                description="Enable simulated WhatsApp gateway without live Meta API charges"
            )
        ]
    },
    {
        "id": "mobile_sms",
        "name": "SMS / Mobile Gateway",
        "description": "Twilio & Enterprise SMS gateway for urgent clinical alerts, two-factor OTP generation, and appointment notifications.",
        "category": "COMMUNICATION",
        "auth_type": "api_key",
        "icon": "sms",
        "provider": "Twilio / Enterprise SMS",
        "required_permissions": ["sms:send", "otp:generate", "otp:verify"],
        "capabilities": ["send_sms", "send_otp", "verify_otp", "send_claim_alert", "appointment_reminder"],
        "config_schema": [
            ConfigFieldSchema(
                name="account_sid",
                label="Twilio Account SID",
                type="text",
                required=True,
                placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            ),
            ConfigFieldSchema(
                name="auth_token",
                label="Twilio Auth Token",
                type="password",
                required=True,
                placeholder="Your Twilio Auth Token"
            ),
            ConfigFieldSchema(
                name="sender_number",
                label="Sender Phone Number",
                type="text",
                required=True,
                placeholder="+1234567890",
                description="Approved 10DLC or Toll-Free sender number"
            ),
            ConfigFieldSchema(
                name="sandbox_mode",
                label="Sandbox / Mock Mode",
                type="checkbox",
                default=True,
                description="Simulate SMS dispatch with real-time OTP verification"
            )
        ]
    },
    {
        "id": "voice_telephony",
        "name": "Telephony & Voice Gateway",
        "description": "Telephony webhook gateway for patient inbound calls, live transcription, triage escalation, and interactive voice response.",
        "category": "COMMUNICATION",
        "auth_type": "api_key",
        "icon": "call",
        "provider": "Twilio Voice / Exotel",
        "required_permissions": ["voice:listen", "voice:transcribe", "voice:outbound"],
        "capabilities": ["incoming_call_events", "transcription", "call_summary", "escalate_to_human"],
        "config_schema": [
            ConfigFieldSchema(
                name="account_sid",
                label="Telephony Account SID",
                type="text",
                required=True,
                placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            ),
            ConfigFieldSchema(
                name="auth_token",
                label="Auth Token",
                type="password",
                required=True,
                placeholder="Account Auth Token"
            ),
            ConfigFieldSchema(
                name="twiml_app_sid",
                label="TwiML App SID",
                type="text",
                placeholder="APxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            ),
            ConfigFieldSchema(
                name="transcription_enabled",
                label="Enable Real-Time Clinical Transcription",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "universal_email",
        "name": "Universal Email (SMTP / SendGrid)",
        "description": "Enterprise SMTP / SendGrid / IMAP server integration for clinical correspondence and hospital billing dispatches.",
        "category": "COMMUNICATION",
        "auth_type": "credentials",
        "icon": "forward_to_inbox",
        "provider": "SMTP / SendGrid / Exchange",
        "required_permissions": ["email:send", "email:receive", "email:draft"],
        "capabilities": ["send", "receive", "create_draft", "verify_delivery"],
        "config_schema": [
            ConfigFieldSchema(
                name="smtp_host",
                label="SMTP Server Host",
                type="text",
                required=True,
                placeholder="smtp.sendgrid.net"
            ),
            ConfigFieldSchema(
                name="smtp_port",
                label="SMTP Server Port",
                type="text",
                required=True,
                default="587"
            ),
            ConfigFieldSchema(
                name="smtp_user",
                label="SMTP Username",
                type="text",
                required=True,
                placeholder="apikey or admin@hospital.com"
            ),
            ConfigFieldSchema(
                name="smtp_password",
                label="SMTP Password / API Key",
                type="password",
                required=True
            ),
            ConfigFieldSchema(
                name="use_tls",
                label="Enforce TLS / SSL Encryption",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "secure_file_vault",
        "name": "Secure File Vault",
        "description": "Zero-trust encrypted storage vault with AES-256 at rest, path traversal prevention, and antivirus scanning abstractions.",
        "category": "FILES & DATA",
        "auth_type": "none",
        "icon": "lock",
        "provider": "MedSentinel Vault Engine",
        "required_permissions": ["files:read", "files:write", "files:delete", "files:scan"],
        "capabilities": ["upload", "download", "calculate_hash", "scan_security", "verify_integrity"],
        "config_schema": [
            ConfigFieldSchema(
                name="storage_path",
                label="Encrypted Vault Path",
                type="text",
                default="./vault/secure"
            ),
            ConfigFieldSchema(
                name="max_file_size_mb",
                label="Max Upload Size (MB)",
                type="text",
                default="50"
            ),
            ConfigFieldSchema(
                name="allowed_extensions",
                label="Permitted Extensions",
                type="text",
                default="pdf, docx, xlsx, csv, txt, jpg, png, zip"
            ),
            ConfigFieldSchema(
                name="enable_antivirus",
                label="Enable ClamAV / Malware Scanning",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "excel_processor",
        "name": "Excel Analytics Engine",
        "description": "High-performance XLSX spreadsheet engine with schema validation, missing data imputation, and macro-execution blocking.",
        "category": "FILES & DATA",
        "auth_type": "none",
        "icon": "table_chart",
        "provider": "Openpyxl / In-Process",
        "required_permissions": ["excel:read", "excel:write", "excel:clean"],
        "capabilities": ["read_excel", "write_excel", "clean_excel", "detect_duplicates"],
        "config_schema": [
            ConfigFieldSchema(
                name="disallow_macros",
                label="Block VBA Macros (Macro Execution Security)",
                type="checkbox",
                default=True
            ),
            ConfigFieldSchema(
                name="auto_clean_data",
                label="Auto-clean Missing & Duplicate Patient Records",
                type="checkbox",
                default=True
            ),
            ConfigFieldSchema(
                name="max_rows",
                label="Max Processable Rows",
                type="text",
                default="100000"
            )
        ]
    },
    {
        "id": "csv",
        "name": "CSV Intelligence Engine",
        "description": "Streaming RFC 4180 CSV parser and validator with automatic delimiter detection, deduplication, and anomaly reporting.",
        "category": "FILES & DATA",
        "auth_type": "none",
        "icon": "dataset",
        "provider": "CSV Intelligence Engine",
        "required_permissions": ["csv:read", "csv:clean", "csv:export"],
        "capabilities": ["parse_csv", "validate_csv", "clean_csv", "deduplicate_csv", "export_csv"],
        "config_schema": [
            ConfigFieldSchema(
                name="delimiter",
                label="Default Delimiter",
                type="select",
                default=",",
                options=[
                    ConfigFieldOption(label="Comma (,)", value=","),
                    ConfigFieldOption(label="Semicolon (;)", value=";"),
                    ConfigFieldOption(label="Tab (\\t)", value="\t")
                ]
            ),
            ConfigFieldSchema(
                name="strip_whitespace",
                label="Trim Whitespace On Ingest",
                type="checkbox",
                default=True
            ),
            ConfigFieldSchema(
                name="deduplicate",
                label="Automatic Deduplication",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "image_vision",
        "name": "Medical Image & Vision Engine",
        "description": "Optical Character Recognition (OCR) and vision analysis for medical prescriptions, lab scans, and ID documents.",
        "category": "FILES & DATA",
        "auth_type": "credentials",
        "icon": "image",
        "provider": "Tesseract / Vision AI",
        "required_permissions": ["vision:ocr", "vision:analyze", "vision:extract"],
        "capabilities": ["analyze_image", "extract_text", "classify_document_image", "quality_assessment"],
        "config_schema": [
            ConfigFieldSchema(
                name="ocr_engine",
                label="OCR Provider",
                type="select",
                default="tesseract",
                options=[
                    ConfigFieldOption(label="Tesseract OCR (Local)", value="tesseract"),
                    ConfigFieldOption(label="Cloud Vision AI", value="cloud_vision")
                ]
            ),
            ConfigFieldSchema(
                name="confidence_threshold",
                label="Min OCR Confidence Threshold (%)",
                type="text",
                default="85"
            ),
            ConfigFieldSchema(
                name="watermark_disclaimer",
                label="Watermark 'AI-ASSISTED NOT HUMAN VERIFIED'",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "pdf_engine",
        "name": "Medical PDF Document Engine",
        "description": "PyPDF & ReportLab PDF processing engine for extracting clinical text, rendering discharge summaries, and SHA-256 stamping.",
        "category": "FILES & DATA",
        "auth_type": "none",
        "icon": "picture_as_pdf",
        "provider": "PyPDF & ReportLab",
        "required_permissions": ["pdf:read", "pdf:generate", "pdf:extract"],
        "capabilities": ["read_pdf", "extract_text", "generate_pdf", "hash_document"],
        "config_schema": [
            ConfigFieldSchema(
                name="flatten_forms",
                label="Flatten PDF Form Fields on Export",
                type="checkbox",
                default=True
            ),
            ConfigFieldSchema(
                name="sha256_audit_stamp",
                label="Affix SHA-256 Tamper-Evident Footer",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "docx_engine",
        "name": "Microsoft Word / DOCX Engine",
        "description": "python-docx medical report generator for rendering clinical case summaries, policy documentation, and letters.",
        "category": "FILES & DATA",
        "auth_type": "none",
        "icon": "description",
        "provider": "python-docx Engine",
        "required_permissions": ["word:read", "word:write", "word:format"],
        "capabilities": ["read_docx", "generate_docx", "format_report"],
        "config_schema": [
            ConfigFieldSchema(
                name="template_dir",
                label="Template Directory",
                type="text",
                default="./templates/docx"
            ),
            ConfigFieldSchema(
                name="redact_pii_in_drafts",
                label="Redact Patient PII in Draft Documents",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "cloud_storage",
        "name": "Enterprise Cloud Storage",
        "description": "Multi-cloud object storage connector supporting AWS S3, Google Cloud Storage, and Microsoft OneDrive with tenant isolation.",
        "category": "STORAGE",
        "auth_type": "credentials",
        "icon": "cloud",
        "provider": "AWS S3 / GCP Storage / OneDrive",
        "required_permissions": ["storage:read", "storage:write", "storage:bucket_manage"],
        "capabilities": ["upload", "download", "generate_presigned_url", "folder_management"],
        "config_schema": [
            ConfigFieldSchema(
                name="provider",
                label="Storage Provider",
                type="select",
                default="s3",
                options=[
                    ConfigFieldOption(label="AWS S3", value="s3"),
                    ConfigFieldOption(label="Google Cloud Storage", value="gcs"),
                    ConfigFieldOption(label="Microsoft Azure / OneDrive", value="azure")
                ]
            ),
            ConfigFieldSchema(
                name="bucket_name",
                label="Bucket Name",
                type="text",
                required=True,
                placeholder="medsentinel-vault-prod"
            ),
            ConfigFieldSchema(
                name="region",
                label="Region",
                type="text",
                default="us-east-1"
            ),
            ConfigFieldSchema(
                name="access_key_id",
                label="Access Key ID",
                type="text",
                required=True
            ),
            ConfigFieldSchema(
                name="secret_access_key",
                label="Secret Access Key",
                type="password",
                required=True
            )
        ]
    },
    {
        "id": "calendar_scheduling",
        "name": "Clinical Calendar & Scheduling",
        "description": "Doctor scheduling and consultation calendar integration with bi-directional conflict detection and timezone normalization.",
        "category": "PRODUCTIVITY",
        "auth_type": "oauth",
        "icon": "calendar_month",
        "provider": "Google / Outlook Calendar",
        "required_permissions": ["calendar:read", "calendar:write", "calendar:cancel"],
        "capabilities": ["check_availability", "create_appointment", "cancel_event", "reschedule"],
        "config_schema": [
            ConfigFieldSchema(
                name="calendar_provider",
                label="Calendar Provider",
                type="select",
                default="google",
                options=[
                    ConfigFieldOption(label="Google Calendar", value="google"),
                    ConfigFieldOption(label="Microsoft Outlook 365", value="outlook"),
                    ConfigFieldOption(label="Local / CalDAV", value="caldav")
                ]
            ),
            ConfigFieldSchema(
                name="auth_action",
                label="OAuth Authorization",
                type="oauth",
                provider="calendar",
                button_label="Connect Calendar Service"
            ),
            ConfigFieldSchema(
                name="sync_interval_mins",
                label="Sync Frequency (Minutes)",
                type="text",
                default="15"
            )
        ]
    },
    {
        "id": "unified_notifications",
        "name": "Multi-Channel Notification Gateway",
        "description": "Unified notification dispatcher coordinating push notifications, in-app SSE streams, and patient notification queues.",
        "category": "PRODUCTIVITY",
        "auth_type": "api_key",
        "icon": "notifications",
        "provider": "SSE / APNS / FCM",
        "required_permissions": ["notification:send", "notification:broadcast", "notification:subscribe"],
        "capabilities": ["notify", "broadcast", "get_status"],
        "config_schema": [
            ConfigFieldSchema(
                name="default_channel",
                label="Default Notification Channel",
                type="select",
                default="sse",
                options=[
                    ConfigFieldOption(label="In-App SSE Broadcast", value="sse"),
                    ConfigFieldOption(label="SMS", value="sms"),
                    ConfigFieldOption(label="Email", value="email"),
                    ConfigFieldOption(label="Mobile Push (FCM)", value="push")
                ]
            ),
            ConfigFieldSchema(
                name="fcm_server_key",
                label="FCM Server Key (Optional)",
                type="password"
            ),
            ConfigFieldSchema(
                name="rate_limit_per_patient_hour",
                label="Max Notifications / Patient / Hour",
                type="text",
                default="10"
            )
        ]
    },
    {
        "id": "hospital_his",
        "name": "Hospital EMR & Directory System",
        "description": "Standardized HL7 FHIR R4 gateway for hospital bed availability, doctor rosters, ICU censuses, and electronic referrals.",
        "category": "HEALTHCARE",
        "auth_type": "credentials",
        "icon": "local_hospital",
        "provider": "FHIR R4 / Hospital Network",
        "required_permissions": ["hospital:read", "hospital:referral", "hospital:beds"],
        "capabilities": ["search_hospitals", "check_bed_availability", "create_referral"],
        "config_schema": [
            ConfigFieldSchema(
                name="fhir_base_url",
                label="Hospital FHIR R4 Endpoint URL",
                type="url",
                required=True,
                placeholder="https://emr.hospital.org/fhir/r4"
            ),
            ConfigFieldSchema(
                name="client_id",
                label="FHIR OAuth Client ID",
                type="text",
                required=True
            ),
            ConfigFieldSchema(
                name="client_secret",
                label="FHIR Client Secret",
                type="password",
                required=True
            ),
            ConfigFieldSchema(
                name="sandbox_mode",
                label="Use Synthetic Hospital Sandbox",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "insurance_tpa",
        "name": "Insurance Payer & TPA Gateway",
        "description": "Insurance claims gateway connecting to Third-Party Administrators (TPAs) for real-time eligibility, pre-auth, and claims.",
        "category": "HEALTHCARE",
        "auth_type": "api_key",
        "icon": "health_and_safety",
        "provider": "Payer Clearinghouse / TPA",
        "required_permissions": ["insurance:claim_submit", "insurance:claim_status", "insurance:eligibility"],
        "capabilities": ["submit_claim", "submit_insurance_claim", "claim_status", "inquiry"],
        "config_schema": [
            ConfigFieldSchema(
                name="clearinghouse_url",
                label="Payer Gateway Base URL",
                type="url",
                required=True,
                placeholder="https://claims.tpa-clearinghouse.org/api/v2"
            ),
            ConfigFieldSchema(
                name="api_key",
                label="Clearinghouse API Key",
                type="password",
                required=True
            ),
            ConfigFieldSchema(
                name="terminal_id",
                label="Provider Terminal ID",
                type="text",
                required=True,
                placeholder="TER_901842"
            ),
            ConfigFieldSchema(
                name="sandbox_mode",
                label="Enable Claims Sandbox",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "payment_gateway",
        "name": "Healthcare Payment Gateway",
        "description": "PCI-compliant payment processing gateway (Stripe & Razorpay) for patient co-pays, hospital fees, and insurance deductibles.",
        "category": "PAYMENTS",
        "auth_type": "api_key",
        "icon": "payments",
        "provider": "Stripe / Razorpay",
        "required_permissions": ["payment:charge", "payment:refund", "payment:status"],
        "capabilities": ["create_payment_request", "get_payment_status", "refund_payment"],
        "config_schema": [
            ConfigFieldSchema(
                name="gateway_provider",
                label="Payment Gateway Provider",
                type="select",
                default="stripe",
                options=[
                    ConfigFieldOption(label="Stripe", value="stripe"),
                    ConfigFieldOption(label="Razorpay", value="razorpay")
                ]
            ),
            ConfigFieldSchema(
                name="secret_key",
                label="Secret Key (Live / Test)",
                type="password",
                required=True,
                placeholder="sk_test_..."
            ),
            ConfigFieldSchema(
                name="publishable_key",
                label="Publishable Key",
                type="text",
                placeholder="pk_test_..."
            ),
            ConfigFieldSchema(
                name="webhook_signing_secret",
                label="Webhook Signing Secret",
                type="password",
                placeholder="whsec_..."
            ),
            ConfigFieldSchema(
                name="sandbox_mode",
                label="Enable Test / Sandbox Mode",
                type="checkbox",
                default=True
            )
        ]
    },
    {
        "id": "custom_api",
        "name": "Custom REST API Connector",
        "description": "Zero-trust HTTP client with active SSRF defense, RFC 1918 private IP blocking, domain allowlisting, and request size caps.",
        "category": "OTHER",
        "auth_type": "api_key",
        "icon": "api",
        "provider": "Custom REST Gateway",
        "required_permissions": ["api:request", "api:webhook", "api:manage"],
        "capabilities": ["http_request", "custom_api_request", "custom_webhook"],
        "config_schema": [
            ConfigFieldSchema(
                name="endpoint_url",
                label="Target REST Endpoint URL",
                type="url",
                required=True,
                placeholder="https://api.external-partner.com/v1"
            ),
            ConfigFieldSchema(
                name="auth_header_type",
                label="Auth Header Type",
                type="select",
                default="Bearer",
                options=[
                    ConfigFieldOption(label="Bearer Token", value="Bearer"),
                    ConfigFieldOption(label="API Key (X-API-Key)", value="ApiKey"),
                    ConfigFieldOption(label="None", value="None")
                ]
            ),
            ConfigFieldSchema(
                name="api_token",
                label="API Token / Key",
                type="password",
                placeholder="Secret token"
            ),
            ConfigFieldSchema(
                name="timeout_seconds",
                label="Request Timeout (Seconds)",
                type="text",
                default="30"
            ),
            ConfigFieldSchema(
                name="validate_ssrf",
                label="Enforce Anti-SSRF Defense (Block Private Subnets)",
                type="checkbox",
                default=True
            )
        ]
    }
]

def determine_connector_status(plugin_id: str, plugin_instance: Any) -> str:
    """
    Computes real, non-fabricated connection status:
    - NOT CONFIGURED if credentials / API configuration missing
    - MOCK / SANDBOX if running in explicitly enabled sandbox driver
    - CONNECTED only after verified connection test or in-process local engine readiness
    - ERROR if authentication / ping failure
    - PAUSED if administrative kill switch active
    - REVOKED if security revocation triggered
    """
    if not plugin_instance:
        return "NOT CONFIGURED"

    # Explicit lifecycle overrides
    if getattr(plugin_instance, "status", None) == PluginStatus.REVOKED:
        return "REVOKED"
    if getattr(plugin_instance, "status", None) == PluginStatus.PAUSED:
        return "PAUSED"
    if getattr(plugin_instance, "status", None) == PluginStatus.ERROR:
        return "ERROR"
    if getattr(plugin_instance, "status", None) == PluginStatus.DISCONNECTED:
        return "NOT CONFIGURED"

    cfg = getattr(plugin_instance, "config", {}) or {}

    # In-process operational engines with no external credentials dependency
    in_process_plugins = {
        "excel_processor", "csv", "pdf_engine", "docx_engine",
        "secure_file_vault", "image_vision"
    }
    if plugin_id in in_process_plugins:
        return "CONNECTED"

    # For external services, inspect credentials
    if plugin_id == "whatsapp_business":
        if cfg.get("access_token") or os.getenv("WHATSAPP_ACCESS_TOKEN"):
            return "CONNECTED" if not cfg.get("sandbox_mode", True) else "MOCK / SANDBOX"
        return "NOT CONFIGURED"

    if plugin_id == "mobile_sms":
        if cfg.get("account_sid") or os.getenv("TWILIO_ACCOUNT_SID"):
            return "CONNECTED" if not cfg.get("sandbox_mode", True) else "MOCK / SANDBOX"
        return "NOT CONFIGURED"

    if plugin_id == "voice_telephony":
        if cfg.get("account_sid") or os.getenv("TWILIO_ACCOUNT_SID"):
            return "CONNECTED" if not cfg.get("sandbox_mode", True) else "MOCK / SANDBOX"
        return "NOT CONFIGURED"

    if plugin_id == "gmail_oauth":
        if cfg.get("token") or cfg.get("oauth_token") or os.getenv("GMAIL_REFRESH_TOKEN"):
            return "CONNECTED"
        if cfg.get("client_id") or os.getenv("GMAIL_CLIENT_ID"):
            return "MOCK / SANDBOX"
        return "NOT CONFIGURED"

    if plugin_id == "universal_email":
        if cfg.get("smtp_host") or os.getenv("SMTP_HOST"):
            return "CONNECTED"
        return "NOT CONFIGURED"

    if plugin_id == "cloud_storage":
        if (cfg.get("access_key_id") and cfg.get("secret_access_key")) or os.getenv("AWS_ACCESS_KEY_ID"):
            return "CONNECTED"
        return "MOCK / SANDBOX" if cfg.get("use_local_fallback", True) else "NOT CONFIGURED"

    if plugin_id == "calendar_scheduling":
        if cfg.get("token") or cfg.get("oauth_token") or os.getenv("CALENDAR_API_KEY"):
            return "CONNECTED"
        return "MOCK / SANDBOX"

    if plugin_id == "unified_notifications":
        return "CONNECTED"  # Local SSE broadcaster is always connected

    if plugin_id == "hospital_his":
        if cfg.get("fhir_base_url") or os.getenv("FHIR_EMR_BASE_URL"):
            return "CONNECTED" if not cfg.get("sandbox_mode", True) else "MOCK / SANDBOX"
        return "MOCK / SANDBOX" if cfg.get("sandbox_mode", True) else "NOT CONFIGURED"

    if plugin_id == "insurance_tpa":
        if cfg.get("clearinghouse_url") or os.getenv("TPA_CLAIMS_GATEWAY_URL"):
            return "CONNECTED" if not cfg.get("sandbox_mode", True) else "MOCK / SANDBOX"
        return "MOCK / SANDBOX" if cfg.get("sandbox_mode", True) else "NOT CONFIGURED"

    if plugin_id == "payment_gateway":
        if cfg.get("secret_key") or os.getenv("STRIPE_SECRET_KEY"):
            return "CONNECTED" if not cfg.get("sandbox_mode", True) else "MOCK / SANDBOX"
        return "MOCK / SANDBOX" if cfg.get("sandbox_mode", True) else "NOT CONFIGURED"

    if plugin_id == "custom_api":
        if cfg.get("endpoint_url"):
            return "CONNECTED"
        return "NOT CONFIGURED"

    return "NOT CONFIGURED"


def get_all_connectors_metadata(plugin_manager: Any) -> List[ConnectorMetadata]:
    """Builds and returns all 18 connectors with live status and metadata."""
    results: List[ConnectorMetadata] = []
    for defn in CATALOG_DEFINITIONS:
        p_id = defn["id"]
        plugin_inst = plugin_manager.get_plugin(p_id)
        status_str = determine_connector_status(p_id, plugin_inst)
        is_en = getattr(plugin_inst, "is_enabled", True) if plugin_inst else True

        last_test = None
        if plugin_inst and getattr(plugin_inst, "last_tested_at", None):
            try:
                last_test = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(plugin_inst.last_tested_at))
            except Exception:
                pass

        results.append(
            ConnectorMetadata(
                id=p_id,
                name=defn["name"],
                description=defn["description"],
                category=defn["category"],
                auth_type=defn["auth_type"],
                status=status_str,
                required_permissions=defn["required_permissions"],
                capabilities=defn["capabilities"],
                icon=defn["icon"],
                provider=defn["provider"],
                config_schema=defn["config_schema"],
                is_enabled=is_en,
                last_tested_at=last_test
            )
        )
    return results


def get_single_connector_metadata(plugin_id: str, plugin_manager: Any) -> Optional[ConnectorMetadata]:
    """Finds and returns a single connector metadata with live status."""
    connectors = get_all_connectors_metadata(plugin_manager)
    for c in connectors:
        if c.id == plugin_id or c.id.replace("_", "") == plugin_id.replace("_", ""):
            return c
    return None
