from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.document_service import DocumentService
from app.models.document import UserDocument

class DocumentAgent:
    """
    Summarizes medical vault documents. Human verification remains authoritative.
    """
    @staticmethod
    async def get_user_documents_data(user_id: int, user_role: str, db: Session) -> Dict[str, Any]:
        if user_role in ["SUPER_ADMIN", "HOSPITAL_ADMIN"]:
            docs = db.query(UserDocument).order_by(UserDocument.upload_date.desc()).limit(10).all()
        else:
            docs = DocumentService.get_user_documents(db=db, user_id=user_id)

        items = []
        for d in docs:
            items.append({
                "document_id": d.id,
                "filename": d.filename,
                "doc_type": d.doc_type,
                "status": d.status,
                "upload_date": str(d.upload_date) if d.upload_date else None,
                "rejection_reason": d.rejection_reason
            })

        return {
            "documents": items,
            "total": len(items)
        }
