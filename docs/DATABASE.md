# MedSentinel — Database Architecture & Schema Specification

MedSentinel utilizes MySQL 8.0 for relational persistence and ACID transaction guarantees, paired with DuckDB for in-memory analytical OLAP queries.

---

## 1. Entity-Relationship Architecture

```
       ┌───────────┐         1:N         ┌───────────────┐
       │   users   ├────────────────────►│    patients   │
       └─────┬─────┘                     └───────┬───────┘
             │                                   │
             │ 1:N                               │ 1:N
             ▼                                   ▼
┌─────────────────────────┐             ┌─────────────────┐
│       appointments      │             │  lab_results    │
└─────────────────────────┘             └─────────────────┘
             ▲                                   ▲
             │                                   │
             │                                   │ 1:N
┌────────────┴────────────┐             ┌────────┴────────┐
│    insurance_claims     │             │ user_documents  │
└────────────┬────────────┘             └─────────────────┘
             │
             │ 1:1
             ▼
┌─────────────────────────┐
│     fraud_analysis      │
└─────────────────────────┘

════════════════════════════════════════════════════════════════════════════════
                        WORKFLOW PERSISTENCE SUBSYSTEM
════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────┐         1:N         ┌─────────────────────────┐
│   workflow_instances    ├────────────────────►│     workflow_steps      │
└────────────┬────────────┘                     └─────────────────────────┘
             │
             │ 1:N
             ├─────────────────────────────────►┌─────────────────────────┐
             │                                  │     workflow_events     │
             │ 1:N                              └─────────────────────────┘
             ├─────────────────────────────────►┌─────────────────────────┐
             │                                  │   workflow_checkpoints  │
             │ 1:N                              └─────────────────────────┘
             └─────────────────────────────────►┌─────────────────────────┐
                                                │      human_reviews      │
                                                └─────────────────────────┘
```

---

## 2. Table Catalog

| Table | Primary Key | Key Foreign Keys | Purpose |
| :--- | :--- | :--- | :--- |
| `workflow_instances` | `id` (int), `workflow_id` (str) | `user_id`, `patient_id` | Master lifecycle tracking for all agentic DAG executions. |
| `workflow_steps` | `id` (int) | `workflow_id` | Granular per-agent execution logs, durations, and output payloads. |
| `workflow_events` | `id` (int) | `workflow_id` | Historical log of all 13 emitted agent lifecycle events. |
| `workflow_checkpoints` | `id` (int) | `workflow_id` | Complete serialized JSON state snapshots for zero-loss server restart recovery. |
| `human_reviews` | `id` (int) | `workflow_id`, `patient_id`, `reviewer_id` | Human-in-the-loop review tickets, risk classifications, and decisions. |
| `patients` | `id` (int) | `user_id` | Master demographic, clinical, and emergency contact registry. |
| `lab_results` | `id` (int) | `patient_id`, `document_id` | Structured biomarker measurements with panic flag annotations. |
| `insurance_claims` | `id` (int) | `user_id`, `patient_id`, `hospital_id` | Health insurance claim submissions, amounts, and statuses. |
| `audit_logs` | `id` (int) | `user_id` | Immutable security ledger capturing actor, action, IP, and timestamp. |
