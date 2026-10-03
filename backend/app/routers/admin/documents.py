from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from app.core.database import get_db
from app.dependencies.auth import require_any_admin
from app.models import User, UserDocument
from app.services.audit_log_service import AuditLogService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/admin/documents", tags=["Admin - Documents"])

class AdminDocumentVerify(BaseModel):
    status: str # APPROVED, REJECTED
    rejection_reason: Optional[str] = None

@router.get("")
def list_documents(
    status: Optional[str] = None,
    doc_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """List medical records and verification queue across the platform."""
    query = db.query(UserDocument).options(
        joinedload(UserDocument.user)
    )
    if status:
        query = query.filter(UserDocument.status == status)
    if doc_type:
        query = query.filter(UserDocument.doc_type == doc_type)

    total = query.count()
    docs = query.order_by(UserDocument.upload_date.desc()).offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "id": d.id,
            "user_id": d.user_id,
            "patient_name": d.user.name if d.user else "Patient",
            "patient_email": d.user.email if d.user else "N/A",
            "doc_type": d.doc_type,
            "filename": d.original_name,
            "file_path": d.file_path,
            "file_size": d.file_size,
            "status": d.status,
            "upload_date": d.upload_date.isoformat() if d.upload_date else None,
            "verified_at": d.verified_at.isoformat() if d.verified_at else None,
            "rejection_reason": d.rejection_reason
        }
        for d in docs
    ]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items
    }

@router.patch("/{document_id}/verify")
def verify_document(
    document_id: int,
    payload: AdminDocumentVerify,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_any_admin)
):
    """Approve or reject a patient medical document."""
    doc = db.query(UserDocument).filter(UserDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if payload.status not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be APPROVED or REJECTED.")

    doc.status = payload.status
    doc.verified_by_id = current_admin.id
    doc.verified_at = datetime.now(timezone.utc)
    if payload.status == "REJECTED":
        doc.rejection_reason = payload.rejection_reason or "Document does not satisfy requirements."
    else:
        doc.rejection_reason = None

    db.commit()
    db.refresh(doc)

    # Trigger notification to user
    NotificationService.create_notification(
        db=db,
        user_id=doc.user_id,
        title=f"Document {payload.status.title()}",
        message=f"Your {doc.doc_type} ({doc.original_name}) has been marked as {payload.status}." + (f" Reason: {doc.rejection_reason}" if doc.rejection_reason else ""),
        type="document"
    )

    # Log audit
    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action=f"DOCUMENT_{payload.status}",
        resource_type="Document",
        resource_id=str(doc.id),
        new_value={"status": payload.status, "reason": doc.rejection_reason}
    )

    return {
        "id": doc.id,
        "status": doc.status,
        "verified_at": doc.verified_at.isoformat(),
        "rejection_reason": doc.rejection_reason
    }
