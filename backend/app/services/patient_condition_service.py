"""
MedSentinel Patient Condition Evidence Extraction Service
Extracts medical conditions and recommended hospital specializations strictly from
actual patient records, laboratory biomarkers, pharmacotherapy context, and clinical documentation.

Strict Healthcare AI Rules:
1. NEVER randomly assign or guess a medical condition.
2. Every detected condition MUST contain:
   - condition_name / category
   - supporting_evidence (actual parameters, values, medications, documented findings)
   - confidence score
   - risk_level
   - source_data
   - recommended_specialties
3. If evidence is insufficient, return an explicit INSUFFICIENT_EVIDENCE state.
"""

import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class DetectedCondition(BaseModel):
    condition_name: str
    category: str  # ENDOCRINOLOGY, CARDIOLOGY, NEPHROLOGY, PULMONOLOGY, ONCOLOGY, NEUROLOGY, GASTROENTEROLOGY, HEMATOLOGY, ORTHOPEDICS, GENERAL_MEDICINE
    supporting_evidence: List[str]
    confidence: float = 0.85
    risk_level: str = "MODERATE"  # LOW, MODERATE, HIGH, CRITICAL
    source_data: str = "Laboratory Biomarkers"
    recommended_specialties: List[str]
    requires_icu: bool = False


class PatientConditionAnalysisResult(BaseModel):
    has_sufficient_evidence: bool = False
    primary_condition: Optional[DetectedCondition] = None
    all_conditions: List[DetectedCondition] = Field(default_factory=list)
    recommended_specialties: List[str] = Field(default_factory=list)
    requires_icu_or_critical_care: bool = False
    clinical_summary: str = ""


