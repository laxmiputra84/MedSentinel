"""
MedSentinel Agentic Architecture — OCR Agent
Extracts raw text from PDF documents, scanned images, and structured clinical files
using multi-engine fallback (fitz, pdfplumber, pypdf, tesseract).
"""

from pathlib import Path
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, EscalationLevel
from app.agents.tools import extract_ocr_tool
from app.core.config import settings
from app.models.document import UserDocument


class OCRAgent(BaseAgent):
    """
    Specialized agent for OCR extraction and text digitization from medical files.
    """

    def __init__(self):
        super().__init__(
            name="ocr",
            role="Multi-Format OCR & Text Extraction",
            description="Digitizes PDF and image medical files into clean UTF-8 text with multi-engine OCR fallback.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        # 1. If text is already populated in state, skip re-extracting
        if state.extracted_text and len(state.extracted_text.strip()) > 0:
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={
                    "char_count": len(state.extracted_text),
                    "source": "pre_extracted_state",
                    "preview": state.extracted_text[:200]
                }
            )

        # 2. Determine file path to read
        target_path = None
        if state.file_path:
            p = Path(state.file_path)
            if p.exists():
                target_path = p
            else:
                # Check within uploads directory
                clean_name = p.name
                candidate = Path(settings.UPLOAD_DIR) / clean_name
                if candidate.exists():
                    target_path = candidate
                elif (Path("./") / state.file_path.lstrip("/")).exists():
                    target_path = Path("./") / state.file_path.lstrip("/")

        # 3. Check if document record exists in DB
        if not target_path and state.document_id and db:
            doc_rec = db.query(UserDocument).filter(UserDocument.id == state.document_id).first()
            if doc_rec:
                if doc_rec.ocr_extracted_text:
                    state.extracted_text = doc_rec.ocr_extracted_text
                    return AgentResult(
                        success=True,
                        agent_name=self.name,
                        data={"char_count": len(doc_rec.ocr_extracted_text), "source": "db_record"}
                    )
                # Resolve path from record
                clean = doc_rec.file_path.lstrip("/")
                c1 = Path(settings.UPLOAD_DIR) / doc_rec.filename if doc_rec.filename else None
                if c1 and c1.exists():
                    target_path = c1
                elif Path(clean).exists():
                    target_path = Path(clean)

        # 4. Check context
        if not target_path and context and context.get("file_path"):
            target_path = Path(context["file_path"])

        if not target_path or not target_path.exists():
            error_msg = f"OCR Error: Source file could not be located at '{state.file_path or state.document_id}'"
            state.escalation_required = True
            state.escalation_level = EscalationLevel.DOCTOR_REVIEW_REQUIRED
            state.escalation_reason = error_msg
            return AgentResult(
                success=False,
                agent_name=self.name,
                errors=[error_msg]
            )

        # 5. Execute OCR Tool
        res = await extract_ocr_tool(str(target_path))
        if not res["success"] or not res["text"]:
            err = res.get("error") or "OCR produced empty text output"
            state.escalation_required = True
            state.escalation_level = EscalationLevel.DOCTOR_REVIEW_REQUIRED
            state.escalation_reason = err
            return AgentResult(
                success=False,
                agent_name=self.name,
                errors=[err]
            )

        extracted_text = res["text"]
        state.extracted_text = extracted_text
        state.document_metadata["ocr_chars"] = res["char_count"]

        # Update DB record if present
        if db and state.document_id:
            doc = db.query(UserDocument).filter(UserDocument.id == state.document_id).first()
            if doc and not doc.ocr_extracted_text:
                doc.ocr_extracted_text = extracted_text[:10000]
                db.commit()

        finding = self.create_finding(
            title="Text Extraction Completed",
            description=f"Extracted {res['char_count']} characters using multi-layer OCR pipeline.",
            category="OCR",
            confidence=res["confidence"]
        )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "char_count": res["char_count"],
                "file_path": str(target_path),
                "confidence": res["confidence"]
            },
            findings=[finding]
        )
