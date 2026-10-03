from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from app.core.database import get_db
from app.models.document import UserDocument
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentVerificationRequest,
)
from app.dependencies.auth import get_current_user, require_any_admin
from app.services.file_service import FileService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/documents", tags=["Medical Documents"])

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

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    document: UploadFile = File(...),
    docType: str = Form("Other"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and securely store medical file in patient's private vault."""
    saved_filename, rel_path, file_size = await FileService.save_upload_file(document)

    doc_record = UserDocument(
        user_id=current_user.id,
        doc_type=docType,
        filename=saved_filename,
        original_name=document.filename or "document",
        file_path=rel_path,
        file_type=document.content_type or "application/octet-stream",
        file_size=file_size,
        status="PENDING"
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    NotificationService.create_notification(
        db=db,
        user_id=current_user.id,
        title="Document Stored in Vault",
        message=f"{doc_record.original_name} was safely uploaded to your private vault.",
        type="document"
    )

    return DocumentUploadResponse(
        id=doc_record.id,
        doc_type=doc_record.doc_type,
        filename=doc_record.filename,
        original_name=doc_record.original_name,
        file_path=doc_record.file_path,
        file_type=doc_record.file_type,
        file_size=doc_record.file_size,
        status=doc_record.status,
        message="Document uploaded successfully"
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

    full_path = os.path.join(FileService.UPLOAD_DIR, doc.filename)
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

    FileService.delete_file(doc.filename)
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully"}
