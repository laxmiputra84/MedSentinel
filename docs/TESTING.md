# MedSentinel — Quality Assurance & Testing Guide

MedSentinel maintains rigorous quality assurance across unit, integration, API, security, and multi-agent workflow tiers.

---

## 1. Test Suite Summary

- **Total Test Cases**: **128 Automated Tests**
  - **118 Existing Tests**: Regression-tested and 100% passing across auth, claims, eligibility, hospitals, insurances, medical vault, OCR, recommendations, schemes, and workflow APIs.
  - **10 Master Agentic Tests**: Verifying the newly implemented Agent Tool Gateway, PII Redaction, Intent parsing, Dynamic DAG Planning, FastEmbed ONNX Embeddings, DuckDB Healthcare Analytics, Medication Safety & DDI, Patient 360, and Human Review Escalation.
- **Test Framework**: `pytest` and `pytest-asyncio` with `httpx` / Starlette `TestClient`.
- **Database Fixture**: In-memory SQLite (`sqlite:///:memory:`) using standard SQLAlchemy transactions for zero-side-effect test execution.

---

## 2. Running Tests

```bash
# Execute the entire suite
python -m pytest backend/tests -q

# Execute specific master agentic tests
python -m pytest backend/tests/test_master_agentic_system.py -v

# Execute workflow engine tests
python -m pytest backend/tests/test_agent_workflow_api.py -v

# Execute RAG and private AI tests
python -m pytest backend/tests/test_rag_and_private_ai.py -v
```

---

## 3. Key Test Categories

1. **Security & Tool Gateway**:
   - Verification that agents cannot access un-allowlisted tools.
   - Verification that outbound Aadhaar, PAN, phone numbers, and emails are scrubbed before reaching tools.
2. **Clinical Safety & Non-Autonomous Decision Policy**:
   - Critical panic lab values (Platelets < 25,000, Hemoglobin < 6.5) trigger escalation to human review.
   - Hazardous Drug-Drug Interactions (e.g. Warfarin + Aspirin) trigger clinical warnings and halt automated execution.
3. **DuckDB Analytics Sandboxing**:
   - Verification that analytical text is translated into valid SQL.
   - Injection attacks and DDL statements (`DROP TABLE`, `INSERT INTO`) are detected and rejected.
4. **Workflow Persistence & Checkpoints**:
   - Verification that workflow instances and step records are saved to the database.
   - In-flight workflows are restored cleanly after server resets.
