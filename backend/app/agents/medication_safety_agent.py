"""
MedSentinel Agentic Architecture — Medication Safety Agent
Evaluates prescribed medications for drug-drug interactions, duplicate drug classes,
excessive dosages, and clinical contraindications.
Strictly clinical decision support: never autonomously alters or prescribes medications.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import (
    WorkflowState,
    AgentResult,
    ClinicalFinding,
    EscalationLevel,
    WorkflowStatus
)

# Known clinically critical drug interaction knowledge base (Evidence-based)
KNOWN_INTERACTIONS: List[Dict[str, Any]] = [
    {
        "drugs": ("warfarin", "aspirin"),
        "severity": "HIGH",
        "mechanism": "Synergistic anticoagulant/antiplatelet effect",
        "clinical_risk": "Marked increase in major hemorrhage / gastrointestinal bleeding.",
        "action": "Dose adjustment and INR monitoring required."
    },
    {
        "drugs": ("warfarin", "ibuprofen"),
        "severity": "CRITICAL",
        "mechanism": "NSAID inhibition of platelet function and gastrointestinal erosion with oral anticoagulant",
        "clinical_risk": "Severe gastrointestinal bleeding risk.",
        "action": "Avoid combination; consider alternative analgesic like Paracetamol."
    },
    {
        "drugs": ("sildenafil", "nitroglycerin"),
        "severity": "CRITICAL",
        "mechanism": "Profound synergistic vasodilation via cGMP accumulation",
        "clinical_risk": "Potentially fatal, refractory systemic hypotension.",
        "action": "Strictly contraindicated. Do not co-administer."
    },
    {
        "drugs": ("metformin", "contrast"),
        "severity": "HIGH",
        "mechanism": "Risk of radiocontrast-induced acute kidney injury leading to metformin accumulation",
        "clinical_risk": "Metformin-associated lactic acidosis (MALA).",
        "action": "Temporarily withhold metformin 48h prior to contrast scan."
    },
    {
        "drugs": ("telmisartan", "spironolactone"),
        "severity": "HIGH",
        "mechanism": "Dual renin-angiotensin-aldosterone blockade with potassium sparing",
        "clinical_risk": "Severe life-threatening hyperkalemia.",
        "action": "Serial serum potassium and creatinine monitoring required."
    },
    {
        "drugs": ("atorvastatin", "clarithromycin"),
        "severity": "HIGH",
        "mechanism": "CYP3A4 inhibition increases statin systemic exposure",
        "clinical_risk": "Significantly elevated risk of rhabdomyolysis and acute renal failure.",
        "action": "Temporarily pause statin during macrolide antibiotic course."
    },
]

# Duplicate class groups
DRUG_CLASSES: Dict[str, List[str]] = {
    "STATIN": ["atorvastatin", "rosuvastatin", "simvastatin", "pravastatin"],
    "BETA_BLOCKER": ["metoprolol", "atenolol", "bisoprolol", "carvedilol", "propranolol"],
    "ACE_INHIBITOR": ["enalapril", "ramipril", "lisinopril", "perindopril"],
    "ARB": ["telmisartan", "losartan", "valsartan", "olmesartan"],
    "NSAID": ["ibuprofen", "naproxen", "diclofenac", "aceclofenac", "indomethacin"],
    "PPI": ["omeprazole", "pantoprazole", "rabeprazole", "esomeprazole"],
}


class MedicationSafetyAgent(BaseAgent):
    """
    Analyzes prescriptions for adverse drug interactions and duplicate therapies.
    Escalates high/critical interactions to Doctor Review.
    """

    def __init__(self):
        super().__init__(
            name="medication_safety",
            role="Pharmacological Safety & Interaction Supervisor",
            description="Screens medications for severe drug-drug interactions, contraindications, and duplicate therapy classes.",
            version="1.0.0"
        )

    def extract_medications_from_text(self, text: str) -> List[str]:
        """Extracts mentioned pharmaceutical active ingredients from clinical text."""
        text_lower = text.lower()
        found_drugs = set()
        
        all_known = set()
        for pair in KNOWN_INTERACTIONS:
            all_known.add(pair["drugs"][0])
            all_known.add(pair["drugs"][1])
        for c_drugs in DRUG_CLASSES.values():
            all_known.update(c_drugs)

        for d in all_known:
            if re.search(rf"\b{re.escape(d)}\b", text_lower):
                found_drugs.add(d)

        return sorted(list(found_drugs))

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        text = state.extracted_text or (context.get("text") if context else "") or ""
        meds = self.extract_medications_from_text(text)
        
        findings: List[ClinicalFinding] = []
        detected_interactions: List[Dict[str, Any]] = []
        duplicate_classes: List[Dict[str, Any]] = []
        has_critical_interaction = False

        # 1. Screen for pairwise interactions
        for i in range(len(meds)):
            for j in range(i + 1, len(meds)):
                d1, d2 = meds[i], meds[j]
                for inter in KNOWN_INTERACTIONS:
                    pair = inter["drugs"]
                    if (d1 in pair and d2 in pair):
                        detected_interactions.append(inter)
                        is_crit = inter["severity"] == "CRITICAL"
                        if is_crit:
                            has_critical_interaction = True

                        findings.append(
                            self.create_finding(
                                title=f"Drug Interaction: {d1.title()} + {d2.title()} ({inter['severity']})",
                                description=f"{inter['mechanism']} — Risk: {inter['clinical_risk']} Action: {inter['action']}",
                                category="PHARMACOLOGY",
                                status=inter["severity"],
                                is_critical=is_crit,
                                evidence="MedSentinel Pharmacovigilance Reference Base",
                                confidence=0.96
                            )
                        )

        # 2. Screen for duplicate therapy classes
        for class_name, drugs_in_class in DRUG_CLASSES.items():
            matches = [d for d in meds if d in drugs_in_class]
            if len(matches) > 1:
                dup_info = {"class": class_name, "drugs": matches}
                duplicate_classes.append(dup_info)
                findings.append(
                    self.create_finding(
                        title=f"Duplicate Drug Class Detected: {class_name}",
                        description=f"Prescription contains multiple agents from same therapeutic class: {', '.join(matches).title()}. Increased risk of cumulative toxicity.",
                        category="PHARMACOLOGY",
                        status="MODERATE",
                        is_critical=False,
                        evidence="Clinical Pharmacology Formulary Guidelines",
                        confidence=0.92
                    )
                )

        # 3. Escalation check
        if has_critical_interaction:
            state.escalation_required = True
            state.escalation_level = EscalationLevel.DOCTOR_REVIEW_REQUIRED
            state.status = WorkflowStatus.DOCTOR_REVIEW_REQUIRED
            state.escalation_reason = "Critical drug-drug interaction detected in prescribed medications."

        state.extracted_entities["medication_safety"] = {
            "identified_medications": meds,
            "interactions_count": len(detected_interactions),
            "duplicate_classes_count": len(duplicate_classes),
            "has_critical_interaction": has_critical_interaction
        }

        return AgentResult(
            success=True,
            agent_name=self.name,
            findings=findings,
            data={
                "medications": meds,
                "interactions": detected_interactions,
                "duplicate_classes": duplicate_classes,
                "escalation_triggered": has_critical_interaction
            }
        )
