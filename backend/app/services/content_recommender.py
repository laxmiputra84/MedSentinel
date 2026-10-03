"""
MedSentinel Content-Based Recommendation Engine
Uses TF-IDF feature extraction & Cosine Similarity over document metadata,
detected clinical tests, OCR text snippets, and medical classification keywords.
Includes graceful fallback to token overlap if machine learning library fails.
"""

import re
import math
from typing import List, Dict, Any, Optional

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class ContentRecommender:
    """Content-based similarity engine for medical documents and clinical records."""

    @staticmethod
    def _extract_document_features(doc: Any) -> str:
        """Combine document type, filename, OCR text, and AI classification into a feature string."""
        parts = []
        if getattr(doc, "doc_type", None):
            parts.append(str(doc.doc_type))
        if getattr(doc, "ai_classification", None):
            parts.append(str(doc.ai_classification))
        if getattr(doc, "original_name", None):
            clean_name = re.sub(r"[_\-.]", " ", str(doc.original_name))
            parts.append(clean_name)
        if getattr(doc, "ocr_extracted_text", None):
            parts.append(str(doc.ocr_extracted_text)[:1000])
        
        # If document has associated lab results
        if hasattr(doc, "lab_results") and doc.lab_results:
            tests = [lr.test_name for lr in doc.lab_results if hasattr(lr, "test_name")]
            parts.extend(tests)

        return " ".join(parts).lower()

    @classmethod
    def compute_similarity(cls, text_a: str, text_b: str) -> float:
        """Compute cosine similarity between two feature texts with fallback."""
        if not text_a.strip() or not text_b.strip():
            return 0.0

        if SKLEARN_AVAILABLE:
            try:
                vectorizer = TfidfVectorizer(stop_words="english", max_features=100)
                tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
                sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                return float(sim)
            except Exception:
                pass

        # Robust pure-Python token overlap / Jaccard-Cosine fallback
        tokens_a = set(re.findall(r"\w+", text_a.lower()))
        tokens_b = set(re.findall(r"\w+", text_b.lower()))
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = len(tokens_a.intersection(tokens_b))
        denominator = math.sqrt(len(tokens_a) * len(tokens_b))
        return float(intersection / denominator) if denominator > 0 else 0.0

    @classmethod
    def get_related_content_scores(cls, target_doc: Any, candidate_docs: List[Any]) -> List[Dict[str, Any]]:
        """Return candidate documents ranked by content similarity to the target document."""
        if not candidate_docs:
            return []

        target_features = cls._extract_document_features(target_doc)
        results = []

        for c_doc in candidate_docs:
            if c_doc.id == target_doc.id:
                continue
            c_features = cls._extract_document_features(c_doc)
            sim_score = cls.compute_similarity(target_features, c_features)
            results.append({
                "document_id": c_doc.id,
                "document_code": getattr(c_doc, "document_code", None),
                "original_name": c_doc.original_name,
                "doc_type": c_doc.doc_type,
                "similarity": round(sim_score, 4),
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results
