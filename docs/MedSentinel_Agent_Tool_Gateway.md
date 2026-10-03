# MedSentinel — Agent Tool Gateway & Decision Engine

## 1. Overview

The **Tool Gateway** is the single entry point through which all 9 MedSentinel AI agents interact with the external world. Autonomous agents are completely isolated from raw network sockets and external HTTP clients.

```text
    AI Agent
       │
       ▼
┌──────────────┐
│ Tool Request │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│                   TOOL GATEWAY                         │
│                                                        │
│  1. Check Global / Plugin Kill Switch                  │
│  2. Authenticate User JWT & RBAC Role                  │
│  3. Validate Resource Ownership & Patient Consent      │
│  4. Verify Plugin Active State & Rate Limits           │
│  5. Redact PII (Mask Phone, Email, Credentials)       │
│  6. Evaluate Policy Engine Risk Tier                   │
│                                                        │
│       ┌─────────────┴─────────────┐                    │
│       ▼                           ▼                    │
│   [LOW Risk]                 [HIGH Risk]               │
│   Autonomous                 Enqueue in Approval Queue │
│   Dispatch                   Awaiting Admin Action     │
│       │                           │                    │
│       └─────────────┬─────────────┘                    │
│                     │                                  │
│  7. Dispatch through Plugin Driver                     │
│  8. Verification Agent Confirms Delivery ID            │
│  9. Record Tamper-Evident Entry in PluginActionAudit   │
└─────────────────────┬──────────────────────────────────┘
                      │
                      ▼
              Verified Tool Result
```

---

## 2. Universal Tool Schemas

### ToolRequest
```json
{
  "workflow_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "user_id": 42,
  "agent_id": "PatientCommunicationAgent",
  "tool_name": "send_whatsapp_message",
  "resource_id": "CLM-9012",
  "parameters": {
    "phone": "+91 9876543210",
    "message": "Your claim CLM-9012 has been pre-authorized."
  },
  "permission": "whatsapp:send",
  "risk_level": "MEDIUM",
  "approval_required": false,
  "idempotency_key": "wa_tx_9823719"
}
```

### ToolResult
```json
{
  "success": true,
  "status": "SUCCESS",
  "result": {
    "message_id": "wamid.HBgLMzkxOTg3NjU0MzIxMBUC",
    "delivery_status": "QUEUED"
  },
  "external_id": "wamid.HBgLMzkxOTg3NjU0MzIxMBUC",
  "error": null,
  "verification_status": "VERIFIED",
  "audit_id": 1042,
  "execution_time_ms": 38
}
```

---

## 3. Decision Engine & Intent Resolution

The `DecisionEngine` intercepts natural language agent plans and compiles them into structured `ToolRequest` specifications:

```python
class DecisionEngine:
    async def evaluate_intent(self, intent: str, context: Dict[str, Any]) -> ToolRequest:
        ...
```

### Risk Matrix & Human Review Rules

| Action Type | Examples | Risk Tier | Approval Rule |
|---|---|---|---|
| **Data Cleaning & Reports** | `clean_csv`, `format_excel`, `create_draft` | **LOW** | Autonomous |
| **Document Previews** | `preview_file`, `ocr_image`, `generate_pdf` | **LOW** | Autonomous |
| **Patient Communications** | `send_sms`, `send_whatsapp_message`, `send_email` | **MEDIUM** | Governed by Configured Policy |
| **Clinical Scheduling** | `create_appointment`, `cancel_event` | **MEDIUM** | Conflict & Double-Booking Check |
| **Financial Operations** | `refund_payment`, `create_payment_request` | **HIGH** | **Mandatory Admin Approval** |
| **Insurance Actions** | `submit_claim`, `settle_claim` | **HIGH** | **Mandatory Admin Approval** |
| **Clinical Treatment Decisions** | Prescriptions, Diagnostic Confirmation | **CRITICAL** | **Doctor Verification Mandatory** |
