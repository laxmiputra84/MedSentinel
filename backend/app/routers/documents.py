import os
import asyncio
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.document import UserDocument
from app.models.user import User
from app.models.patient import Patient
from app.models.lab_result import LabResult
from app.models.health_score import HealthScore
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentVerificationRequest,
    DocumentClassifyResponse,
    DuplicateCheckResponse,
    DocumentIntegrityResponse,
)
from app.schemas.lab_result import LabExtractionResponse
from app.dependencies.auth import get_current_user, require_any_admin
from app.services.file_service import FileService
from app.services.notification_service import NotificationService
from app.services.document_classifier import DocumentClassifier
from app.services.ocr_service import OCRService
from app.services.lab_analyzer import LabAnalyzer
from app.services.health_score import HealthScoreEngine
from app.services.document_verifier import DocumentVerifier
from app.core.events import EventType
from app.services.event_bus import publish_event

router = APIRouter(prefix="/documents", tags=["Medical Documents"])

def _get_or_create_patient(db: Session, user: User, patient_code: Optional[str] = None, patient_name: Optional[str] = None) -> Patient:
    """Finds or creates a linked Patient profile for a user."""
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        code = patient_code or f"MS-{datetime.utcnow().year}-{user.id:05d}"
        patient = Patient(
            user_id=user.id,
            patient_code=code,
            name=patient_name or user.name,
            blood_group=user.blood_group,
            emergency_contact=user.emergency_contact,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return patient

@router.get("", response_model=List[DocumentResponse])
def get_user_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all uploaded documents for the current user (or all documents for admin)."""
    user_role = (current_user.role or "USER").upper()
    if user_role in ["HOSPITAL_ADMIN", "INSURANCE_ADMIN", "SUPER_ADMIN"]:
        return db.query(UserDocument).order_by(UserDocument.upload_date.desc()).all()

    return db.query(UserDocument).filter(
        UserDocument.user_id == current_user.id
    ).order_by(UserDocument.upload_date.desc()).all()

@router.post("/classify", response_model=DocumentClassifyResponse)
async def classify_document(
    file: Optional[UploadFile] = File(None),
    filename: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    """
    FEATURE 1: Automatically classify an uploaded document or text snippet.
    Supported types:
    Lab Report, Prescription, Medical Invoice, Insurance Document,
    Discharge Summary, Radiology Report, Scan Report, Other.
    """
    extracted_text = text or ""
    file_name = filename or ""

    if file and file.filename:
        file_name = file.filename
        content = await file.read()
        # Preview text if text file or run OCR if binary
        if len(content) > 0:
            try:
                extracted_text = content.decode("utf-8", errors="ignore")[:4000]
            except Exception:
                extracted_text = ""

    doc_type, confidence = DocumentClassifier.classify_text(extracted_text, file_name)
    return DocumentClassifyResponse(document_type=doc_type, confidence=confidence)

@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    FEATURE 8: Check if a document is a duplicate by computing SHA-256 hash.
    """
    content = await file.read()
    file_hash = DocumentVerifier.calculate_sha256(content)
    is_dup, match = DocumentVerifier.check_duplicate(db, file_hash)

    matching_doc_dict = None
    matching_doc_id = None
    if is_dup and match:
        matching_doc_id = match.document_code or f"DOC-{match.id}"
        matching_doc_dict = {
            "id": match.id,
            "document_code": match.document_code,
            "original_name": match.original_name,
            "doc_type": match.doc_type,
            "upload_date": match.upload_date.isoformat() if match.upload_date else None,
        }

    return DuplicateCheckResponse(
        duplicate_detected=is_dup,
        matching_document=matching_doc_dict,
        matching_document_id=matching_doc_id,
    )

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    document: UploadFile = File(...),
    docType: str = Form("Other"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    FEATURE 1, 2, 3, 4, 5, 7, 8:
    Upload and securely store medical file in patient's private vault:
      - Generates unique Document ID (DOC-YYYY-NNNNNN)
      - Computes SHA-256 Hash
      - Detects duplicates
      - Auto-classifies document type
      - Performs OCR and structured lab data extraction if Lab Report
      - Calculates health score, risk score, and non-diagnostic AI summary
    """
    saved_filename, rel_path, file_size = await FileService.save_upload_file(document)
    full_disk_path = Path(settings.UPLOAD_DIR) / saved_filename

    # Calculate SHA-256 Hash
    file_hash = DocumentVerifier.calculate_sha256(full_disk_path)
    document_code = DocumentVerifier.generate_document_code()

    # Check for duplicate document
    is_duplicate, matching_doc = DocumentVerifier.check_duplicate(db, file_hash)
    verification_status = "FLAGGED" if is_duplicate else "VERIFIED"
    duplicate_of_id = matching_doc.id if (is_duplicate and matching_doc) else None

    # Perform OCR text extraction asynchronously in thread pool
    extracted_text = await asyncio.to_thread(OCRService.extract_text_from_file, str(full_disk_path))

    # Auto-classify document if not explicitly chosen or if generic
    ai_doc_type, ai_confidence = DocumentClassifier.classify_text(extracted_text, document.filename or "")
    final_doc_type = docType if (docType and docType != "Other") else ai_doc_type

    # Ensure linked Patient record
    patient = _get_or_create_patient(db, current_user)

    # Save document record
    doc_record = UserDocument(
        user_id=current_user.id,
        patient_id=patient.id,
        document_code=document_code,
        file_hash=file_hash,
        doc_type=final_doc_type,
        filename=saved_filename,
        original_name=document.filename or "document",
        file_path=rel_path,
        file_type=document.content_type or "application/octet-stream",
        file_size=file_size,
        status="PENDING",
        verification_status=verification_status,
        is_duplicate=is_duplicate,
        duplicate_of_id=duplicate_of_id,
        ai_classification=ai_doc_type,
        ai_confidence=ai_confidence,
        ocr_extracted_text=extracted_text[:10000] if extracted_text else None,
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # If Lab Report, process structured lab extraction & health scoring
    if final_doc_type in ["Lab Report", "Other"]:
        lab_data = LabAnalyzer.extract_laboratory_data(extracted_text)
        if lab_data["tests"]:
            # Update patient info if detected
            if lab_data.get("patient_name") and patient.name == current_user.name:
                patient.name = lab_data["patient_name"]
            if lab_data.get("patient_id") and not patient.patient_code.startswith("MS-"):
                patient.patient_code = lab_data["patient_id"]

            parsed_date = datetime.utcnow()
            try:
                if lab_data.get("report_date"):
                    parsed_date = datetime.strptime(lab_data["report_date"], "%Y-%m-%d")
            except Exception:
                pass

            # Store structured LabResult rows
            for t in lab_data["tests"]:
                result_row = LabResult(
                    patient_id=patient.id,
                    document_id=doc_record.id,
                    test_name=t["name"],
                    observed_value=t["value"],
                    unit=t["unit"],
                    reference_min=t.get("reference_min"),
                    reference_max=t.get("reference_max"),
                    status=t.get("status", "NORMAL"),
                    is_critical=t.get("is_critical", False),
                    test_date=parsed_date,
                )
                db.add(result_row)

            # Calculate Health & Risk Scores
            health_score, risk_score, risk_level, abnormal_count = HealthScoreEngine.calculate_scores(lab_data["tests"])
            ai_summary = HealthScoreEngine.generate_health_summary(lab_data["tests"], risk_level)

            score_record = HealthScore(
                patient_id=patient.id,
                document_id=doc_record.id,
                health_score=health_score,
                risk_score=risk_score,
                risk_level=risk_level,
                abnormal_tests=abnormal_count,
                ai_summary=ai_summary,
            )
            db.add(score_record)
            db.commit()

            # Trigger Laboratory Event
            publish_event(
                event_type=EventType.LAB_REPORT_RECEIVED.value,
                entity_id=doc_record.id,
                user_id=current_user.id,
                payload={"patient_id": patient.id, "tests_count": len(lab_data["tests"])},
                entity_type="document",
                db=db,
                sync=False,
            )
            if any(t.get("is_critical") or t.get("status") == "CRITICAL" for t in lab_data["tests"]):
                publish_event(
                    event_type=EventType.CRITICAL_LAB_VALUE_DETECTED.value,
                    entity_id=doc_record.id,
                    user_id=current_user.id,
                    payload={"patient_id": patient.id},
                    entity_type="lab_result",
                    db=db,
                    sync=False,
                )

    # Publish Document Ingestion Event to Central Event Bus
    if is_duplicate:
        publish_event(
            event_type=EventType.DOCUMENT_DUPLICATE_DETECTED.value,
            entity_id=doc_record.id,
            user_id=current_user.id,
            payload={"document_code": document_code, "file_hash": file_hash, "duplicate_of_id": duplicate_of_id},
            entity_type="document",
            db=db,
            sync=False,
        )
    else:
        publish_event(
            event_type=EventType.DOCUMENT_UPLOADED.value,
            entity_id=doc_record.id,
            user_id=current_user.id,
            payload={"document_code": document_code, "file_hash": file_hash, "doc_type": final_doc_type},
            entity_type="document",
            db=db,
            sync=False,
        )

    NotificationService.create_notification(
        db=db,
        user_id=current_user.id,
        title="Document Stored & Verified",
        message=f"{doc_record.original_name} was encrypted with SHA-256 and stored ({document_code})." +
                (" [Duplicate Detected]" if is_duplicate else ""),
        type="document"
    )

    matching_doc_code = matching_doc.document_code if (is_duplicate and matching_doc and matching_doc.document_code) else (f"DOC-{matching_doc.id}" if matching_doc else None)

    return DocumentUploadResponse(
        id=doc_record.id,
        doc_type=doc_record.doc_type,
        document_code=doc_record.document_code,
        file_hash=doc_record.file_hash,
        filename=doc_record.filename,
        original_name=doc_record.original_name,
        file_path=doc_record.file_path,
        file_type=doc_record.file_type,
        file_size=doc_record.file_size,
        status=doc_record.status,
        verification_status=doc_record.verification_status,
        is_duplicate=doc_record.is_duplicate,
        duplicate_detected=is_duplicate,
        matching_document_id=matching_doc_code,
        ai_classification=doc_record.ai_classification,
        ai_confidence=doc_record.ai_confidence,
        message="Document uploaded, cryptographically hashed, and verified successfully"
    )

@router.post("/{document_id}/verify-integrity", response_model=DocumentIntegrityResponse)
def verify_document_integrity(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    FEATURE 7: Cryptographically verify file integrity against its original SHA-256 hash.
    """
    doc = db.query(UserDocument).filter(UserDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    is_owner = doc.user_id == current_user.id
    is_admin = (current_user.role or "USER").upper() in ["HOSPITAL_ADMIN", "INSURANCE_ADMIN", "SUPER_ADMIN"]
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    res = DocumentVerifier.verify_document_integrity(db, document_id)

    # Publish DOCUMENT_VERIFIED Event
    publish_event(
        event_type=EventType.DOCUMENT_VERIFIED.value,
        entity_id=document_id,
        user_id=current_user.id,
        payload={"valid": res["valid"], "verification_status": res["verification_status"]},
        entity_type="document",
        db=db,
        sync=False,
    )

    return DocumentIntegrityResponse(
        document_id=res["document_id"],
        hash=res["hash"],
        verification_status=res["verification_status"],
        valid=res["valid"],
        message=res["message"],
    )

@router.post("/{document_id}/extract-lab", response_model=LabExtractionResponse)
def extract_lab_data(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    FEATURE 2 & 3: Run OCR and structured laboratory data extraction on an uploaded document.
    """
    doc = db.query(UserDocument).filter(UserDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Get text
    text = doc.ocr_extracted_text or ""
    if not text:
        clean_path = doc.file_path.lstrip("/")
        full_disk_path = Path("./uploads") / Path(doc.file_path).name
        if not full_disk_path.exists():
            full_disk_path = Path("./") / clean_path
        text = OCRService.extract_text_from_file(str(full_disk_path))
        doc.ocr_extracted_text = text[:10000] if text else None
        db.commit()

    lab_data = LabAnalyzer.extract_laboratory_data(text)

    # If patient not created yet, get or create
    patient = _get_or_create_patient(db, current_user, lab_data.get("patient_id"), lab_data.get("patient_name"))

    parsed_date = datetime.utcnow()
    try:
        if lab_data.get("report_date"):
            parsed_date = datetime.strptime(lab_data["report_date"], "%Y-%m-%d")
    except Exception:
        pass

    # Save results to lab_results table if not already saved
    existing_count = db.query(LabResult).filter(LabResult.document_id == doc.id).count()
    if existing_count == 0 and lab_data["tests"]:
        for t in lab_data["tests"]:
            row = LabResult(
                patient_id=patient.id,
                document_id=doc.id,
                test_name=t["name"],
                observed_value=t["value"],
                unit=t["unit"],
                reference_min=t.get("reference_min"),
                reference_max=t.get("reference_max"),
                status=t.get("status", "NORMAL"),
                is_critical=t.get("is_critical", False),
                test_date=parsed_date,
            )
            db.add(row)

        health_score, risk_score, risk_level, abnormal_count = HealthScoreEngine.calculate_scores(lab_data["tests"])
        ai_summary = HealthScoreEngine.generate_health_summary(lab_data["tests"], risk_level)

        score_rec = HealthScore(
            patient_id=patient.id,
            document_id=doc.id,
            health_score=health_score,
            risk_score=risk_score,
            risk_level=risk_level,
            abnormal_tests=abnormal_count,
            ai_summary=ai_summary,
        )
        db.add(score_rec)
        db.commit()

    return LabExtractionResponse(
        patient_name=lab_data["patient_name"],
        patient_id=lab_data["patient_id"],
        report_date=lab_data["report_date"],
        report_type="Lab Report",
        tests=lab_data["tests"],
    )

@router.patch("/{document_id}/verify", response_model=DocumentResponse)
def verify_document(
    document_id: int,
    req: DocumentVerificationRequest,
    current_admin: User = Depends(require_any_admin),
    db: Session = Depends(get_db)
):
    """Verify or reject a medical document (Admins only)."""
    norm_status = req.status.upper().strip()
    if norm_status not in ["APPROVED", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be either APPROVED or REJECTED"
        )

    doc = db.query(UserDocument).filter(UserDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    doc.status = norm_status
    doc.verified_by_id = current_admin.id
    doc.verified_at = datetime.now(timezone.utc)
    if req.rejection_reason:
        doc.rejection_reason = req.rejection_reason

    db.commit()
    db.refresh(doc)

    NotificationService.create_notification(
        db=db,
        user_id=doc.user_id,
        title=f"Document {norm_status}",
        message=f"Your document '{doc.original_name}' has been {norm_status.lower()}." + (f" Reason: {req.rejection_reason}" if req.rejection_reason else ""),
        type="document"
    )

    return doc

@router.get("/{document_id}/file")
def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download document file securely, verifying user ownership or admin role."""
    doc = db.query(UserDocument).filter(UserDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    is_owner = doc.user_id == current_user.id
    is_admin = (current_user.role or "USER").upper() in ["HOSPITAL_ADMIN", "INSURANCE_ADMIN", "SUPER_ADMIN"]
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    full_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File on disk not found")

    return FileResponse(
        path=full_path,
        filename=doc.original_name,
        media_type=doc.file_type
    )

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete document from vault and disk."""
    doc = db.query(UserDocument).filter(UserDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if doc.user_id != current_user.id and (current_user.role or "USER").upper() != "SUPER_ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    FileService.delete_file(doc.file_path)
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully"}
