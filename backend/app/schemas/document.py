from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    user_id: int
    patient_id: Optional[int] = None
    document_code: Optional[str] = None
    file_hash: Optional[str] = None
    doc_type: str
    filename: str
    original_name: str
    file_path: str
    file_type: str
    file_size: int
    upload_date: Optional[datetime] = None
    status: str # PENDING, APPROVED, REJECTED
    verification_status: Optional[str] = "PENDING"
    is_duplicate: Optional[bool] = False
    duplicate_of_id: Optional[int] = None
    ai_classification: Optional[str] = None
    ai_confidence: Optional[float] = None
    ocr_extracted_text: Optional[str] = None
    verified_by_id: Optional[int] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentUploadResponse(BaseModel):
    id: int
    doc_type: str
    document_code: Optional[str] = None
    file_hash: Optional[str] = None
    filename: str
    original_name: str
    file_path: str
    file_type: str
    file_size: int
    status: str = "PENDING"
    verification_status: str = "PENDING"
    is_duplicate: bool = False
    duplicate_detected: bool = False
    matching_document_id: Optional[str] = None
    ai_classification: Optional[str] = None
    ai_confidence: Optional[float] = None
    message: str = "Document uploaded successfully"

class DocumentClassifyRequest(BaseModel):
    text: Optional[str] = None
    filename: Optional[str] = None

class DocumentClassifyResponse(BaseModel):
    document_type: str
    confidence: float

class DuplicateCheckResponse(BaseModel):
    duplicate_detected: bool
    matching_document: Optional[Dict[str, Any]] = None
    matching_document_id: Optional[str] = None

class DocumentIntegrityResponse(BaseModel):
    document_id: Optional[str] = None
    hash: Optional[str] = None
    verification_status: str
    valid: bool
    message: str

class DocumentVerificationRequest(BaseModel):
    status: str # APPROVED, REJECTED
    rejection_reason: Optional[str] = None
