"""
MedSentinel Agentic Architecture — Symptom / Clinical Analysis Agent
Analyzes symptoms, clinical notes, and medication context to produce
structured decision-support observations while strictly avoiding definitive diagnosis.
"""

import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding


# Clinical observation patterns
SYMPTOM_PATTERNS = {
    "Fatigue & Weakness": [r"\bfatigue\b", r"\btiredness\b", r"\blethargy\b", r"\bweakness\b", r"\basthenia\b"],
    "Fever & Chills": [r"\bfever\b", r"\bpyrexia\b", r"\bchills\b", r"\belevated temperature\b", r"\bshivering\b"],
    "Dyspnea & Respiratory": [r"\bdyspnea\b", r"\bshortness of breath\b", r"\bcough\b", r"\bwheezing\b", r"\bchest congestion\b"],
    "Chest Pain & Cardiovascular": [r"\bchest pain\b", r"\bangina\b", r"\bpalpitations\b", r"\btachycardia\b"],
    "Gastrointestinal Symptoms": [r"\bnausea\b", r"\bvomiting\b", r"\babdominal pain\b", r"\bdiarrhea\b", r"\bconstipation\b"],
    "Headache & Neurological": [r"\bheadache\b", r"\bcephalalgia\b", r"\bdizziness\b", r"\bvertigo\b", r"\bmigraine\b"],
    "Glycemic Variation": [r"\bpolyuria\b", r"\bpolydipsia\b", r"\bhyperglycemia\b", r"\bhypoglycemia\b", r"\bhigh blood sugar\b"],
}


class SymptomClinicalAgent(BaseAgent):
    """
    Specialized agent for structured clinical observation and non-diagnostic symptom pattern analysis.
    """

    def __init__(self):
        super().__init__(
            name="symptom_clinical",
            role="Clinical Observation & Symptom Analysis",
            description="Identifies documented symptom patterns and contextual correlations using cautious decision-support language.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        combined_text = (state.extracted_text or "") + " " + (context.get("clinical_notes", "") if context else "")
        detected_symptoms: List[str] = []
        findings: List[ClinicalFinding] = []

        # 1. Scan for symptom clusters
        for category, patterns in SYMPTOM_PATTERNS.items():
            for p in patterns:
                if re.search(p, combined_text, re.IGNORECASE):
                    if category not in detected_symptoms:
                        detected_symptoms.append(category)
                    break

        # 2. Correlate with abnormal lab results in state
        abnormal_labs = [t for t in state.lab_results if t.get("status") in ["LOW", "HIGH", "CRITICAL"]]

        for sym in detected_symptoms:
            correlations = []
            if "Fatigue" in sym:
                anemia_markers = [t["name"] for t in abnormal_labs if t["name"] in ["Hemoglobin", "RBC Count", "PCV"]]
                if anemia_markers:
                    correlations.append(f"documented variation in {', '.join(anemia_markers)}")
            if "Fever" in sym:
                inf_markers = [t["name"] for t in abnormal_labs if t["name"] in ["WBC", "Neutrophils", "CRP"]]
                if inf_markers:
                    correlations.append(f"immune response markers ({', '.join(inf_markers)})")
            if "Glycemic" in sym:
                sugar_markers = [t["name"] for t in abnormal_labs if t["name"] in ["Fasting Blood Glucose", "HbA1c"]]
                if sugar_markers:
                    correlations.append(f"glycemic indicators ({', '.join(sugar_markers)})")

            corr_text = f" Observed finding may correlate with {'; '.join(correlations)}." if correlations else ""
            desc = (
                f"Symptom cluster '{sym}' identified from documented clinical context.{corr_text} "
                "Further clinical evaluation by an attending healthcare provider is recommended."
            )

            findings.append(
                self.create_finding(
                    title=f"Clinical Observation: {sym}",
                    description=desc,
                    category="SYMPTOM_ANALYSIS",
                    status="MODERATE" if correlations else "NORMAL",
                    confidence=0.88
                )
            )

        # 3. If no symptoms detected in raw text
        if not detected_symptoms:
            if abnormal_labs:
                findings.append(
                    self.create_finding(
                        title="Subclinical Laboratory Findings",
                        description=(
                            f"No overt clinical symptom clusters were documented in the text, though {len(abnormal_labs)} "
                            "abnormal laboratory parameters were detected. Clinical correlation is advised."
                        ),
                        category="SYMPTOM_ANALYSIS",
                        status="NORMAL",
                        confidence=0.85
                    )
                )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "detected_symptoms": detected_symptoms,
                "symptoms_count": len(detected_symptoms),
                "abnormal_labs_correlated": len(abnormal_labs),
            },
            findings=findings
        )