class PatientConditionService:
    """
    Evidence-based clinical condition detector that maps extracted patient data
    to appropriate medical specialties for hospital matching.
    """

    @staticmethod
    def extract_patient_condition_evidence(
        extracted_text: Optional[str] = None,
        lab_results: Optional[List[Dict[str, Any]]] = None,
        clinical_findings: Optional[List[Any]] = None,
        clinical_notes: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> PatientConditionAnalysisResult:
        """
        Analyzes multimodal patient evidence (text, lab items, findings, key-value data) without hallucination or random guessing.
        """
        raw_text = ((extracted_text or "") + " " + (clinical_notes or "")).strip()
        text_lower = raw_text.lower()
        labs = list(lab_results or [])
        findings = clinical_findings or []

        # Ingest key-value extracted_data if provided
        if extracted_data and isinstance(extracted_data, dict):
            for k, v in extracted_data.items():
                if isinstance(v, (int, float, str)):
                    labs.append({"name": str(k).replace("_", " "), "value": v, "status": "OBSERVED"})

        detected_conditions: List[DetectedCondition] = []
        all_specialties: Set[str] = set()
        overall_icu = False

        # =========================================================================
        # 1. DIABETES & ENDOCRINOLOGY
        # =========================================================================
        diab_evidence: List[str] = []
        diab_risk = "MODERATE"
        diab_conf = 0.85

        for lab in labs:
            name = (lab.get("name") or lab.get("test_name") or "").strip().lower()
            val = lab.get("value") or lab.get("observed_value")
            status = (lab.get("status") or "").upper()

            if "hba1c" in name and val is not None:
                try:
                    num_val = float(val)
                    if num_val >= 6.5 or status in ["HIGH", "CRITICAL"]:
                        diab_evidence.append(f"Elevated HbA1c ({num_val}%; ref: 4.0 - 5.6%) [Diagnostic for Diabetes]")
                        diab_conf = max(diab_conf, 0.96)
                        if num_val >= 9.0:
                            diab_risk = "HIGH"
                    elif num_val >= 5.7:
                        diab_evidence.append(f"Pre-diabetic Range HbA1c ({num_val}%; ref: 4.0 - 5.6%)")
                except (ValueError, TypeError):
                    pass

            if any(k in name for k in ["glucose", "blood sugar", "fasting blood sugar", "postprandial", "fbs", "ppbs"]) and val is not None:
                try:
                    num_val = float(val)
                    if num_val >= 126.0 or status in ["HIGH", "CRITICAL"]:
                        diab_evidence.append(f"Elevated Blood Glucose ({num_val} mg/dL; ref: 70 - 99 mg/dL)")
                        diab_conf = max(diab_conf, 0.94)
                        if num_val >= 250.0 or status == "CRITICAL":
                            diab_risk = "CRITICAL"
                except (ValueError, TypeError):
                    pass

        # Medication Evidence
        diab_meds = ["metformin", "insulin", "glimepiride", "gliclazide", "sitagliptin", "vildagliptin", "dapagliflozin", "empagliflozin", "pioglitazone"]
        for med in diab_meds:
            if re.search(rf"\b{re.escape(med)}\b", text_lower):
                diab_evidence.append(f"Documented prescription of antidiabetic pharmacotherapy ({med.title()})")
                diab_conf = max(diab_conf, 0.92)

        # Keyword Evidence
        diab_keywords = ["type 2 diabetes", "type 1 diabetes", "diabetes mellitus", "hyperglycemia", "diabetic ketoacidosis", "t2dm", "t1dm"]
        for kw in diab_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                diab_evidence.append(f"Clinical documentation notes: '{kw.title()}'")
                diab_conf = max(diab_conf, 0.90)

        if diab_evidence:
            specs = ["Endocrinology", "General Medicine"]
            detected_conditions.append(
                DetectedCondition(
                    condition_name="Diabetes Mellitus / Glycemic Variance",
                    category="ENDOCRINOLOGY",
                    supporting_evidence=diab_evidence,
                    confidence=diab_conf,
                    risk_level=diab_risk,
                    source_data="Laboratory Biomarkers & Clinical Records",
                    recommended_specialties=specs,
                    requires_icu=diab_risk == "CRITICAL",
                )
            )
            all_specialties.update(specs)
            if diab_risk == "CRITICAL":
                overall_icu = True

        # =========================================================================
        # 2. CARDIOVASCULAR & CARDIOLOGY
        # =========================================================================
        cardiac_evidence: List[str] = []
        cardiac_risk = "MODERATE"
        cardiac_conf = 0.85
        cardiac_icu = False

        for lab in labs:
            name = (lab.get("name") or lab.get("test_name") or "").strip().lower()
            val = lab.get("value") or lab.get("observed_value")
            status = (lab.get("status") or "").upper()

            if any(k in name for k in ["troponin", "trop i", "trop t", "trop-i", "trop-t"]) and val is not None:
                try:
                    num_val = float(val)
                    if num_val >= 0.04 or status in ["HIGH", "CRITICAL"]:
                        cardiac_evidence.append(f"Elevated Cardiac Troponin ({num_val} ng/mL; ref: < 0.04 ng/mL) [Myocardial Injury Marker]")
                        cardiac_conf = 0.98
                        cardiac_risk = "CRITICAL"
                        cardiac_icu = True
                except (ValueError, TypeError):
                    pass

            if "cholesterol" in name and "total" in name and val is not None:
                try:
                    num_val = float(val)
                    if num_val >= 200.0 or status in ["HIGH", "CRITICAL"]:
                        cardiac_evidence.append(f"Hypercholesterolemia ({num_val} mg/dL; ref: < 200 mg/dL)")
                except (ValueError, TypeError):
                    pass

            if "ldl" in name and val is not None:
                try:
                    num_val = float(val)
                    if num_val >= 130.0 or status in ["HIGH", "CRITICAL"]:
                        cardiac_evidence.append(f"Elevated LDL Cholesterol ({num_val} mg/dL; ref: < 100 mg/dL)")
                except (ValueError, TypeError):
                    pass

            if any(k in name for k in ["bnp", "nt-probnp", "ck-mb"]) and status in ["HIGH", "CRITICAL"]:
                cardiac_evidence.append(f"Elevated cardiac stress biomarker: {name.upper()}")
                cardiac_risk = "HIGH"

        cardiac_meds = ["atorvastatin", "rosuvastatin", "telmisartan", "amlodipine", "clopidogrel", "aspirin", "metoprolol", "bisoprolol", "digoxin", "nitroglycerin"]
        for med in cardiac_meds:
            if re.search(rf"\b{re.escape(med)}\b", text_lower):
                cardiac_evidence.append(f"Documented cardiovascular medication ({med.title()})")
                cardiac_conf = max(cardiac_conf, 0.90)

        cardiac_keywords = ["coronary artery disease", "myocardial infarction", "angina", "hypertension", "heart failure", "arrhythmia", "ischemic heart disease", "cardiology", "cardiac"]
        for kw in cardiac_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                cardiac_evidence.append(f"Clinical documentation notes: '{kw.title()}'")
                cardiac_conf = max(cardiac_conf, 0.90)

        if cardiac_evidence:
            specs = ["Cardiology", "Cardiac Surgery", "Multi-speciality"]
            detected_conditions.append(
                DetectedCondition(
                    condition_name="Cardiovascular / Cardiac Condition",
                    category="CARDIOLOGY",
                    supporting_evidence=cardiac_evidence,
                    confidence=cardiac_conf,
                    risk_level=cardiac_risk,
                    source_data="Cardiac Biomarkers & Clinical Records",
                    recommended_specialties=specs,
                    requires_icu=cardiac_icu,
                )
            )
            all_specialties.update(specs)
            if cardiac_icu:
                overall_icu = True

        # =========================================================================
        # 3. RENAL & NEPHROLOGY
        # =========================================================================
        renal_evidence: List[str] = []
        renal_risk = "MODERATE"
        renal_conf = 0.85
        renal_icu = False

        for lab in labs:
            name = (lab.get("name") or lab.get("test_name") or "").strip().lower()
            val = lab.get("value") or lab.get("observed_value")
            status = (lab.get("status") or "").upper()

            if "creatinine" in name and val is not None:
                try:
                    num_val = float(val)
                    if num_val >= 1.4 or status in ["HIGH", "CRITICAL"]:
                        renal_evidence.append(f"Elevated Serum Creatinine ({num_val} mg/dL; ref: 0.7 - 1.3 mg/dL) [Impaired Renal Clearance]")
                        renal_conf = 0.96
                        if num_val >= 3.0 or status == "CRITICAL":
                            renal_risk = "CRITICAL"
                            renal_icu = True
                        elif num_val >= 2.0:
                            renal_risk = "HIGH"
                except (ValueError, TypeError):
                    pass

            if any(k in name for k in ["bun", "blood urea", "urea"]) and val is not None:
                try:
                    num_val = float(val)
                    if num_val >= 25.0 or status in ["HIGH", "CRITICAL"]:
                        renal_evidence.append(f"Elevated Blood Urea Nitrogen ({num_val} mg/dL; ref: 7 - 20 mg/dL)")
                except (ValueError, TypeError):
                    pass

            if "egfr" in name and val is not None:
                try:
                    num_val = float(val)
                    if num_val <= 60.0:
                        renal_evidence.append(f"Reduced Estimated GFR ({num_val} mL/min/1.73m²; ref: > 90 mL/min)")
                        renal_risk = "HIGH"
                except (ValueError, TypeError):
                    pass

        renal_keywords = ["chronic kidney disease", "renal failure", "nephrology", "dialysis", "hemodialysis", "nephritis", "acute kidney injury", "ckd"]
        for kw in renal_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                renal_evidence.append(f"Clinical documentation notes: '{kw.title()}'")
                renal_conf = max(renal_conf, 0.92)

        if renal_evidence:
            specs = ["Nephrology", "Multi-speciality"]
            detected_conditions.append(
                DetectedCondition(
                    condition_name="Renal / Nephrological Variance",
                    category="NEPHROLOGY",
                    supporting_evidence=renal_evidence,
                    confidence=renal_conf,
                    risk_level=renal_risk,
                    source_data="Renal Panel & Clinical Records",
                    recommended_specialties=specs,
                    requires_icu=renal_icu,
                )
            )
            all_specialties.update(specs)
            if renal_icu:
                overall_icu = True

        # =========================================================================
        # 4. ONCOLOGY & MALIGNANCY
        # =========================================================================
        onco_evidence: List[str] = []
        onco_risk = "HIGH"
        onco_conf = 0.90

        for lab in labs:
            name = (lab.get("name") or lab.get("test_name") or "").strip().lower()
            val = lab.get("value") or lab.get("observed_value")
            status = (lab.get("status") or "").upper()

            if "psa" in name and val is not None:
                try:
                    num_val = float(val)
                    if num_val >= 4.0 or status in ["HIGH", "CRITICAL"]:
                        onco_evidence.append(f"Elevated Total PSA ({num_val} ng/mL; ref: < 4.0 ng/mL) [Prostatic Biomarker]")
                        onco_conf = 0.94
                except (ValueError, TypeError):
                    pass

            if any(k in name for k in ["ca-125", "cea", "afp", "ca 19-9"]) and status in ["HIGH", "CRITICAL"]:
                onco_evidence.append(f"Elevated onco-biomarker ({name.upper()})")

        onco_keywords = ["cancer", "oncology", "carcinoma", "malignancy", "tumor", "chemotherapy", "radiation therapy", "biopsy positive", "lymphoma", "leukemia", "sarcoma"]
        for kw in onco_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                onco_evidence.append(f"Clinical documentation notes: '{kw.title()}'")
                onco_conf = max(onco_conf, 0.94)

        if onco_evidence:
            specs = ["Oncology", "Surgical Oncology", "Multi-speciality"]
            detected_conditions.append(
                DetectedCondition(
                    condition_name="Oncological / Malignancy Risk",
                    category="ONCOLOGY",
                    supporting_evidence=onco_evidence,
                    confidence=onco_conf,
                    risk_level=onco_risk,
                    source_data="Oncology Markers & Pathology Context",
                    recommended_specialties=specs,
                    requires_icu=False,
                )
            )
            all_specialties.update(specs)

        # =========================================================================
        # 5. HEMATOLOGY & SEVERE ANEMIA
        # =========================================================================
        hem_evidence: List[str] = []
        hem_risk = "MODERATE"
        hem_conf = 0.85
        hem_icu = False

        for lab in labs:
            name = (lab.get("name") or lab.get("test_name") or "").strip().lower()
            val = lab.get("value") or lab.get("observed_value")
            status = (lab.get("status") or "").upper()

            if "hemoglobin" in name and val is not None:
                try:
                    num_val = float(val)
                    if num_val <= 7.0 or status == "CRITICAL":
                        hem_evidence.append(f"Severe Critical Anemia: Hemoglobin {num_val} g/dL (ref: 12.0 - 17.5 g/dL) [Panic Value]")
                        hem_risk = "CRITICAL"
                        hem_conf = 0.98
                        hem_icu = True
                    elif num_val <= 10.0 or status == "LOW":
                        hem_evidence.append(f"Documented Anemia: Hemoglobin {num_val} g/dL (ref: 12.0 - 17.5 g/dL)")
                        hem_risk = "MODERATE"
                except (ValueError, TypeError):
                    pass

            if "platelet" in name and val is not None:
                try:
                    num_val = float(val)
                    if num_val <= 30000 or status == "CRITICAL":
                        hem_evidence.append(f"Profound Thrombocytopenia: Platelet Count {int(num_val):,} /uL (ref: 150,000 - 450,000 /uL) [Bleeding Risk]")
                        hem_risk = "CRITICAL"
                        hem_conf = 0.98
                        hem_icu = True
                    elif num_val <= 100000 or status == "LOW":
                        hem_evidence.append(f"Low Platelet Count: {int(num_val):,} /uL (ref: 150,000 - 450,000 /uL)")
                except (ValueError, TypeError):
                    pass

        if hem_evidence:
            specs = ["Hematology", "General Medicine", "Oncology"]
            detected_conditions.append(
                DetectedCondition(
                    condition_name="Hematological Disorder / Severe Cytopenia",
                    category="HEMATOLOGY",
                    supporting_evidence=hem_evidence,
                    confidence=hem_conf,
                    risk_level=hem_risk,
                    source_data="Complete Blood Count & Hematology Panel",
                    recommended_specialties=specs,
                    requires_icu=hem_icu,
                )
            )
            all_specialties.update(specs)
            if hem_icu:
                overall_icu = True

        # =========================================================================
        # 6. NEUROLOGY & NEUROSURGERY
        # =========================================================================
        neuro_evidence: List[str] = []
        neuro_risk = "MODERATE"
        neuro_conf = 0.85
        neuro_icu = False

        neuro_keywords = ["neurology", "stroke", "ischemic stroke", "hemiparesis", "seizure", "epilepsy", "parkinson", "neuropathy", "multiple sclerosis", "neurosurgery"]
        for kw in neuro_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                neuro_evidence.append(f"Clinical documentation notes: '{kw.title()}'")
                neuro_conf = 0.92
                if "stroke" in kw or "seizure" in kw:
                    neuro_risk = "HIGH"

        neuro_meds = ["levodopa", "donepezil", "carbamazepine", "sodium valproate", "phenytoin", "levetiracetam", "gabapentin"]
        for med in neuro_meds:
            if re.search(rf"\b{re.escape(med)}\b", text_lower):
                neuro_evidence.append(f"Documented neurological medication ({med.title()})")
                neuro_conf = max(neuro_conf, 0.90)

        if neuro_evidence:
            specs = ["Neurology", "Neurosurgery", "Multi-speciality"]
            detected_conditions.append(
                DetectedCondition(
                    condition_name="Neurological Condition",
                    category="NEUROLOGY",
                    supporting_evidence=neuro_evidence,
                    confidence=neuro_conf,
                    risk_level=neuro_risk,
                    source_data="Neurological Documentation & Pharmacotherapy",
                    recommended_specialties=specs,
                    requires_icu=neuro_icu,
                )
            )
            all_specialties.update(specs)

        # =========================================================================
        # 7. PULMONOLOGY & RESPIRATORY
        # =========================================================================
        pulmo_evidence: List[str] = []
        pulmo_risk = "MODERATE"
        pulmo_conf = 0.85

        pulmo_keywords = ["pulmonology", "asthma", "copd", "pneumonia", "bronchitis", "respiratory failure", "tuberculosis", "dyspnea"]
        for kw in pulmo_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                pulmo_evidence.append(f"Clinical documentation notes: '{kw.title()}'")
                pulmo_conf = 0.90
                if "respiratory failure" in kw:
                    pulmo_risk = "CRITICAL"
                    overall_icu = True

        pulmo_meds = ["budesonide", "formoterol", "salbutamol", "ipratropium", "montelukast", "theophylline"]
        for med in pulmo_meds:
            if re.search(rf"\b{re.escape(med)}\b", text_lower):
                pulmo_evidence.append(f"Documented respiratory inhaler/bronchodilator ({med.title()})")
                pulmo_conf = max(pulmo_conf, 0.90)

        if pulmo_evidence:
            specs = ["Pulmonology", "General Medicine"]
            detected_conditions.append(
                DetectedCondition(
                    condition_name="Respiratory / Pulmonary Condition",
                    category="PULMONOLOGY",
                    supporting_evidence=pulmo_evidence,
                    confidence=pulmo_conf,
                    risk_level=pulmo_risk,
                    source_data="Pulmonary Documentation & Pharmacotherapy",
                    recommended_specialties=specs,
                    requires_icu=pulmo_risk == "CRITICAL",
                )
            )
            all_specialties.update(specs)

        # =========================================================================
        # 8. GASTROENTEROLOGY & HEPATOLOGY
        # =========================================================================
        gastro_evidence: List[str] = []
        gastro_risk = "MODERATE"
        gastro_conf = 0.85

        for lab in labs:
            name = (lab.get("name") or lab.get("test_name") or "").strip().lower()
            val = lab.get("value") or lab.get("observed_value")
            status = (lab.get("status") or "").upper()

            if "bilirubin" in name and val is not None:
                try:
                    num_val = float(val)
                    if num_val >= 2.0 or status in ["HIGH", "CRITICAL"]:
                        gastro_evidence.append(f"Elevated Total Bilirubin ({num_val} mg/dL; ref: 0.2 - 1.2 mg/dL) [Hepatic Dysfunction]")
                        gastro_conf = 0.94
                except (ValueError, TypeError):
                    pass

            if any(k in name for k in ["sgot", "ast", "sgpt", "alt"]) and status in ["HIGH", "CRITICAL"]:
                gastro_evidence.append(f"Elevated transaminases ({name.upper()}) [Hepatocellular Inflammation]")

        gastro_keywords = ["gastroenterology", "hepatology", "hepatitis", "cirrhosis", "liver failure", "pancreatitis", "endoscopy", "cholecystitis"]
        for kw in gastro_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                gastro_evidence.append(f"Clinical documentation notes: '{kw.title()}'")
                gastro_conf = max(gastro_conf, 0.90)

        if gastro_evidence:
            specs = ["Gastroenterology", "Hepatology", "Multi-speciality"]
            detected_conditions.append(
                DetectedCondition(
                    condition_name="Gastroenterology & Hepatic Condition",
                    category="GASTROENTEROLOGY",
                    supporting_evidence=gastro_evidence,
                    confidence=gastro_conf,
                    risk_level=gastro_risk,
                    source_data="Liver Function Panel & Clinical Records",
                    recommended_specialties=specs,
                    requires_icu=False,
                )
            )
            all_specialties.update(specs)

        # =========================================================================
        # 9. ORTHOPEDICS
        # =========================================================================
        ortho_evidence: List[str] = []
        ortho_keywords = ["orthopedics", "fracture", "joint replacement", "arthroscopy", "osteoarthritis", "rheumatoid arthritis", "lumbar spine", "orthopedic"]
        for kw in ortho_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                ortho_evidence.append(f"Clinical documentation notes: '{kw.title()}'")

        if ortho_evidence:
            specs = ["Orthopedics", "Multi-speciality"]
            detected_conditions.append(
                DetectedCondition(
                    condition_name="Orthopedic / Musculoskeletal Condition",
                    category="ORTHOPEDICS",
                    supporting_evidence=ortho_evidence,
                    confidence=0.92,
                    risk_level="MODERATE",
                    source_data="Clinical Records",
                    recommended_specialties=specs,
                    requires_icu=False,
                )
            )
            all_specialties.update(specs)

        # =========================================================================
        # 10. INSUFFICIENT EVIDENCE CHECK
        # =========================================================================
        if not detected_conditions:
            return PatientConditionAnalysisResult(
                has_sufficient_evidence=False,
                primary_condition=None,
                all_conditions=[],
                recommended_specialties=[],
                requires_icu_or_critical_care=False,
                clinical_summary="Insufficient clinical evidence in patient record to determine specific medical specialty requirements.",
            )

        # Sort conditions by risk priority (CRITICAL > HIGH > MODERATE > LOW) and confidence
        risk_priority = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "LOW": 1}
        detected_conditions.sort(key=lambda c: (risk_priority.get(c.risk_level, 1), c.confidence), reverse=True)
        primary = detected_conditions[0]

        summary_parts = [
            f"Evidence indicates possible {primary.condition_name} (Confidence: {int(primary.confidence * 100)}%, Risk: {primary.risk_level})."
        ]
        if primary.supporting_evidence:
            summary_parts.append(f"Key Evidence: {'; '.join(primary.supporting_evidence[:3])}.")
        summary_parts.append(f"Recommended clinical specializations: {', '.join(primary.recommended_specialties)}.")

        return PatientConditionAnalysisResult(
            has_sufficient_evidence=True,
            primary_condition=primary,
            all_conditions=detected_conditions,
            recommended_specialties=list(all_specialties),
            requires_icu_or_critical_care=overall_icu,
            clinical_summary=" ".join(summary_parts),
        )


patient_condition_service = PatientConditionService()
