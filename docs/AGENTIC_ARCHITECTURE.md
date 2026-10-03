# MedSentinel — Master AI Agentic Architecture

MedSentinel is a production-grade **Hybrid AI Agentic Healthcare Platform** operating on a zero-autonomous-harm philosophy. It pairs high-speed deterministic validation, rule-based clinical safety gates, and immutable state persistence with controlled LLM reasoning (intent parsing, dynamic DAG planning, grounded clinical summarization, and data analytics assistance).

---

## 1. End-to-End Orchestration Pipeline

```
USER / CLINICIAN
       │
       ▼
NEXT.JS FRONTEND (React 18 / Tailwind / Real-Time SSE)
       │
       ▼
FASTAPI ASYNC GATEWAY (Pydantic v2 / OAuth2 JWT / RBAC)
       │
       ▼
SUPERVISOR AGENT (`SupervisorAgent`)
       │
       ├──► INTENT AGENT (`IntentAgent`): Structured extraction of workflow intent & patient context
       │
       ├──► PLANNER AGENT (`PlannerAgent`): Dynamic DAG construction with dependency resolution & cycle validation
       │
       ▼
CONTROLLED WORKFLOW DAG ENGINE
       │
       ├───► PARALLEL BATCH EXECUTION: Independent agents scheduled concurrently via `asyncio.gather`
       │
       ├───► TOOL GATEWAY (`AgentToolGateway`): Zero-Trust access control, PII redaction, allowlist enforcement
       │
       ├───► SPECIALIZED AGENTS:
       │       • DocumentIntelligenceAgent (Validation & Classification)
       │       • OCRAgent (Tesseract & Image Extraction)
       │       • LabAnalysisAgent (Numeric biomarker extraction & panic threshold classification)
       │       • ClinicalRAGAgent (Grounded FastEmbed semantic vector retrieval)
       │       • MedicationSafetyAgent (Deterministic Drug-Drug Interaction & duplicate therapy)
       │       • RiskAssessmentAgent (Predictive readmission & clinical risk index)
       │       • ClaimsAgent & FraudDetectionAgent (Rule-based anomaly scoring with explainability)
       │       • VerificationAgent (Cross-modality consistency checking)
       │       • DataAnalystAgent (DuckDB in-memory OLAP & AST-validated SQL generation)
       │       • ReportGenerationAgent (Executive clinical report synthesis)
       │
       ▼
DETERMINISTIC SAFETY ENGINE (`SafetyAgent`)
       │
       ├───► LOW / MEDIUM RISK: Continues with automated validation
       ├───► HIGH / CRITICAL RISK: Halts autonomous workflow; dispatches to Human Review Center
       │
       ▼
HUMAN-IN-THE-LOOP CENTER (`HumanReviewAgent` & `/human-reviews`)
       │
       ├───► Chief Medical Officer / Medical Reviewer inspects telemetry, evidence, & panic values
       └───► Approve & Release, Reject, or Escalate to Sub-specialist
       │
       ▼
FINAL CLINICAL DOSSIER & PERSISTENCE
       ├───► MySQL (WorkflowInstances, Steps, Events, Checkpoints, Reviews)
       └───► Redis Pub/Sub Streaming Bus ──► SSE Event Stream ──► Next.js Visualizer
```

---

## 2. Hybrid Agentic Philosophy

| Modality | Technology / Paradigm | Rationale |
| :--- | :--- | :--- |
| **Safety Gates & Panic Thresholds** | Deterministic Python rules | Medical ethics mandate zero tolerance for LLM hallucinations in critical lab values. |
| **Role-Based Access Control** | FastAPI Security + DB Session | Strict isolation between Patients, Doctors, Hospital Admins, and Insurance Reviewers. |
| **Tool Execution** | Zero-Trust Tool Gateway | Agents never possess raw SQL or network socket access; all calls pass through PII redaction. |
| **Intent Understanding & Planning** | LLM Reasoning + Pydantic Validation | Flexible comprehension of unstructured requests bounded by validated DAG templates. |
| **Knowledge Retrieval** | FastEmbed ONNX (`bge-small-en-v1.5`) | High-throughput, localized 384-dimensional semantic embeddings with zero external API latency. |
| **Analytical OLAP Queries** | DuckDB + AST Validation | Rapid aggregations across patient populations protected against SQL injection and DDL/DML. |

---

## 3. Workflow State & Checkpointing

All workflow transitions are committed to MySQL in ACID-compliant transactions:
1. `WorkflowInstance`: Master record with UUID, user attribution, DAG status, retry counts, and serialized state JSON.
2. `WorkflowStepRecord`: Micro-step execution logs recording start/end timestamps, duration, agent name, and outputs.
3. `WorkflowCheckpointRecord`: State snapshots created before and after critical step execution, enabling zero-loss resume after unexpected backend restarts.
4. `HumanReviewRecord`: Formal escalation records tracking physician approvals, rejection reasons, and audit trails.
