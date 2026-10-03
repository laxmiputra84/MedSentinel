# MedSentinel — Webhook Security & Ingestion Architecture

## 1. Overview

MedSentinel's Webhook Security Gateway (`/api/webhooks/*`) accepts asynchronous event notifications from external providers (WhatsApp Cloud API, Twilio SMS, Telephony providers). Because webhooks originate over the public internet, they are subject to strict cryptographic verification, replay mitigation, and schema validation.

---

## 2. Inbound Webhook Execution Pipeline

```text
       INCOMING WEBHOOK HTTP POST
                   │
                   ▼
┌──────────────────────────────────────┐
│  1. HMAC-SHA256 SIGNATURE VALIDATION │  (X-Hub-Signature-256, X-Twilio-Signature)
└──────────────────┬───────────────────┘
                   │ Signature Verified
                   ▼
┌──────────────────────────────────────┐
│   2. TIMESTAMP & REPLAY MITIGATION   │  (Sliding 300s window & Seen Event IDs)
└──────────────────┬───────────────────┘
                   │ Nonce Valid & Non-Duplicate
                   ▼
┌──────────────────────────────────────┐
│  3. TAMPER-EVIDENT INGESTION LEDGER  │  (Persist to PluginWebhookEvent Table)
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  4. EXTERNAL CONTENT SANITIZATION    │  (Wrap in <EXTERNAL_UNTRUSTED_DATA>)
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  5. AGENT ORCHESTRATION DISPATCH     │  (Route to PatientCommunication / Email Agent)
└──────────────────────────────────────┘
```

---

## 3. Cryptographic Verification Standard

### WhatsApp Cloud API
- Header: `X-Hub-Signature-256: sha256=<hex_digest>`
- Algorithm:
  ```python
  expected_signature = hmac.new(
      key=WHATSAPP_APP_SECRET.encode('utf-8'),
      msg=raw_request_body,
      digestmod=hashlib.sha256
  ).hexdigest()
  assert hmac.compare_digest(provided_signature, expected_signature)
  ```
- Handshake: Supports Meta's `GET /api/webhooks/whatsapp` challenge-response protocol (`hub.mode=subscribe`, `hub.verify_token`, `hub.challenge`).

### Twilio SMS & Voice
- Validates `X-Twilio-Signature` using the account authentication token across the URL and sorted POST parameters.

---

## 4. Replay Attack Defense & Event Idempotency

1. **Event ID Extraction:** Provider message IDs (`wamid.*`, `MessageSid`, `CallSid`) are extracted.
2. **Deduplication Sliding Cache:** An in-memory and database-backed cache tracks processed event IDs within a 300-second window.
3. **Rejection of Duplicates:** Immediate duplicates return `HTTP 409 Conflict`, preventing duplicate patient messages or multiple claim document submissions.
