# MedSentinel — AI-Powered Healthcare Multi-Agent Platform

> **Production-grade Hybrid AI Agentic Healthcare Platform built with Next.js 14 App Router, FastAPI, MySQL 8.0, Redis Event Streaming, and ONNX Runtime. Engineered with an 18-agent fleet, Dynamic DAG Planning, Zero-Trust Tool Gateway with deterministic PII redaction, FastEmbed local semantic RAG, DuckDB OLAP Healthcare Analytics, Patient 360° longitudinal timeline, and a Human-in-the-Loop Review Center enforcing a Zero-Autonomous-Harm policy.**

---

## 🌟 Master System Capabilities

- **Multi-Agent Orchestration**: Master `SupervisorAgent` coordinates `IntentAgent`, `PlannerAgent`, and 16 specialized agents via dynamic Directed Acyclic Graphs (DAGs) with cycle validation and parallel batching.
- **Persistent Workflow State**: Volatile in-memory state replaced with durable MySQL tables (`workflow_instances`, `workflow_steps`, `workflow_events`, `workflow_checkpoints`, `human_reviews`), surviving unexpected backend restarts.
- **Redis Event Streaming**: Resilient pub/sub streaming bus delivering real-time lifecycle events to Server-Sent Events (SSE) frontend clients with in-memory fallback.
- **Zero-Trust Tool Gateway**: Strict permission check, per-agent tool allowlist, and deterministic PII redaction (Aadhaar, PAN, phone, email) before invoking typed tools.
- **Real Semantic RAG**: Local FastEmbed ONNX transformer embeddings (`BAAI/bge-small-en-v1.5`, 384 dimensions) with cosine similarity retrieval, eliminating non-semantic hash approximations.
- **Clinical Safety Engine & Human-in-the-Loop**: Strict deterministic safety rules automatically escalate panic biomarker values, severe Drug-Drug Interactions (DDI), and high-risk claims anomalies to the `/human-review` portal.
- **Patient 360° & Longitudinal Timeline**: Unified view synthesizing demographics, risk stratification, diagnostic lab trends, medical documents, and insurance claims.
- **AI Healthcare Data Analyst**: DuckDB in-memory OLAP analytics translating natural language queries into read-only SQL with deterministic Abstract Syntax Tree (AST) validation.
- **Quality Assurance**: **128 / 128 automated tests passing** (118 existing regression tests + 10 comprehensive master agentic tests).

---

## 🏗️ Architectural Topology

```
USER / CLINICIAN
       │
       ▼
NEXT.JS 14 FRONTEND (App Router / SSE Agent Workflow Visualizer / Human Review Center)
       │
       ▼
FASTAPI ASYNC GATEWAY (OAuth2 JWT / Hierarchical RBAC / Pydantic v2)
       │
       ▼
SUPERVISOR AGENT (`SupervisorAgent`)
  ├──► INTENT AGENT (`IntentAgent`)
  ├──► PLANNER AGENT (`PlannerAgent` - Dynamic DAG)
  │
  ├──► PARALLEL BATCH SCHEDULER
  │     ├── DocumentIntelligenceAgent & OCRAgent
  │     ├── LabAnalysisAgent & RiskAssessmentAgent
  │     ├── ClinicalRAGAgent (FastEmbed ONNX 384-dim)
  │     ├── MedicationSafetyAgent (DDI & Duplicate Therapy)
  │     ├── ClaimsAgent & FraudDetectionAgent
  │     ├── DataAnalystAgent (DuckDB OLAP Engine)
  │     └── ReportGenerationAgent
  │
  ├──► TOOL GATEWAY (`AgentToolGateway` - PII Redaction & Allowlist)
  │
  ├──► SAFETY ARBITER (`SafetyAgent` - Deterministic Panic Gate)
  │
  ├──► HUMAN-IN-THE-LOOP CENTER (`HumanReviewAgent` & `/human-reviews`)
  │
  └──► PERSISTENCE & EVENT STREAMING
        ├── MySQL 8.0 (Checkpoints, Steps, States, Reviews)
        └── Redis Event Bus ──► SSE ──► Next.js Visualizer
```

---

## 📁 Repository Structure

