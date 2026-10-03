import pytest
import asyncio
from app.plugins import (
    plugin_manager,
    emergency_controller,
    decision_engine,
    ToolRequest,
    ToolResult,
    BasePlugin,
    PolicyEngine,
)
from app.models.plugin import ActionRiskLevel, PluginStatus

@pytest.mark.asyncio
async def test_all_16_plugins_registered():
    plugins = plugin_manager.get_all_plugins()
    assert len(plugins) >= 16
    plugin_ids = {p.plugin_id for p in plugins}
    expected_ids = {
        "whatsapp_business", "mobile_sms", "voice_telephony", "gmail_oauth",
        "universal_email", "secure_file_vault", "excel_processor", "image_vision",
        "pdf_engine", "docx_engine", "cloud_storage", "calendar_scheduling",
        "unified_notifications", "payment_gateway", "hospital_his", "insurance_tpa"
    }
    assert expected_ids.issubset(plugin_ids)

@pytest.mark.asyncio
async def test_low_risk_tool_execution():
    # Excel duplicate detection
    req = ToolRequest(
        agent_id="LabAnalysisAgent",
        tool_name="detect_duplicates",
        parameters={"data": [{"test": "Glucose", "value": 110}]}
    )
    res = await plugin_manager.execute_tool(req)
    assert res.success is True
    assert res.status == "SUCCESS"
    assert res.verification_status == "VERIFIED"
    assert res.result["duplicate_records_found"] == 0

@pytest.mark.asyncio
async def test_phone_masking_and_sms():
    req = ToolRequest(
        agent_id="PatientCommunicationAgent",
        tool_name="send_sms",
        parameters={"phone": "+91 9876543210", "message": "Appointment scheduled"}
    )
    res = await plugin_manager.execute_tool(req)
    assert res.success is True
    assert res.result["recipient"] == "+91 ******3210"
    assert "9876543210" not in res.result["recipient"]

@pytest.mark.asyncio
async def test_whatsapp_message_and_tracking():
    req = ToolRequest(
        agent_id="PatientCommunicationAgent",
        tool_name="send_whatsapp_message",
        parameters={"phone": "+91 9123456789", "message": "Claim approved"}
    )
    res = await plugin_manager.execute_tool(req)
    assert res.success is True
    assert res.result["delivery_status"] == "SENT_TO_GATEWAY"
    assert res.result["recipient"] == "+91 ******6789"
    assert res.result["channel"] == "WhatsApp Business"

@pytest.mark.asyncio
async def test_high_risk_claim_approval_gate():
    # High risk action must trigger human approval gate
    req = ToolRequest(
        agent_id="InsuranceAgent",
        tool_name="submit_insurance_claim",
        parameters={"policy_number": "POL-1004", "claim_amount": 80000.0}
    )
    res = await plugin_manager.execute_tool(req)
    assert res.success is False
    assert res.status == "PENDING_APPROVAL"
    assert res.result["gate"] == "HUMAN_IN_THE_LOOP"
    assert res.result["risk_level"] == "HIGH"

@pytest.mark.asyncio
async def test_emergency_kill_switch():
    req = ToolRequest(
        agent_id="DocumentIntelligenceAgent",
        tool_name="read_pdf",
        parameters={"filename": "lab.pdf"}
    )
    
    # 1. Normal execution
    res1 = await plugin_manager.execute_tool(req)
    assert res1.success is True

    # 2. Trip global kill switch
    emergency_controller.set_global_pause(True, "Emergency audit in progress")
    res2 = await plugin_manager.execute_tool(req)
    assert res2.success is False
    assert res2.status == "PAUSED"
    assert "EMERGENCY KILL SWITCH ACTIVE" in res2.error

    # 3. Reset kill switch
    emergency_controller.set_global_pause(False)
    res3 = await plugin_manager.execute_tool(req)
    assert res3.success is True

@pytest.mark.asyncio
async def test_target_plugin_kill_switch():
    emergency_controller.set_plugin_pause("payment_gateway", True, "Payment provider maintenance")
    req = ToolRequest(
        agent_id="BillingAgent",
        tool_name="get_payment_status",
        parameters={"transaction_id": "tx_123"}
    )
    res = await plugin_manager.execute_tool(req)
    assert res.success is False
    assert res.status == "PAUSED"
    assert "payment_gateway" in res.error

    emergency_controller.set_plugin_pause("payment_gateway", False)

