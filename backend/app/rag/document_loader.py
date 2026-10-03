import os
import json
from typing import List, Dict, Any, Optional
from app.rag.text_extractor import TextExtractor

class DocumentLoader:
    @staticmethod
    def load_dataset_content(file_path: str, dataset_name: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Loads document file from path, extracts text, and partitions into logical document units.
        Returns a list of document dicts with 'title', 'content', and 'metadata'.
        """
        raw_text = TextExtractor.extract_text(file_path, file_type)
        if not raw_text:
            return []

        # If document contains clear page markers, split by pages/sections
        if "--- Page " in raw_text:
            pages = raw_text.split("--- Page ")
            documents = []
            for p in pages:
                if not p.strip():
                    continue
                lines = p.strip().split("\n", 1)
                page_num = lines[0].replace("---", "").strip()
                page_content = lines[1].strip() if len(lines) > 1 else lines[0]
                documents.append({
                    "title": f"{dataset_name} — Section/Page {page_num}",
                    "content": page_content,
                    "metadata": {"source_page": page_num, "dataset_name": dataset_name}
                })
            return documents

        # If spreadsheet/CSV has sheet partitions
        if "=== Sheet:" in raw_text:
            sheets = raw_text.split("=== Sheet:")
            documents = []
            for s in sheets:
                if not s.strip():
                    continue
                lines = s.strip().split("\n", 1)
                sheet_title = lines[0].replace("===", "").strip()
                sheet_content = lines[1].strip() if len(lines) > 1 else lines[0]
                documents.append({
                    "title": f"{dataset_name} — Sheet: {sheet_title}",
                    "content": sheet_content,
                    "metadata": {"sheet_name": sheet_title, "dataset_name": dataset_name}
                })
            return documents

        # Single monolithic document
        return [{
            "title": dataset_name,
            "content": raw_text,
            "metadata": {"dataset_name": dataset_name}
        }]
