"""
MedSentinel Agentic Architecture — Tool Calling Wrappers
Asynchronous, standardized tool interfaces wrapping existing backend services,
database queries, ML models, OCR pipelines, verification, and RAG.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.document_classifier import DocumentClassifier
from app.services.ocr_service import OCRService
from app.services.lab_analyzer import LabAnalyzer, STANDARD_LAB_TESTS
from app.services.health_score import HealthScoreEngine
from app.services.document_verifier import DocumentVerifier
from app.services.fraud_detector import FraudDetector
from app.rag.rag_pipeline import RAGPipeline
from app.services.recommendation_engine import RecommendationEngine

from app.models.patient import Patient
from app.models.document import UserDocument
from app.models.lab_result import LabResult
from app.models.insurance_claim import InsuranceClaim


# ==========================================
# 1. Document Intelligence & OCR Tools
# ==========================================

async def classify_document_tool(text: str, filename: str = "") -> Dict[str, Any]:
    """
    Tool: Classifies document type based on extracted text and filename.
    Reuses DocumentClassifier.
    """
    doc_type, confidence = DocumentClassifier.classify_text(text, filename)
    return {
        "document_type": doc_type,
        "confidence": confidence,
        "is_supported": doc_type in [
            "Lab Report", "Prescription", "Medical Invoice",
            "Insurance Document", "Discharge Summary", "Radiology Report", "Scan Report"
        ]
    }


async def extract_ocr_tool(file_path: str) -> Dict[str, Any]:
    """
    Tool: Extracts text from PDF or image using multi-layer OCR pipeline.
    Reuses OCRService in a background thread pool.
    """
    try:
        extracted = await asyncio.to_thread(OCRService.extract_text_from_file, file_path)
        char_count = len(extracted)
        has_content = char_count > 0
        return {
            "success": True,
            "text": extracted,
            "char_count": char_count,
            "confidence": 0.95 if has_content else 0.0,
            "error": None if has_content else "No text could be extracted from file"
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "char_count": 0,
            "confidence": 0.0,
            "error": f"OCR extraction failed: {str(e)}"
        }


# ==========================================
# 2. Clinical Data Validation Tool
# ==========================================

async def validate_clinical_data_tool(tests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tool: Validates clinical sanity of extracted laboratory tests.
    Detects impossible physiological values, missing units, or formatting anomalies.
    NEVER invents or fabricates missing medical data.
    """
    valid_tests: List[Dict[str, Any]] = []
    errors: List[str] = []
    warnings: List[str] = []

    # Biological sanity bounds (extreme absolute physiological limits)
    ABSOLUTE_BOUNDS = {
        "Hemoglobin": (0.5, 30.0),
        "WBC": (100.0, 500000.0),
        "Platelets": (1000.0, 3000000.0),
        "RBC Count": (0.5, 12.0),
        "Fasting Blood Glucose": (10.0, 1500.0),
        "Serum Creatinine": (0.1, 40.0),
        "Total Bilirubin": (0.05, 60.0),
        "Potassium": (1.0, 12.0),
        "Sodium": (70.0, 200.0),
        "HbA1c": (2.0, 22.0),
    }

    for t in tests:
        name = t.get("name")
        val = t.get("value")

        if not name or val is None:
            warnings.append(f"Skipping unparseable lab record without valid name/value: {t}")
            continue

        try:
            num_val = float(val)
        except (ValueError, TypeError):
            errors.append(f"Non-numeric observed value for '{name}': {val}")
            continue

        if num_val < 0:
            errors.append(f"Physiologically impossible negative value for '{name}': {num_val}")
            continue

        # Check extreme physiological limits
        if name in ABSOLUTE_BOUNDS:
            min_limit, max_limit = ABSOLUTE_BOUNDS[name]
            if num_val < min_limit or num_val > max_limit:
                warnings.append(
                    f"Out-of-universe physiological value for '{name}': {num_val} "
                    f"(expected range [{min_limit}, {max_limit}])."
                )

        valid_tests.append(t)

    is_valid = len(errors) == 0 and len(valid_tests) > 0
    return {
        "is_valid": is_valid,
        "valid_tests": valid_tests,
        "errors": errors,
        "warnings": warnings,
        "total_extracted": len(tests),
        "valid_count": len(valid_tests)
    }


# ==========================================
# 3. Laboratory Analysis & Reference Range Tools
# ==========================================