@pytest.mark.asyncio
async def test_secure_file_path_traversal_protection():
    req = ToolRequest(
        agent_id="DocumentAgent",
        tool_name="upload",
        parameters={"filename": "../../etc/passwd", "content": "test"}
    )
    res = await plugin_manager.execute_tool(req)
    assert res.success is True
    # Verify traversal was stripped to basename
    assert res.result["filename"] == "passwd"

@pytest.mark.asyncio
async def test_decision_engine_intent_routing():
    res = await decision_engine.route_intent(
        intent="Check hospital bed availability in Cardiology",
        parameters={"hospital_id": "HOSP_001", "specialty": "Cardiology"},
        agent_id="HospitalMatchingAgent"
    )
    assert res.success is True
    assert res.result["specialty"] == "Cardiology"
    assert res.result["available_beds"] > 0

@pytest.mark.asyncio
async def test_calendar_availability_and_conflict_detection():
    req = ToolRequest(
        agent_id="PatientIntakeAgent",
        tool_name="check_availability",
        parameters={"doctor_id": "DR_CARDIO_1", "appointment_time": "2026-09-20T10:00:00Z"}
    )
    res = await plugin_manager.execute_tool(req)
    assert res.success is True
    assert len(res.result["available_slots"]) > 0
    assert res.result["conflicts_detected"] == 0

@pytest.mark.asyncio
async def test_payment_zero_secret_exposure():
    req = ToolRequest(
        agent_id="FinanceAgent",
        tool_name="create_payment_request",
        parameters={"amount": 2500.0, "currency": "INR", "secret_card_key": "raw_12345"},
        approval_required=False # simulate approved
    )
    res = await plugin_manager.execute_tool(req)
    assert res.success is True
    assert "raw_12345" not in str(res.result)
    assert "tokenized session" in res.result["security"]

@pytest.mark.asyncio
async def test_connector_catalog_and_categories():
    from app.plugins.connector_catalog import get_all_connectors_metadata
    connectors = get_all_connectors_metadata(plugin_manager)
    assert len(connectors) == 18

    cat_map = {}
    for c in connectors:
        cat_map.setdefault(c.category, []).append(c.id)

    # 1. COMMUNICATION: Gmail, WhatsApp Business, SMS / Mobile, Voice, Email
    assert "COMMUNICATION" in cat_map
    comm_ids = set(cat_map["COMMUNICATION"])
    assert {"gmail_oauth", "whatsapp_business", "mobile_sms", "voice_telephony", "universal_email"}.issubset(comm_ids)

    # 2. FILES & DATA: Secure File, Excel, CSV, Image / OCR, PDF, Document
    assert "FILES & DATA" in cat_map
    files_ids = set(cat_map["FILES & DATA"])
    assert {"secure_file_vault", "excel_processor", "csv", "image_vision", "pdf_engine", "docx_engine"}.issubset(files_ids)

    # 3. STORAGE: Cloud Storage
    assert "STORAGE" in cat_map
    assert "cloud_storage" in cat_map["STORAGE"]

    # 4. PRODUCTIVITY: Calendar, Notification
    assert "PRODUCTIVITY" in cat_map
    assert {"calendar_scheduling", "unified_notifications"}.issubset(set(cat_map["PRODUCTIVITY"]))

    # 5. HEALTHCARE: Hospital, Insurance
    assert "HEALTHCARE" in cat_map
    assert {"hospital_his", "insurance_tpa"}.issubset(set(cat_map["HEALTHCARE"]))

    # 6. PAYMENTS: Payment Gateway
    assert "PAYMENTS" in cat_map
    assert "payment_gateway" in cat_map["PAYMENTS"]

    # 7. OTHER: Custom API
    assert "OTHER" in cat_map
    assert "custom_api" in cat_map["OTHER"]

@pytest.mark.asyncio
async def test_dynamic_connector_config_schemas():
    from app.plugins.connector_catalog import get_single_connector_metadata
    gmail = get_single_connector_metadata("gmail_oauth", plugin_manager)
    assert gmail is not None
    assert gmail.auth_type == "oauth"
    assert any(f.type == "oauth" for f in gmail.config_schema)

    whatsapp = get_single_connector_metadata("whatsapp_business", plugin_manager)
    assert whatsapp is not None
    assert whatsapp.auth_type == "api_key"
    assert any(f.name == "access_token" and f.type == "password" for f in whatsapp.config_schema)

    custom_api = get_single_connector_metadata("custom_api", plugin_manager)
    assert custom_api is not None
    assert any(f.name == "endpoint_url" and f.type == "url" for f in custom_api.config_schema)

