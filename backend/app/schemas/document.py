from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class DocumentResponse(BaseModel):
    id: int
    user_id: int
    doc_type: str
    filename: str
    original_name: str
    file_path: str
    file_type: str
    file_size: int
    upload_date: Optional[datetime] = None
    status: str # PENDING, APPROVED, REJECTED
    verified_by_id: Optional[int] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentUploadResponse(BaseModel):
    id: int
    doc_type: str
    filename: str
    original_name: str
    file_path: str
    file_type: str
    file_size: int
    status: str = "PENDING"
    message: str = "Document uploaded successfully"

class DocumentVerificationRequest(BaseModel):
    status: str # APPROVED, REJECTED
    rejection_reason: Optional[str] = None