async def analyze_lab_data_tool(text: str) -> Dict[str, Any]:
    """
    Tool: Extracts structured lab parameters, biological ranges, and patient metadata.
    Reuses LabAnalyzer.
    """
    data = LabAnalyzer.extract_laboratory_data(text)
    return {
        "patient_name": data.get("patient_name"),
        "patient_id": data.get("patient_id"),
        "report_date": data.get("report_date"),
        "tests": data.get("tests", []),
        "tests_count": len(data.get("tests", []))
    }


async def evaluate_lab_parameter_tool(
    test_name: str,
    value: float,
    ref_min: Optional[float] = None,
    ref_max: Optional[float] = None
) -> Dict[str, Any]:
    """
    Tool: Evaluates observed parameter against standard clinical biological reference ranges.
    """
    status, is_critical = LabAnalyzer.evaluate_status(test_name, value, ref_min, ref_max)
    return {
        "test_name": test_name,
        "value": value,
        "reference_min": ref_min,
        "reference_max": ref_max,
        "status": status,
        "is_critical": is_critical
    }


# ==========================================
# 4. Patient History & Longitudinal Trends Tool
# ==========================================

async def get_patient_history_tool(
    db: Session,
    patient_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: int = 15
) -> Dict[str, Any]:
    """
    Tool: Retrieves longitudinal test history and previous records for a patient.
    """
    if not patient_id and not user_id:
        return {"records": [], "test_history": {}, "count": 0}

    # Resolve patient
    query_patient = db.query(Patient)
    if patient_id:
        query_patient = query_patient.filter(Patient.id == patient_id)
    elif user_id:
        query_patient = query_patient.filter(Patient.user_id == user_id)
    patient = query_patient.first()

    if not patient:
        return {"records": [], "test_history": {}, "count": 0}

    # Retrieve prior lab results
    past_results = db.query(LabResult).filter(
        LabResult.patient_id == patient.id
    ).order_by(LabResult.test_date.desc()).limit(100).all()

    test_history: Dict[str, List[Dict[str, Any]]] = {}
    for r in past_results:
        if r.test_name not in test_history:
            test_history[r.test_name] = []
        test_history[r.test_name].append({
            "value": r.observed_value,
            "unit": r.unit,
            "status": r.status,
            "date": r.test_date.isoformat() if r.test_date else None,
            "is_critical": r.is_critical
        })

    # Retrieve past documents
    past_docs = db.query(UserDocument).filter(
        UserDocument.patient_id == patient.id
    ).order_by(UserDocument.upload_date.desc()).limit(limit).all()

    doc_list = [{
        "id": d.id,
        "code": d.document_code,
        "type": d.doc_type,
        "name": d.original_name,
        "date": d.upload_date.isoformat() if d.upload_date else None,
        "status": d.verification_status
    } for d in past_docs]

    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "patient_code": patient.patient_code,
        "test_history": test_history,
        "documents": doc_list,
        "total_past_tests": len(past_results),
        "total_past_documents": len(past_docs)
    }


# ==========================================
# 5. Medical Risk & Health Scoring Tool
# ==========================================

