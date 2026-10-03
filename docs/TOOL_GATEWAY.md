# MedSentinel — Zero-Trust Tool Gateway

The `AgentToolGateway` is a security barrier insulating core databases, patient records, and external APIs from AI agents.

---

## 1. Security Architecture

```
Agent Invocations
       │
       ▼
AgentToolGateway.execute_tool(agent_name, tool_name, kwargs, user_id, user_role, patient_id)
       │
       ├──► 1. Tool Existence Check (Typed Registry)
       ├──► 2. Agent Tool Allowlist Verification (`AGENT_TOOL_ALLOWLIST`)
       ├──► 3. RBAC Privilege Enforcement (Role Gate)
       ├──► 4. Patient Boundary & Data Isolation Gate
       ├──► 5. Outbound PII Redaction Filter (Scrub Aadhaar, PAN, Phone, Email)
       ├──► 6. Real Tool Invocation (Clean Sandboxed Function)
       ├──► 7. Inbound Result Validation & Sanitization
       └──► 8. Audit Log Emission to MySQL (`audit_logs`)
```

---

## 2. PII Redaction Engine

Outbound parameters are passed through deterministic regex filters before touching external systems or agent short-term memory:
- **Aadhaar Numbers**: `\b\d{4}\s?\d{4}\s?\d{4}\b` ──► `[REDACTED_AADHAAR]`
- **PAN Cards**: `\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b` ──► `[REDACTED_PAN]`
- **Indian Phone Numbers**: `(?:\+91[-\s]?)?[6-9]\d{9}` ──► `[REDACTED_PHONE]`
- **Email Addresses**: `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}` ──► `[REDACTED_EMAIL]`

---

## 3. Registered Typed Tools

| Tool Identifier | Description | Required Role | Allowlisted Agents |
| :--- | :--- | :--- | :--- |
| `search_patient` | Looks up patient demographic records by code or name | DOCTOR, ADMIN | IntentAgent, PatientIntakeAgent |
| `get_patient_timeline` | Compiles chronological patient history | DOCTOR, ADMIN | PatientIntakeAgent, VerificationAgent, HumanReviewAgent |
| `get_lab_results` | Retrieves numeric biomarker parameters | DOCTOR, ADMIN | LabAnalysisAgent, RiskAssessmentAgent |
| `search_documents` | Retrieves verified medical vault records | ALL_AUTHENTICATED | DocumentIntelligenceAgent, OCRAgent, VerificationAgent |
| `retrieve_medical_knowledge` | Performs grounded FastEmbed semantic search | ALL_AUTHENTICATED | ClinicalRAGAgent, MedicalKnowledgeAgent, MedicationSafetyAgent |
| `analyze_lab_results` | Evaluates biomarker levels against normal/panic limits | DOCTOR, ADMIN | LabAnalysisAgent |
| `check_medication_safety` | Checks drug interactions and therapeutic duplications | DOCTOR, ADMIN | MedicationSafetyAgent |
| `analyze_claim` | Audits health insurance claims against billing limits | INSURANCE_OFFICER, ADMIN | ClaimsAgent, FraudDetectionAgent |
| `detect_claim_anomaly` | Runs fraud rule matrix against insurance claims | INSURANCE_OFFICER, ADMIN | FraudDetectionAgent |
| `run_healthcare_analytics` | Executes AST-validated DuckDB analytical queries | ADMIN, DOCTOR | DataAnalystAgent |
| `generate_report` | Synthesizes multi-agent telemetry into clinical report | DOCTOR, ADMIN | ReportGenerationAgent |