```
MedSentinel/
├── backend/                       # Python FastAPI Backend
│   ├── app/
│   │   ├── agents/                # Multi-Agent Hierarchy:
│   │   │   ├── supervisor_agent.py      # Master DAG Orchestrator
│   │   │   ├── intent_agent.py          # Structured Intent Extraction
│   │   │   ├── planner_agent.py         # Dynamic DAG Planning & Parallel Batching
│   │   │   ├── medication_safety_agent.py # DDI & Duplicate Therapy Detection
│   │   │   ├── data_analyst_agent.py    # DuckDB OLAP & AST Validation
│   │   │   ├── human_review_agent.py    # Human Review Escalation
│   │   │   ├── tool_gateway.py          # Zero-Trust Tool Gateway & PII Redactor
│   │   │   ├── tools.py                 # Registered Typed Clinical Tools
│   │   │   └── ...                      # OCR, Lab, RAG, Claims, Risk agents
│   │   ├── core/                  # MySQL DB Engine, Config, Security (JWT, bcrypt)
│   │   ├── models/                # SQLAlchemy Models (WorkflowInstance, Steps, Patient, LabResult...)
│   │   ├── routers/               # Endpoints:
│   │   │   ├── workflows.py             # DAG Execution, Checkpoints & SSE Events
│   │   │   ├── human_review.py          # Human-in-the-Loop Decisions (/api/human-reviews)
│   │   │   ├── patient_360.py           # Patient 360, Timeline & Trends (/api/patients)
│   │   │   ├── healthcare_analytics.py  # DuckDB Healthcare Analytics (/api/analytics/query)
│   │   │   ├── agent_monitor.py         # Telemetry & Agent Health (/api/agent-monitor)
│   │   │   └── ...                      # Documents, Health, Claims, Auth
│   │   ├── rag/                   # FastEmbed ONNX & Cloud Semantic Embedding Services
│   │   ├── services/              # Redis Event Bus, Workflow Manager, OCR, Lab Analyzer
│   │   └── main.py                # FastAPI Application Entrypoint
│   ├── tests/                     # 128 Pytest Automated Tests (100% Passing)
│   │   ├── test_master_agentic_system.py # Master Agentic Suite (10/10)
│   │   ├── test_agent_workflow_api.py    # Workflow State & DAG Tests (10/10)
│   │   ├── test_rag_and_private_ai.py    # Semantic Embedding & RAG Tests (6/6)
│   │   └── ...                           # All 118 existing tests passing
│   └── requirements.txt
│
├── frontend/                      # Next.js 14 Web Application
│   ├── app/
│   │   ├── agent-workflow/        # Real-Time Dynamic DAG Visualizer & SSE Stream
│   │   ├── human-review/          # Human-in-the-Loop Review Center
│   │   ├── patients/              # Patient Intelligence Directory
│   │   │   └── [id]/              # Patient 360° Dossier, Timeline & Lab Trends
│   │   ├── analytics/             # DuckDB AI Healthcare Data Analyst Studio
│   │   ├── agent-monitor/         # Fleet Telemetry & Operations Dashboard
│   │   ├── medical-vault/         # Document Ingestion, OCR & Verification
│   │   ├── health-dashboard/      # Clinical KPI Cards & Recommendations
│   │   ├── claims/                # Insurance Claims & Fraud Detection
│   │   └── ...                    # Knowledge Base, Audit, Security, Settings
│   ├── components/                # AgentWorkflowVisualizer, Navbar, ProtectedRoute...
│   ├── lib/                       # AgenticAPI Client & TypeScript Interfaces
│   └── package.json
│
└── docs/                          # Architecture & Engineering Documentation
    ├── AGENTIC_ARCHITECTURE.md    # Master Agentic Specification
    ├── AGENTS.md                  # 18 Specialized Agents Catalog
    ├── WORKFLOW_ENGINE.md         # DAG Execution & Checkpointing
    ├── TOOL_GATEWAY.md            # Zero-Trust Tool Gateway & PII Redaction
    ├── RAG_ARCHITECTURE.md        # FastEmbed ONNX Semantic Embeddings
    ├── SECURITY.md                # Zero Autonomous Harm & RBAC
    ├── DATABASE.md                # MySQL & DuckDB Data Models
    ├── API.md                     # REST & SSE API Reference
    ├── DEPLOYMENT.md              # Production Setup & Configuration
    └── TESTING.md                 # QA & Test Verification Guide
```

---

## ⚡ Quick Start

### 1. Backend Service
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
*Interactive Swagger documentation: `http://localhost:8000/docs`*

### 2. Frontend Web Application
```powershell
cd frontend
npm install
npm run dev
```
*Frontend application: `http://localhost:3000`*

### 3. Running Automated Tests
```powershell
python -m pytest backend/tests -q
```
*Result: **128 passed in ~57s***
