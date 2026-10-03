# MedSentinel — Provider Integration & Setup Guide

This guide details how administrators configure and connect external services into MedSentinel's Plugin Hub.

---

## 1. WhatsApp Business Cloud API Integration

### Requirements
- Meta for Developers account with registered Business App
- WhatsApp Business Account (WABA) ID
- Phone Number ID and System User Access Token
- Webhook Secret and Verify Token

### Setup Steps
1. Navigate to **Meta Developer Console** → Your App → WhatsApp → API Setup.
2. Generate a Permanent System User Token with permissions: `whatsapp_business_messaging`, `whatsapp_business_management`.
3. In MedSentinel Control Center (`/admin/plugins`):
   - Click **+ ADD CONNECTOR** → Select **WhatsApp Business**.
   - Input your **Phone Number ID** and **Access Token**.
   - Save configuration.
4. Configure Webhook in Meta Console:
   - Callback URL: `https://your-domain.com/api/webhooks/whatsapp`
   - Verify Token: Matches `WHATSAPP_VERIFY_TOKEN` in `.env`
   - Subscriptions: `messages`, `message_template_status_update`.

---

## 2. Mobile SMS & OTP Gateway (Twilio)

### Requirements
- Twilio Account SID, Auth Token, and Sender Phone Number.

### Setup Steps
1. In MedSentinel Control Center (`/admin/plugins`):
   - Select **Mobile / SMS Gateway** → Click **Manage / Connect**.
   - Input your Twilio Account SID and Auth Token.
   - Configure Sender Number: e.g., `+1234567890`.
2. Configure Status Callback URL in Twilio Console:
   - Webhook URL: `https://your-domain.com/api/webhooks/sms`
   - HTTP Method: `POST`.
3. Click **Test Ping** in MedSentinel to dispatch a synthetic OTP verification.

---

## 3. Telephony / Voice Gateway

### Requirements
- Approved Telephony Provider (Twilio Voice, Exotel, or Vonage)
- TwiML Application or Webhook Endpoint

### Setup Steps
1. Configure Voice Webhook URL: `https://your-domain.com/api/webhooks/voice`.
2. Incoming calls trigger automated patient identity verification and appointment lookup.
3. High-risk medical questions are automatically routed to human staff with full audio transcription.

---

## 4. Gmail OAuth 2.0 Integration

### Principles
- Zero plaintext password storage.
- Least-privilege OAuth scopes:
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/gmail.send`
  - `https://www.googleapis.com/auth/gmail.compose`

### Setup Steps
1. In Google Cloud Console, create OAuth 2.0 Credentials:
   - Application Type: Web Application
   - Authorized Redirect URI: `http://localhost:3000/api/auth/callback/google`
2. Configure `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` in `.env`.
3. In Plugin Hub, click **Connect Gmail** to authorize access.
4. The `EmailIntelligenceAgent` automatically triages inbound claim and lab emails.

---

## 5. Cloud Storage (AWS S3 / MinIO)

### Requirements
- AWS Access Key, Secret Key, Region, and S3 Bucket Name.
- S3 Bucket with server-side encryption (`AES-256` / `aws:kms`) enabled.

### Setup Steps
1. In MedSentinel Control Center:
   - Select **Cloud Storage** → **Configure**.
   - Specify Bucket: `medsentinel-encrypted-vault-prod`.
2. Access is scoped strictly to patient-specific directory prefixes: `tenants/{tenant_id}/patients/{patient_id}/`.
3. Root account browsing by AI agents is strictly prohibited by Tool Gateway policy.

---

## 6. Hospital Systems (FHIR R4 / HL7)

### Requirements
- Hospital EMR FHIR endpoint base URL and OAuth client credentials.

### Capabilities
- `search_hospitals`: Real-time hospital bed and doctor availability.
- `check_bed_availability`: ICU and general ward census query.
- `create_referral`: Standard FHIR ServiceRequest creation with doctor signature.

---

