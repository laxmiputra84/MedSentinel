import hashlib
import random
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.document import UserDocument

class DocumentVerifier:
    @staticmethod
    def calculate_sha256(content_or_path: bytes | str | Path) -> str:
        """Calculates SHA-256 hash of file content or file at path."""
        hasher = hashlib.sha256()

        if isinstance(content_or_path, (str, Path)):
            p = Path(content_or_path)
            if not p.exists():
                return ""
            with open(p, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
        elif isinstance(content_or_path, bytes):
            hasher.update(content_or_path)

        return hasher.hexdigest()

    @staticmethod
    def generate_document_code() -> str:
        """Generates human-readable document code like DOC-2026-882910."""
        year = time.strftime("%Y")
        random_digits = random.randint(100000, 999999)
        return f"DOC-{year}-{random_digits}"

    @staticmethod
    def check_duplicate(db: Session, file_hash: str, exclude_doc_id: Optional[int] = None) -> Tuple[bool, Optional[UserDocument]]:
        """
        Searches DB for matching SHA-256 file hash.
        Returns (duplicate_detected, matching_document).
        """
        if not file_hash:
            return False, None

        query = db.query(UserDocument).filter(UserDocument.file_hash == file_hash)
        if exclude_doc_id:
            query = query.filter(UserDocument.id != exclude_doc_id)

        matching_doc = query.first()
        if matching_doc:
            return True, matching_doc

        return False, None

    @staticmethod
    def verify_document_integrity(db: Session, doc_id: int) -> Dict[str, Any]:
        """
        Re-computes the file hash from disk and compares against stored hash.
        Returns verification details.
        """
        doc = db.query(UserDocument).filter(UserDocument.id == doc_id).first()
        if not doc:
            return {
                "document_id": None,
                "verification_status": "NOT_FOUND",
                "valid": False,
                "message": "Document record does not exist",
            }

        # Resolve path robustly against UPLOAD_DIR and relative paths
        from app.core.config import settings
        clean_path = doc.file_path.lstrip("/")
        if Path(clean_path).is_absolute() and Path(clean_path).exists():
            disk_path = Path(clean_path)
        elif (Path(settings.UPLOAD_DIR) / Path(doc.file_path).name).exists():
            disk_path = Path(settings.UPLOAD_DIR) / Path(doc.file_path).name
        elif (Path("./") / clean_path).exists():
            disk_path = Path("./") / clean_path
        else:
            disk_path = Path(settings.UPLOAD_DIR) / Path(doc.file_path).name

        if not disk_path.exists():
            return {
                "document_id": doc.document_code or f"DOC-{doc.id}",
                "verification_status": "MISSING_FILE",
                "valid": False,
                "message": "Underlying storage file cannot be located",
            }

        current_hash = DocumentVerifier.calculate_sha256(disk_path)
        is_tamper_free = (current_hash == doc.file_hash)

        new_status = "VERIFIED" if is_tamper_free else "FLAGGED"
        doc.verification_status = new_status
        db.commit()

        return {
            "document_id": doc.document_code or f"DOC-{doc.id}",
            "hash": current_hash,
            "stored_hash": doc.file_hash,
            "verification_status": new_status,
            "valid": is_tamper_free,
            "message": "Cryptographic signature verified" if is_tamper_free else "Hash mismatch detected! Document may have been modified.",
        }
