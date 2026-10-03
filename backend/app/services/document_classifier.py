import re
from typing import Tuple

SUPPORTED_DOCUMENT_TYPES = [
    "Lab Report",
    "Prescription",
    "Medical Invoice",
    "Insurance Document",
    "Discharge Summary",
    "Radiology Report",
    "Scan Report",
    "Other",
]

# Clinical and administrative keyword dictionaries for classification
CLASSIFICATION_KEYWORDS = {
    "Lab Report": [
        "laboratory report", "lab report", "hematology", "biochemistry", "pathology",
        "complete blood count", "cbc", "hemoglobin", "wbc", "rbc", "platelet",
        "serum creatinine", "blood urea", "fasting blood sugar", "lipid panel",
        "crp", "c-reactive protein", "hba1c", "reference range", "biological reference",
        "specimen", "observed value", "urine routine", "culture & sensitivity", "sgot", "sgpt",
    ],
    "Prescription": [
        "prescription", "rx", "dr.", "doctor", "tablet", "capsule", "syrup",
        "dosage", "once daily", "twice daily", "bd", "tid", "od", "after food",
        "before food", "mg", "sig:", "consultation note", "take 1 tab",
    ],
    "Medical Invoice": [
        "invoice", "tax invoice", "bill", "hospital bill", "amount payable",
        "total charges", "pharmacy bill", "subtotal", "gstin", "receipt",
        "payment receipt", "room charges", "consultation fee", "net amount",
        "billing date", "payment mode", "balance due",
    ],
    "Insurance Document": [
        "insurance policy", "policy number", "sum insured", "claim form",
        "tpa", "third party administrator", "cashless authorization", "pre-auth",
        "insurance company", "health insurance", "coverage amount", "deductible",
        "co-pay", "premium receipt", "member id", "policyholder",
    ],
    "Discharge Summary": [
        "discharge summary", "discharge card", "date of admission", "date of discharge",
        "final diagnosis", "course in hospital", "condition at discharge", "treatment given",
        "operative procedure", "surgical summary", "follow up advice", "chief complaints",
        "admission date", "discharge instructions",
    ],
    "Radiology Report": [
        "radiology report", "x-ray", "x ray", "computed tomography", "ct scan",
        "magnetic resonance imaging", "mri", "ultrasonography", "usg", "mammogram",
        "technique:", "findings:", "impression:", "contrast enhanced", "axial slices",
        "coronal views", "no acute osseous abnormality", "attenuation",
    ],
    "Scan Report": [
        "scan report", "ecg", "electrocardiogram", "echocardiogram", "echo report",
        "eeg", "dexa scan", "pet scan", "sinus rhythm", "ejection fraction",
        "doppler ultrasound", "scan results",
    ],
}

class DocumentClassifier:
    @staticmethod
    def classify_text(text: str, filename: str = "") -> Tuple[str, float]:
        """
        Classifies document text and filename into one of the supported document types.
        Returns (document_type, confidence_score).
        """
        combined = f"{filename.lower()} {text.lower()}"
        if not text.strip() and not filename.strip():
            return "Other", 0.50

        scores: dict[str, int] = {doc_type: 0 for doc_type in CLASSIFICATION_KEYWORDS}

        for doc_type, keywords in CLASSIFICATION_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", combined):
                    # Higher weight if keyword matches filename
                    weight = 3 if kw in filename.lower() else 1
                    scores[doc_type] += weight

        best_type = max(scores, key=lambda k: scores[k])
        max_score = scores[best_type]

        if max_score == 0:
            return "Other", 0.55

        # Calculate normalized confidence between 0.65 and 0.98
        confidence = min(0.98, max(0.65, round(0.60 + (max_score * 0.05), 2)))

        return best_type, confidence
