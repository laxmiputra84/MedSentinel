# MedSentinel — Security & Governance Architecture

MedSentinel implements healthcare-grade zero-trust security engineered in compliance with HIPAA, ISO 27001, and Indian Digital Personal Data Protection (DPDP) principles.

---

## 1. Authentication & RBAC

- **JWT Token Architecture**: Asymmetric HMAC-SHA256 access tokens (15-minute expiry) paired with cryptographically secure, refresh tokens (7-day rotation).
- **Hierarchical Role Matrix**:
  - `PATIENT`: Self-service access to medical vault, appointments, claims, and personal 360 timeline.
  - `DOCTOR`: Clinical record inspection, lab trajectory evaluation, workflow initialization, and human review sign-off.
  - `HOSPITAL_ADMIN`: Hospital resource allocation, department scheduling, and fee schedule governance.
  - `INSURANCE_OFFICER`: Claims evaluation, fraud anomaly review, and policy adjudication.
  - `ADMIN`: Platform monitoring, security audit log inspection, and system settings.

---

## 2. Zero Autonomous Harm Policy

Under no circumstances does MedSentinel autonomously:
1. Issue a definitive medical diagnosis.
2. Prescribe or modify pharmaceutical dosages.
3. Automatically deny or approve high-value insurance claims.
4. Discharge a patient from a hospital encounter.

All high or critical clinical risk determinations (such as panic lab values or severe drug interactions) trigger deterministic halts, routing the case directly to the **Human Review Center** for medical officer sign-off.

---

## 3. Sandboxed Analytics (DuckDB AST Validation)

Natural language analytical queries are parsed into Abstract Syntax Trees using `sqlparse`. The AST validator enforces:
- Only read-only `SELECT` queries are permitted.
- `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, and `EXEC` statements are rejected at the compiler level before reaching the DuckDB in-memory OLAP engine.
