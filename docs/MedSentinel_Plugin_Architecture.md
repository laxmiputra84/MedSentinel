# MedSentinel — Enterprise Plugin & Connector Architecture

## 1. Executive Summary

MedSentinel delivers a centralized, zero-trust **Plugin & Integration Hub** that decouples autonomous AI decision-making from external service execution. External integrations (WhatsApp Business, SMS, Voice, Gmail, Enterprise Email, Excel, CSV, PDF, Word, Images, Cloud Storage, Calendar, Hospital Systems, Insurance TPAs, Payment Gateways, and Custom REST APIs) are strictly governed by a unified **Tool Gateway**, an application-side **Policy Engine**, and a **Human-in-the-Loop Approval Gate**.

Under no circumstances can an LLM directly invoke an arbitrary third-party API.

---

## 2. Architectural Blueprint

```text
                                MEDSENTINEL WEB APPLICATION
                                             │
                                   ┌─────────▼─────────┐
                                   │    Web Control    │  (/admin/plugins)
                                   │      Center       │
                                   └─────────┬─────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │   Authentication  │  (JWT + RBAC + Tenant)
                                   │    & Permissions  │
                                   └─────────┬─────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │ Agent Orchestrator│
                                   └─────────┬─────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │  Decision Engine  │
                                   └─────────┬─────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │   Tool Gateway    │
                                   └─────────┬─────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │   Policy Engine   │  (LOW, MEDIUM, HIGH, CRITICAL)
                                   └─────────┬─────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             [Approval Gate] (Human-in-Loop)             [Autonomous Execution]
             (Claims, Payments, Clinical)                (Reports, Previews, Scans)
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │  Plugin Manager   │
                                   └─────────┬─────────┘
                                             │
         ┌────────────┬────────────┬─────────┴──────────┬────────────┬────────────┐
         ▼            ▼            ▼                    ▼            ▼            ▼
      WhatsApp       SMS         Voice                Gmail        Email        Files
         │            │            │                    │            │            │
         ▼            ▼            ▼                    ▼            ▼            ▼
       Excel         CSV         Images                PDF          Word       Storage
         │            │            │                    │            │            │
         ▼            ▼            ▼                    ▼            ▼            ▼
      Calendar    Hospital     Insurance             Payment     Custom API  Internal
         │            │            │                    │            │            │
         └────────────┴────────────┴─────────┬──────────┴────────────┴────────────┘
                                             ▼
                                    EXTERNAL SERVICES
                                             │
                                   ┌─────────▼─────────┐
                                   │Verification Agent │  (Idempotency, Receipts)
                                   └─────────┬─────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │  Audit & Security │  (Tamper-Evident Ledger)
                                   └───────────────────┘
```

---

## 3. Plugin Lifecycle State Machine

Each plugin transition follows an audited lifecycle:

```text
                  ┌────────────────────────┐
                  │     NOT_CONFIGURED     │
                  └───────────┬────────────┘
                              │ Configure Credentials / Keys
                              ▼
                  ┌────────────────────────┐
                  │       CONNECTING       │
                  └───────────┬────────────┘
                              │ Synthetic Ping & OAuth Verify
               ┌──────────────┴──────────────┐
               ▼                             ▼
   ┌───────────────────────┐     ┌───────────────────────┐
   │         ERROR         │     │       CONNECTED       │
   └───────────────────────┘     └───────────┬───────────┘
                                             │ Admin Enable / Disable
                                 ┌───────────┴───────────┐
                                 ▼                       ▼
                     ┌───────────────────────┐ ┌───────────────────────┐
                     │        ENABLED        │ │       DISABLED        │
                     └───────────┬───────────┘ └───────────────────────┘
                                 │ Kill Switch / Security Event
                                 ▼
                     ┌───────────────────────┐
                     │        PAUSED         │
                     └───────────────────────┘
                                 │ Admin Revoke Action
                                 ▼
                     ┌───────────────────────┐
                     │        REVOKED        │
                     └───────────────────────┘
```

---

## 4. The 18 Concrete Plugin Connectors

