from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import User, UserDocument

def get_user_documents_tool(
    db: Session,
    user: User,
    doc_type: Optional[str] = None
) -> Dict[str, Any]:
    """Retrieve uploaded documents and verification statuses for the authenticated user."""
    query = db.query(UserDocument).filter(UserDocument.user_id == user.id)
    if doc_type:
        query = query.filter(UserDocument.doc_type == doc_type)

    docs = query.order_by(UserDocument.upload_date.desc()).all()

    items = []
    for d in docs:
        items.append({
            "id": d.id,
            "filename": d.original_name,
            "document_type": d.doc_type,
            "status": d.status,
            "upload_date": d.upload_date.isoformat() if d.upload_date else None,
            "verified_at": d.verified_at.isoformat() if d.verified_at else None,
            "rejection_reason": d.rejection_reason,
            "status_explanation": (
                "Verified and accepted by healthcare administrator." if d.status == "APPROVED"
                else f"Rejected: {d.rejection_reason}" if d.status == "REJECTED"
                else "Pending review by hospital/insurance verification team."
            )
        })

    return {
        "user_email": user.email,
        "total_documents": len(items),
        "documents": items,
        "admin_notice": "Document approval and rejection are strictly managed by human verification officers."
    }