## 7. Insurance TPA & Claims Gateway

### Policy & Controls
- **Mandatory Human-in-the-Loop Authorization:** All claim submissions (`submit_claim`) and settlement requests require human authorization in the **Pending Approvals Gate**.
- Payload contains diagnosis codes (ICD-10), procedure codes (CPT), and cryptographic document fingerprints.

---

## 8. Custom REST API Connector (SSRF Protected)

### Security Features
- Prohibits internal IP addresses: `127.0.0.1`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`.
- Hostname allowlist: only approved domains (e.g. `.gov`, `.org`, `.health`, `.ai`).
- Strict 30s timeout and 5MB payload caps.

---

## 9. Implementation & Readiness Classification Matrix

To ensure absolute transparency between internal code readiness and third-party credential dependencies, all connectors are categorized across four strict operational states:

| Plugin ID | Architecture Category | Code Implementation Status | External Credential Status | Runtime Environment Status |
|---|---|---|---|---|
| `excel_processor` | Files & Data | **IMPLEMENTED** | Not Required (In-Process) | Production Ready |
| `csv` | Files & Data | **IMPLEMENTED** | Not Required (In-Process) | Production Ready |
| `secure_file_vault` | Files & Storage | **IMPLEMENTED** | Not Required (Local Encryption) | Production Ready |
| `pdf_engine` | Files & Data | **IMPLEMENTED** | Not Required (In-Process PyPDF/ReportLab) | Production Ready |
| `document_word` | Files & Data | **IMPLEMENTED** | Not Required (In-Process python-docx) | Production Ready |
| `image_vision` | Files & Data | **IMPLEMENTED** | Optional Tesseract / Vision Engine | Sandbox / Production Ready |
| `custom_api` | Network / API | **IMPLEMENTED** | Target Endpoint Auth Token Required | Production Ready (SSRF Protected) |
| `whatsapp_business` | Communication | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (Meta WABA Token, Phone ID) | **MOCK/SANDBOX** (Failsafe to Not Configured without Token) |
| `mobile_sms` | Communication | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (Twilio SID, Auth Token) | **MOCK/SANDBOX** (Failsafe to Not Configured without Token) |
| `voice_telephony` | Communication | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (Twilio Voice / SIP trunk) | **MOCK/SANDBOX** (Failsafe to Not Configured without Token) |
| `gmail_oauth` | Email | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (Google Cloud OAuth Client/Secret) | **MOCK/SANDBOX** (OAuth Flow Implemented) |
| `universal_email` | Email | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (SMTP/SendGrid Credentials) | **MOCK/SANDBOX** (Failsafe to Not Configured without Token) |
| `cloud_storage` | Storage | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (AWS S3 / GCP Storage Bucket) | **MOCK/SANDBOX** (Local Fallback Implemented) |
| `calendar_scheduling` | Productivity | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (Google / Outlook Calendar API) | **MOCK/SANDBOX** (In-Memory Fallback Implemented) |
| `notification_service`| Productivity | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (APNS / FCM / Push Key) | **MOCK/SANDBOX** (SSE Broadcast Implemented) |
| `hospital_network` | Healthcare | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (Hospital FHIR R4 Endpoint Credentials) | **MOCK/SANDBOX** (Synthetic Mock Provider Available) |
| `insurance_tpa` | Healthcare | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (Payer Portal / Claims Clearinghouse Auth) | **MOCK/SANDBOX** (Synthetic Mock Provider Available) |
| `payment_gateway` | Payments | **IMPLEMENTED** | **CONFIGURATION REQUIRED** (Stripe / Razorpay Secret Keys) | **MOCK/SANDBOX** (Test Mode Active) |
| `epic_cerner_direct` | Healthcare | **NOT IMPLEMENTED** | Vendor B2B Certification Required | Planned / Future Phase |
| `hl7_v2_mllp` | Healthcare | **NOT IMPLEMENTED** | Legacy Interface Engine Required | Planned / Future Phase |

