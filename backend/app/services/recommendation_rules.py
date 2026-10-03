"""
MedSentinel Recommendation Rules & Clinical Guardrail Configurations
Decoupled rule sets, document association maps, and clinical advisory templates.
"""

RELATED_DOCUMENT_RULES = {
    "Lab Report": [
        "Previous Lab Report",
        "Prescription",
        "Doctor Consultation Record",
    ],
    "Prescription": [
        "Lab Report",
        "Doctor Consultation Record",
        "Medical Invoice",
    ],
    "Medical Invoice": [
        "Prescription",
        "Lab Report",
        "Insurance Claim",
    ],
    "Insurance Document": [
        "Medical Invoice",
        "Supporting Medical Record",
    ],
    "Discharge Summary": [
        "Medical Invoice",
        "Prescription",
        "Lab Report",
    ],
    "Radiology Report": [
        "Prescription",
        "Doctor Consultation Record",
        "Previous Scan Report",
    ],
    "Scan Report": [
        "Prescription",
        "Radiology Report",
        "Doctor Consultation Record",
    ],
    "Other": [
        "Supporting Medical Record",
        "Doctor Consultation Record",
    ]
}

# Monitored tests for longitudinal trend review
MONITORED_LAB_TESTS = [
    "Hemoglobin",
    "WBC",
    "Platelets",
    "Blood Glucose",
    "Fasting Blood Glucose",
    "HbA1c",
    "Serum Creatinine",
    "Creatinine",
    "CRP",
    "Potassium",
]

# Baseline weights for hybrid recommendation scoring
SCORE_WEIGHTS = {
    "RULE_SCORE": 0.40,
    "TREND_SCORE": 0.30,
    "CONTENT_SIMILARITY": 0.15,
    "DATA_QUALITY": 0.15,
}

# Recommendation Priority Thresholds
PRIORITY_THRESHOLDS = {
    "HIGH": 0.85,
    "MEDIUM": 0.65,
    "LOW": 0.0,
}

# Non-assertive advisory disclaimer included with recommendations
RECOMMENDATION_DISCLAIMER = (
    "MedSentinel recommendations are informational and administrative suggestions. "
    "They do not provide a medical diagnosis, prescription, or clinical certainty. "
    "Always consult a qualified healthcare professional regarding health concerns."
)
