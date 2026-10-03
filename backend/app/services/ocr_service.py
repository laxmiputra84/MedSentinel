import os
from pathlib import Path
from typing import Optional

class OCRService:
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """
        Extracts raw text from PDF documents or images using available libraries
        (fitz / pdfplumber / pypdf for PDF, pytesseract / PIL for images).
        """
        path = Path(file_path)
        if not path.exists():
            return ""

        ext = path.suffix.lower()
        extracted_text = ""

        if ext == ".pdf":
            extracted_text = OCRService._extract_from_pdf(path)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
            extracted_text = OCRService._extract_from_image(path)
        elif ext in [".txt", ".csv", ".json"]:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    extracted_text = f.read()
            except Exception:
                pass

        return extracted_text.strip()

    @staticmethod
    def _extract_from_pdf(path: Path) -> str:
        text_content = []

        # 1. Try PyMuPDF (fitz) - very fast & accurate
        try:
            import fitz  # type: ignore
            doc = fitz.open(path)
            for page in doc:
                text_content.append(page.get_text() or "")
            doc.close()
            combined = "\n".join(text_content).strip()
            if combined:
                return combined
        except Exception:
            pass

        # 2. Try pdfplumber
        try:
            import pdfplumber  # type: ignore
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_content.append(extracted)
            combined = "\n".join(text_content).strip()
            if combined:
                return combined
        except Exception:
            pass

        # 3. Try pypdf
        try:
            from pypdf import PdfReader  # type: ignore
            reader = PdfReader(str(path))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text_content.append(t)
            combined = "\n".join(text_content).strip()
            if combined:
                return combined
        except Exception:
            pass

        return ""

    @staticmethod
    def _extract_from_image(path: Path) -> str:
        try:
            from PIL import Image  # type: ignore
            import pytesseract  # type: ignore

            img = Image.open(path)
            # Run pytesseract
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception:
            # Fallback if tesseract binary is not installed in OS path
            return ""