| # | Plugin ID | Provider | Category | Primary Capabilities | Risk Tier |
|---|---|---|---|---|---|
| 1 | `whatsapp_business` | Meta Cloud API | Communication | `send_whatsapp_message`, `send_template`, `request_document` | MEDIUM |
| 2 | `mobile_sms` | Twilio / Enterprise SMS | Communication | `send_sms`, `send_otp`, `verify_otp` | MEDIUM |
| 3 | `voice_telephony` | Telephony Provider | Communication | `incoming_call_events`, `transcription`, `call_summary` | MEDIUM |
| 4 | `gmail_oauth` | Google Workspace | Email | `search_email`, `read_email`, `create_draft` | LOW |
| 5 | `universal_email` | SMTP / SendGrid / Exchange | Email | `send`, `receive`, `create_draft`, `verify_delivery` | MEDIUM |
| 6 | `secure_file_vault` | MedSentinel Vault | Files & Storage | `upload`, `download`, `calculate_hash`, `scan_security` | LOW |
| 7 | `excel_processor` | Native Openpyxl / CSV | Files & Data | `read_excel`, `clean_excel`, `detect_duplicates` | LOW |
| 8 | `csv` | CSV Intelligence Engine | Files & Data | `parse_csv`, `validate_csv`, `deduplicate_csv`, `export_csv` | LOW |
| 9 | `image_vision` | Tesseract / Vision Engine | Files & Data | `analyze_image`, `extract_text`, `quality_assessment` | LOW |
| 10 | `pdf_engine` | ReportLab / PyPDF | Files & Data | `extract_text`, `generate_pdf`, `hash_document` | LOW |
| 11 | `document_word` | Python-Docx Engine | Files & Data | `read_docx`, `generate_docx`, `format_report` | LOW |
| 12 | `cloud_storage` | AWS S3 / Google Drive / OneDrive | Storage | `upload`, `download`, `folder_management` | LOW |
| 13 | `calendar_scheduling` | Google / CalDAV / Exchange | Productivity | `check_availability`, `create_appointment`, `cancel_event` | MEDIUM |
| 14 | `notification_service` | Multi-Channel Broadcast | Productivity | `notify(channel, recipient, message, priority)` | MEDIUM |
| 15 | `hospital_network` | EMR / HIS FHIR Gateway | Healthcare | `search_hospitals`, `check_bed_availability`, `referral` | LOW |
| 16 | `insurance_tpa` | Payer FHIR Gateway | Healthcare | `submit_claim`, `claim_status`, `inquiry` | HIGH |
| 17 | `payment_gateway` | Stripe / Razorpay | Payments | `payment_request`, `payment_status`, `refund_payment` | HIGH |
| 18 | `custom_api` | Custom REST Gateway | Other | `http_request`, `custom_webhook` (SSRF Protected) | MEDIUM |

---

## 5. Zero-Trust Tool Gateway Protocol

Every autonomous action flows through `ToolGateway.execute_tool(...)`:
1. **Kill Switch Evaluation:** Verifies global kill switch, agent pause, plugin pause, and outbound scope.
2. **Authentication & RBAC Check:** Validates JWT claims and role boundaries (`super_admin`, `admin`, `doctor`, `staff`, `patient`).
3. **Capability & Scope Authorization:** Checks if the target plugin allows the requested scope.
4. **Rate Limiting:** Enforces sliding-window limits per plugin connector.
5. **PII Redaction:** Automatically masks phone numbers (`+91 ******1234`), emails (`l****@domain.com`), and credentials (`[REDACTED]`).
6. **Policy Engine Risk Tiering:**
   - `LOW`: Autonomous execution permitted.
   - `MEDIUM`: Autonomous execution governed by administrator policies.
   - `HIGH`: Enqueued in `PluginApprovalRequest` awaiting human review.
   - `CRITICAL`: Absolute human verification mandatory; automated execution prohibited.
7. **Execution & Idempotency:** Plugin executes through isolated provider driver.
8. **Verification:** `VerificationReportAgent` confirms delivery receipt and transaction ID.
9. **Tamper-Evident Audit:** Record committed to `PluginActionAudit` with microsecond latency and verification state.
