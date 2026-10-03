from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document import UserDocument

class DocumentService:
    @staticmethod
    def get_user_documents(db: Session, user_id: int) -> List[UserDocument]:
        return db.query(UserDocument).filter(
            UserDocument.user_id == user_id
        ).order_by(UserDocument.upload_date.desc()).all()

    @staticmethod
    def get_document_by_id(db: Session, doc_id: int, user_id: Optional[int] = None) -> Optional[UserDocument]:
        query = db.query(UserDocument).filter(UserDocument.id == doc_id)
        if user_id:
            query = query.filter(UserDocument.user_id == user_id)
        return query.first()
