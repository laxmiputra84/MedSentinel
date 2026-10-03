# MedSentinel — Master REST & SSE API Reference

All API endpoints are documented with OpenAPI schemas at `/docs`. Below is the master endpoint catalog for the agentic healthcare platform.

---

## 1. Multi-Agent Workflow Endpoints

### `POST /api/workflows`
Starts or schedules a multi-agent workflow.
- **Payload**:
  ```json
  {
    "workflow_type": "AUTOMATIC",
    "patient_id": 1,
    "input_data": {
      "clinical_text": "Patient presenting with Platelets 22,000 /uL..."
    }
  }
  ```
- **Response**:
  ```json
  {
    "workflow_id": "c1f7b82e-9d21-4f11-9a72-88192a6c8e31",
    "status": "RUNNING",
    "workflow_type": "AUTOMATIC",
    "created_at": "2026-10-03T12:00:00Z"
  }
  ```

### `GET /api/workflows/{workflow_id}`
Retrieves workflow instance status, executed steps, outputs, and safety evaluations.

### `POST /api/workflows/{workflow_id}/cancel`
Cancels an active or pending workflow.

### `GET /api/workflows/{workflow_id}/events`
Server-Sent Events (SSE) streaming endpoint broadcasting live agent lifecycle telemetry.

---

## 2. Human-in-the-Loop Review Center

### `GET /api/human-reviews`
Lists review tickets filtered by query param `?status=PENDING|ESCALATED|APPROVED|REJECTED`.

### `POST /api/human-reviews/{review_id}/approve`
Medical officer sign-off approving and releasing downstream workflow results.
- **Payload**: `{"comments": "Verified panic value; clinical team notified.", "modifications": null}`

### `POST /api/human-reviews/{review_id}/reject`
Rejects workflow output with mandatory justification notes.

### `POST /api/human-reviews/{review_id}/escalate`
Escalates review ticket to senior specialist.

---

## 3. Patient 360 & Longitudinal Intelligence

### `GET /api/patients/{patient_id}/360`
Unified dossier returning patient profile, overall health score, latest 20 lab values, documents, and active insurance claims.

### `GET /api/patients/{patient_id}/timeline`
Longitudinal chronological timeline combining appointments, lab tests, uploaded documents, and claim filings.

### `GET /api/patients/{patient_id}/labs/trends`
Biomarker trend analysis grouped by test parameter with panic limit annotations.

---

## 4. AI Healthcare Data Analyst (DuckDB)

### `POST /api/analytics/query`
Executes natural language analytical queries against healthcare tables with AST validation.
- **Payload**: `{"query": "Average lab turnaround by department", "chart_type": "bar"}`
- **Response**: `{"query": "...", "sql": "SELECT ...", "data": [...], "columns": [...], "execution_time_ms": 12.4}`

---

## 5. Agent Operations & Telemetry

### `GET /api/agent-monitor`
Real-time operations metrics including active workflows, completion rate, agent fleet latency, and event streaming status.