async def calculate_health_risk_tool(tests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tool: Computes composite health and risk score, and generates non-diagnostic summary.
    Reuses HealthScoreEngine.
    """
    health_score, risk_score, risk_level, abnormal_count = HealthScoreEngine.calculate_scores(tests)
    ai_summary = HealthScoreEngine.generate_health_summary(tests, risk_level)

    return {
        "health_score": health_score,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "abnormal_count": abnormal_count,
        "ai_summary": ai_summary,
        "requires_escalation": risk_level in ["HIGH", "CRITICAL"]
    }


# ==========================================
# 6. Verification & Cryptographic Hash Tools
# ==========================================

async def verify_document_integrity_tool(db: Session, doc_id: int) -> Dict[str, Any]:
    """
    Tool: Cryptographically verifies file integrity against SHA-256 hash.
    Reuses DocumentVerifier.
    """
    return DocumentVerifier.verify_document_integrity(db, doc_id)


async def check_duplicate_document_tool(
    db: Session,
    file_hash: str,
    exclude_doc_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Tool: Checks if file hash already exists in database.
    Reuses DocumentVerifier.
    """
    is_dup, matching_doc = DocumentVerifier.check_duplicate(db, file_hash, exclude_doc_id)
    return {
        "is_duplicate": is_dup,
        "matching_document_id": matching_doc.id if matching_doc else None,
        "matching_document_code": matching_doc.document_code if matching_doc else None,
        "matching_original_name": matching_doc.original_name if matching_doc else None,
    }


def generate_document_code_tool() -> str:
    """Tool: Generates formatted DOC-YYYY-NNNNNN identifier."""
    return DocumentVerifier.generate_document_code()


# ==========================================
# 7. Insurance Claims Fraud Tool
# ==========================================

async def detect_claim_fraud_tool(db: Session, claim_id: int) -> Dict[str, Any]:
    """
    Tool: Evaluates claim for duplication, velocity spikes, and fraud signals.
    Reuses FraudDetector.
    """
    return FraudDetector.analyze_claim(db, claim_id)


# ==========================================
# 8. Private Medical RAG Retrieval Tool
# ==========================================

async def query_medical_rag_tool(
    query: str,
    user_role: str = "USER",
    user_id: Optional[int] = None,
    user_hospital_id: Optional[int] = None,
    mode: str = "strict_private",
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Tool: Retrieves verified, tenant-isolated medical knowledge with citations.
    Reuses RAGPipeline.
    """
    return await RAGPipeline.execute_rag_query(
        query=query,
        user_role=user_role,
        user_id=user_id,
        user_hospital_id=user_hospital_id,
        mode=mode,
        db=db
    )


# ==========================================
# 9. Recommendation Engine Tool
# ==========================================

async def generate_recommendations_tool(
    db: Session,
    user_id: int,
    patient_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Tool: Generates multi-signal hybrid recommendations.
    Reuses RecommendationEngine.
    """
    return RecommendationEngine.generate_all_recommendations(db, user_id, patient_id)


async def get_patient_demographics_tool(db: Session, patient_id: int) -> Dict[str, Any]:
    """Tool: Resolves patient identity and verified demographic details."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {}
    return {
        "id": patient.id,
        "name": patient.name,
        "patient_code": patient.patient_code,
        "blood_group": patient.blood_group,
        "gender": patient.gender,
        "emergency_contact": patient.emergency_contact
    }


# ==========================================
# 10. Register Typed Tools in Tool Gateway
# ==========================================

from app.agents.tool_gateway import agent_tool_gateway, TypedToolDefinition, ToolRiskTier

agent_tool_gateway.register_tool(
    TypedToolDefinition(name="search_patient", description="Look up patient demographics by ID", risk_tier=ToolRiskTier.LOW),
    get_patient_demographics_tool
)
agent_tool_gateway.register_tool(
    TypedToolDefinition(name="get_patient_timeline", description="Retrieve longitudinal clinical timeline", risk_tier=ToolRiskTier.LOW),
    get_patient_history_tool
)
agent_tool_gateway.register_tool(
    TypedToolDefinition(name="analyze_lab_results", description="Extract and analyze lab parameters against biological ranges", risk_tier=ToolRiskTier.LOW),
    analyze_lab_data_tool
)
agent_tool_gateway.register_tool(
    TypedToolDefinition(name="validate_clinical_data", description="Check physiological sanity of extracted lab tests", risk_tier=ToolRiskTier.LOW),
    validate_clinical_data_tool
)
agent_tool_gateway.register_tool(
    TypedToolDefinition(name="classify_document", description="Classify medical document category", risk_tier=ToolRiskTier.LOW),
    classify_document_tool
)
agent_tool_gateway.register_tool(
    TypedToolDefinition(name="extract_ocr", description="Extract text from PDF or image", risk_tier=ToolRiskTier.LOW),
    extract_ocr_tool
)
agent_tool_gateway.register_tool(
    TypedToolDefinition(name="retrieve_medical_knowledge", description="Query tenant-isolated medical knowledge base", risk_tier=ToolRiskTier.LOW),
    query_medical_rag_tool
)
agent_tool_gateway.register_tool(
    TypedToolDefinition(name="detect_claim_anomaly", description="Evaluate claim fraud risk and billing anomalies", risk_tier=ToolRiskTier.MEDIUM),
    detect_claim_fraud_tool
)
agent_tool_gateway.register_tool(
    TypedToolDefinition(name="calculate_health_risk", description="Calculate composite health risk score", risk_tier=ToolRiskTier.LOW),
    calculate_health_risk_tool
)
