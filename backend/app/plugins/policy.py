from typing import Tuple, Dict
from app.models.plugin import ActionRiskLevel
from app.plugins.schema import ToolRequest

class PolicyEngine:
    """
    Zero-Trust Policy & Risk Evaluation Engine.
    Evaluates every agent tool invocation against deterministic risk profiles
    and determines whether human approval is mandatory prior to execution.
    """

    DEFAULT_ACTION_RISK: Dict[str, ActionRiskLevel] = {
        # LOW RISK (Immediate automated execution, no human approval needed)
        "create_report": ActionRiskLevel.LOW,
        "format_excel": ActionRiskLevel.LOW,
        "read_spreadsheet": ActionRiskLevel.LOW,
        "clean_tabular_data": ActionRiskLevel.LOW,
        "create_email_draft": ActionRiskLevel.LOW,
        "read_email": ActionRiskLevel.LOW,
        "search_emails": ActionRiskLevel.LOW,
        "get_attachments": ActionRiskLevel.LOW,
        "classify_email_thread": ActionRiskLevel.LOW,
        "read_pdf": ActionRiskLevel.LOW,
        "extract_text": ActionRiskLevel.LOW,
        "split_pdf": ActionRiskLevel.LOW,
        "merge_pdf": ActionRiskLevel.LOW,
        "generate_pdf": ActionRiskLevel.LOW,
        "verify_pdf_signature": ActionRiskLevel.LOW,
        "generate_docx": ActionRiskLevel.LOW,
        "read_docx": ActionRiskLevel.LOW,
        "generate_claim_summary": ActionRiskLevel.LOW,
        "generate_patient_letter": ActionRiskLevel.LOW,
        "ocr_image": ActionRiskLevel.LOW,
        "classify_medical_image": ActionRiskLevel.LOW,
        "extract_metadata": ActionRiskLevel.LOW,
        "check_resolution_quality": ActionRiskLevel.LOW,
        "sanitize_scan": ActionRiskLevel.LOW,
        "search_hospitals": ActionRiskLevel.LOW,
        "get_hospital_details": ActionRiskLevel.LOW,
        "get_doctor_directory": ActionRiskLevel.LOW,
        "check_bed_availability": ActionRiskLevel.LOW,
        "check_availability": ActionRiskLevel.LOW,
        "detect_conflicts": ActionRiskLevel.LOW,
        "verify_policy_eligibility": ActionRiskLevel.LOW,
        "get_claim_adjudication_status": ActionRiskLevel.LOW,
        "get_payment_status": ActionRiskLevel.LOW,
        "verify_transaction": ActionRiskLevel.LOW,
        "generate_receipt": ActionRiskLevel.LOW,
        "preview": ActionRiskLevel.LOW,
        "download": ActionRiskLevel.LOW,
        "download_from_cloud": ActionRiskLevel.LOW,
        "search_scoped_folder": ActionRiskLevel.LOW,
        "calculate_hash": ActionRiskLevel.LOW,
        "detect_duplicates": ActionRiskLevel.LOW,
        "get_call_status": ActionRiskLevel.LOW,
        "transcribe_audio": ActionRiskLevel.LOW,
        "track_delivery_status": ActionRiskLevel.LOW,
        "verify_otp": ActionRiskLevel.LOW,
        "get_notification_status": ActionRiskLevel.LOW,

        # MEDIUM RISK (Configurable approval gate / sensitive communications)
        "send_message": ActionRiskLevel.MEDIUM,
        "send_whatsapp_message": ActionRiskLevel.MEDIUM,
        "send_template": ActionRiskLevel.MEDIUM,
        "request_document": ActionRiskLevel.MEDIUM,
        "send_claim_status": ActionRiskLevel.MEDIUM,
        "send_appointment_reminder": ActionRiskLevel.MEDIUM,
        "send_sms": ActionRiskLevel.MEDIUM,
        "send_otp": ActionRiskLevel.MEDIUM,
        "send_claim_alert": ActionRiskLevel.MEDIUM,
        "appointment_reminder": ActionRiskLevel.MEDIUM,
        "send": ActionRiskLevel.MEDIUM,
        "send_approved_email": ActionRiskLevel.MEDIUM,
        "notify": ActionRiskLevel.MEDIUM,
        "route_by_urgency": ActionRiskLevel.MEDIUM,
        "broadcast_alert": ActionRiskLevel.MEDIUM,
        "create_appointment": ActionRiskLevel.MEDIUM,
        "update_appointment": ActionRiskLevel.MEDIUM,
        "cancel_appointment": ActionRiskLevel.MEDIUM,
        "send_calendar_invite": ActionRiskLevel.MEDIUM,
        "upload": ActionRiskLevel.MEDIUM,
        "upload_to_cloud": ActionRiskLevel.MEDIUM,
        "upload_claim_documents": ActionRiskLevel.MEDIUM,
        "create_presigned_url": ActionRiskLevel.MEDIUM,
        "rename": ActionRiskLevel.MEDIUM,
        "move": ActionRiskLevel.MEDIUM,
        "copy": ActionRiskLevel.MEDIUM,
        "version": ActionRiskLevel.MEDIUM,
        "write_spreadsheet": ActionRiskLevel.MEDIUM,
        "generate_report": ActionRiskLevel.MEDIUM,
        "initiate_call": ActionRiskLevel.MEDIUM,
        "escalate_to_human": ActionRiskLevel.MEDIUM,

        # HIGH RISK (Mandatory Human Authorization Required)
        "submit_claim": ActionRiskLevel.HIGH,
        "submit_insurance_claim": ActionRiskLevel.HIGH,
        "request_pre_authorization": ActionRiskLevel.HIGH,
        "approve_claim": ActionRiskLevel.HIGH,
        "reject_claim": ActionRiskLevel.HIGH,
        "medical_decision": ActionRiskLevel.HIGH,
        "create_payment_request": ActionRiskLevel.HIGH,
        "process_payment": ActionRiskLevel.HIGH,
        "initiate_refund": ActionRiskLevel.HIGH,
        "refund_payment": ActionRiskLevel.HIGH,
        "delete": ActionRiskLevel.HIGH,
        "delete_file": ActionRiskLevel.HIGH,
        "create_patient_referral": ActionRiskLevel.HIGH,
        "request_emergency_bed": ActionRiskLevel.HIGH,

        # CRITICAL RISK
        "emergency_kill_switch": ActionRiskLevel.CRITICAL,
        "revoke_plugin_credentials": ActionRiskLevel.CRITICAL,
        "purge_records": ActionRiskLevel.CRITICAL,
    }


    def __init__(self, strict_medium_approval: bool = False):
        self.strict_medium_approval = strict_medium_approval

    def evaluate(self, request: ToolRequest) -> Tuple[bool, ActionRiskLevel, bool, str]:
        """
        Returns:
            allowed (bool): Whether the action is permitted by policy.
            risk_level (ActionRiskLevel): Determined risk classification.
            approval_required (bool): Whether human authorization is required.
            reason (str): Justification text for audit trail.
        """
        action_name = request.tool_name.lower().strip()
        
        # 1. Determine risk tier
        if request.risk_level:
            risk_level = request.risk_level
        else:
            risk_level = self.DEFAULT_ACTION_RISK.get(action_name, ActionRiskLevel.MEDIUM)

        # 2. Check if approval is explicitly forced in request
        if request.approval_required is not None:
            approval_required = request.approval_required
        elif risk_level in [ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL]:
            approval_required = True
        elif risk_level == ActionRiskLevel.MEDIUM and self.strict_medium_approval:
            approval_required = True
        else:
            approval_required = False

        reason = f"Policy evaluated: {action_name} classified as {risk_level.value}. " \
                 f"Human approval required: {approval_required}."

        return True, risk_level, approval_required, reason
