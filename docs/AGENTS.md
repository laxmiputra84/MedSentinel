# MedSentinel — Specialized Agent Fleet Specification

MedSentinel orchestrates 18 specialized agents across clinical, diagnostic, pharmaceutical, financial, and analytical modalities. Every agent implements typed inputs, structured outputs, strict timeouts, bounded retries, and access to explicitly allowlisted tools.

---

## Agent Directory & Responsibilities

### 1. `SupervisorAgent`
- **Role**: Master orchestrator. Coordinates intent extraction, dynamic DAG synthesis, batch parallel dispatch, safety evaluation, human escalations, and event emission.
- **Allowed Tools**: None (orchestration supervisor only; calls other agents).
- **Timeouts**: 120s overall workflow timeout.

### 2. `IntentAgent`
- **Role**: Parses unstructured clinical text or user requests into a typed `StructuredIntent` object containing workflow target, patient ID, requested operation, and initial risk tier.
- **Allowed Tools**: `search_patient`

### 3. `PlannerAgent`
- **Role**: Generates execution plans, determines step dependencies, constructs execution tiers for parallel scheduling, and validates DAG acyclicity.
- **Allowed Tools**: None (deterministic and LLM planning compiler).

### 4. `PatientIntakeAgent`
- **Role**: Validates patient demographic records, cross-references national ID formats, and initializes patient session state.
- **Allowed Tools**: `search_patient`, `get_patient_timeline`

### 5. `DocumentIntelligenceAgent`
- **Role**: Validates uploaded PDF/JPEG/PNG documents, computes SHA-256 hashes, performs MIME verification, and classifies document category (Lab Report, Prescription, Claim Form, Discharge Summary).
- **Allowed Tools**: `search_documents`

### 6. `OCRAgent`
- **Role**: Extracts raw text and bounding boxes from scanned images and PDFs using PyTesseract with layout analysis and pre-processing.
- **Allowed Tools**: `search_documents`

### 7. `LabAnalysisAgent`
- **Role**: Extracts discrete biomarker parameters (Hemoglobin, Platelets, WBC, Glucose, etc.), normalizes units, maps against sex/age-adjusted reference intervals, and flags abnormal/panic thresholds.
- **Allowed Tools**: `get_lab_results`, `analyze_lab_results`

### 8. `ClinicalRAGAgent`
- **Role**: Executes hybrid semantic vector retrieval via FastEmbed ONNX against clinical knowledge chunks and synthesizes grounded, cited responses.
- **Allowed Tools**: `retrieve_medical_knowledge`, `search_documents`

### 9. `MedicalKnowledgeAgent`
- **Role**: Provides authoritative clinical practice guidelines, diagnostic criteria, and standard treatment protocols with source attribution.
- **Allowed Tools**: `retrieve_medical_knowledge`

### 10. `MedicationSafetyAgent`
- **Role**: Cross-checks prescribed medications against patient history and reference knowledge to detect critical Drug-Drug Interactions (DDI) and duplicate therapeutic classes.
- **Allowed Tools**: `check_medication_safety`, `retrieve_medical_knowledge`

### 11. `RiskAssessmentAgent`
- **Role**: Computes composite health risk scores (0-100), readmission risk likelihood, and clinical severity index based on multi-parameter lab trends and vital signs.
- **Allowed Tools**: `get_lab_results`, `get_patient_timeline`

### 12. `ClaimsAgent`
- **Role**: Ingests health insurance claims, verifies policy coverage limits, matches billing items against hospital fee schedules, and flags discrepancies.
- **Allowed Tools**: `analyze_claim`, `search_documents`

### 13. `FraudDetectionAgent`
- **Role**: Evaluates claims against deterministic fraud rule matrices (excessive billing, duplicate claims, phantom procedures, unbundled billing) and calculates anomaly confidence scores.
- **Allowed Tools**: `analyze_claim`, `detect_claim_anomaly`

### 14. `VerificationAgent`
- **Role**: Cross-verifies extracted data across multiple modalities (e.g., verifying that prescription dates align with hospital admission records and claim invoice dates).
- **Allowed Tools**: `get_patient_timeline`, `search_documents`

### 15. `DataAnalystAgent`
- **Role**: Executes DuckDB OLAP queries over healthcare datasets, aggregates longitudinal patient metrics, and returns structured tables with verified SQL ASTs.
- **Allowed Tools**: `run_healthcare_analytics`

### 16. `ReportGenerationAgent`
- **Role**: Synthesizes multi-agent telemetry and findings into a cohesive, structured clinical or insurance evaluation report.
- **Allowed Tools**: `generate_report`, `get_patient_timeline`

### 17. `SafetyAgent`
- **Role**: Centralized safety arbiter. Inspects all agent outputs for panic thresholds, drug interactions, or high-risk claims anomalies. Enforces the zero-autonomous-harm policy.
- **Allowed Tools**: None (governance arbiter).

### 18. `HumanReviewAgent`
- **Role**: Manages clinical escalation tickets. Creates pending review entries, notifies medical review officers, and halts downstream autonomous releases until human approval is signed off.
- **Allowed Tools**: `get_patient_timeline`
