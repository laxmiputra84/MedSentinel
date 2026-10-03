import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Standard clinical reference database with default biological reference intervals and critical panic ranges
STANDARD_LAB_TESTS: Dict[str, Dict[str, Any]] = {
    "Hemoglobin": {
        "aliases": ["hemoglobin", "hb", "hgb"],
        "unit": "g/dL",
        "reference_min": 13.5,
        "reference_max": 17.5,
        "critical_low": 7.0,
        "critical_high": 20.0,
    },
    "RBC Count": {
        "aliases": ["rbc count", "rbc", "red blood cell", "red blood cells", "erythrocytes"],
        "unit": "x10^6/uL",
        "reference_min": 4.5,
        "reference_max": 5.9,
        "critical_low": 2.0,
        "critical_high": 7.0,
    },
    "PCV": {
        "aliases": ["packed cell volume", "pcv", "hematocrit", "hct"],
        "unit": "%",
        "reference_min": 40.0,
        "reference_max": 50.0,
        "critical_low": 20.0,
        "critical_high": 60.0,
    },
    "MCV": {
        "aliases": ["mean corpuscular volume", "mcv"],
        "unit": "fL",
        "reference_min": 80.0,
        "reference_max": 100.0,
        "critical_low": 65.0,
        "critical_high": 120.0,
    },
    "WBC": {
        "aliases": ["total leukocyte count", "wbc count", "wbc", "white blood cell", "leukocytes", "total wbc"],
        "unit": "cells/uL",
        "reference_min": 4000.0,
        "reference_max": 11000.0,
        "critical_low": 2000.0,
        "critical_high": 30000.0,
    },
    "Platelets": {
        "aliases": ["platelet count", "platelets", "plt"],
        "unit": "/uL",
        "reference_min": 150000.0,
        "reference_max": 450000.0,
        "critical_low": 30000.0,
        "critical_high": 1000000.0,
    },
    "Neutrophils": {
        "aliases": ["neutrophils", "neutrophil", "neut"],
        "unit": "%",
        "reference_min": 40.0,
        "reference_max": 70.0,
        "critical_low": 15.0,
        "critical_high": 90.0,
    },
    "Lymphocytes": {
        "aliases": ["lymphocytes", "lymphocyte", "lymph"],
        "unit": "%",
        "reference_min": 20.0,
        "reference_max": 40.0,
        "critical_low": 5.0,
        "critical_high": 80.0,
    },
    "Monocytes": {
        "aliases": ["monocytes", "monocyte", "mono"],
        "unit": "%",
        "reference_min": 2.0,
        "reference_max": 8.0,
        "critical_low": None,
        "critical_high": 20.0,
    },
    "Eosinophils": {
        "aliases": ["eosinophils", "eosinophil", "eos"],
        "unit": "%",
        "reference_min": 1.0,
        "reference_max": 6.0,
        "critical_low": None,
        "critical_high": 25.0,
    },
    "Basophils": {
        "aliases": ["basophils", "basophil", "baso"],
        "unit": "%",
        "reference_min": 0.0,
        "reference_max": 1.0,
        "critical_low": None,
        "critical_high": 5.0,
    },
    "Fasting Blood Glucose": {
        "aliases": ["fasting blood glucose", "fasting blood sugar", "fbs", "glucose fasting", "blood glucose"],
        "unit": "mg/dL",
        "reference_min": 70.0,
        "reference_max": 100.0,
        "critical_low": 50.0,
        "critical_high": 400.0,
    },
    "HbA1c": {
        "aliases": ["glycated hemoglobin", "hba1c", "a1c"],
        "unit": "%",
        "reference_min": 4.0,
        "reference_max": 5.6,
        "critical_low": None,
        "critical_high": 12.0,
    },
    "Serum Creatinine": {
        "aliases": ["serum creatinine", "creatinine"],
        "unit": "mg/dL",
        "reference_min": 0.7,
        "reference_max": 1.3,
        "critical_low": 0.3,
        "critical_high": 4.0,
    },
    "BUN": {
        "aliases": ["blood urea nitrogen", "bun", "blood urea"],
        "unit": "mg/dL",
        "reference_min": 7.0,
        "reference_max": 20.0,
        "critical_low": 2.0,
        "critical_high": 80.0,
    },
    "eGFR": {
        "aliases": ["egfr", "estimated gfr"],
        "unit": "mL/min/1.73m2",
        "reference_min": 90.0,
        "reference_max": 130.0,
        "critical_low": 15.0,
        "critical_high": None,
    },
    "ALT": {
        "aliases": ["alanine aminotransferase", "alt", "sgpt", "alt/sgpt"],
        "unit": "U/L",
        "reference_min": 7.0,
        "reference_max": 56.0,
        "critical_low": None,
        "critical_high": 500.0,
    },
    "AST": {
        "aliases": ["aspartate aminotransferase", "ast", "sgot", "ast/sgot"],
        "unit": "U/L",
        "reference_min": 8.0,
        "reference_max": 48.0,
        "critical_low": None,
        "critical_high": 500.0,
    },
    "Total Bilirubin": {
        "aliases": ["serum bilirubin", "total bilirubin", "bilirubin total", "bilirubin"],
        "unit": "mg/dL",
        "reference_min": 0.2,
        "reference_max": 1.2,
        "critical_low": None,
        "critical_high": 15.0,
    },
    "CRP": {
        "aliases": ["c-reactive protein", "crp", "hs-crp", "high-sensitivity crp"],
        "unit": "mg/L",
        "reference_min": 0.0,
        "reference_max": 3.0,
        "critical_low": None,
        "critical_high": 50.0,
    },
    "Potassium": {
        "aliases": ["serum potassium", "potassium", "k+"],
        "unit": "mEq/L",
        "reference_min": 3.5,
        "reference_max": 5.1,
        "critical_low": 2.8,
        "critical_high": 6.0,
    },
    "Sodium": {
        "aliases": ["serum sodium", "sodium", "na+"],
        "unit": "mEq/L",
        "reference_min": 136.0,
        "reference_max": 145.0,
        "critical_low": 120.0,
        "critical_high": 160.0,
    },
    "Calcium": {
        "aliases": ["serum calcium", "calcium", "ca++"],
        "unit": "mg/dL",
        "reference_min": 8.5,
        "reference_max": 10.5,
        "critical_low": 6.5,
        "critical_high": 13.0,
    },
}

class LabAnalyzer:
    @staticmethod
    def evaluate_status(
        test_name: str,
        value: float,
        ref_min: Optional[float] = None,
        ref_max: Optional[float] = None,
    ) -> Tuple[str, bool]:
        """
        Compares observed value against reference ranges.
        Returns (status, is_critical), where status in:
        NORMAL, LOW, HIGH, CRITICAL, UNKNOWN
        """
        # Look up standard definitions if available
        def_info = STANDARD_LAB_TESTS.get(test_name)
        if def_info:
            if ref_min is None:
                ref_min = def_info.get("reference_min")
            if ref_max is None:
                ref_max = def_info.get("reference_max")
            crit_low = def_info.get("critical_low")
            crit_high = def_info.get("critical_high")

            # Check critical thresholds
            if crit_low is not None and value <= crit_low:
                return "CRITICAL", True
            if crit_high is not None and value >= crit_high:
                return "CRITICAL", True

        if ref_min is None and ref_max is None:
            return "UNKNOWN", False

        if ref_min is not None and value < ref_min:
            # If standard critical wasn't hit but value is severe (< 60% of min)
            if ref_min > 0 and value < (ref_min * 0.5):
                return "CRITICAL", True
            return "LOW", False

        if ref_max is not None and value > ref_max:
            # If standard critical wasn't hit but value is severe (> 200% of max)
            if ref_max > 0 and value > (ref_max * 2.5):
                return "CRITICAL", True
            return "HIGH", False

        return "NORMAL", False

    @staticmethod
    def extract_patient_info(text: str) -> Dict[str, Optional[str]]:
        """Extracts patient name, ID, and date from text."""
        patient_name = None
        patient_id = None
        report_date = None

        # Patient name search
        name_match = re.search(r"(?i)patient\s*name\s*[:\-]?\s*([A-Za-z\s\.]+?)(?:\s{2,}|\n|\||\r|$)", text)
        if name_match:
            candidate = name_match.group(1).strip()
            if len(candidate) > 2 and not candidate.lower().startswith("id"):
                patient_name = candidate

        # Patient ID / MRN search
        id_match = re.search(r"(?i)(?:patient\s*id|mrn|patient\s*no|uhid)\s*[:\-]?\s*([A-Za-z0-9\-]+)", text)
        if id_match:
            patient_id = id_match.group(1).strip()

        # Date search
        date_match = re.search(r"(?i)(?:report\s*date|date\s*collected|date)\s*[:\-]?\s*(\d{4}-\d{2}-\d{2}|\d{2}[/\-]\d{2}[/\-]\d{4})", text)
        if date_match:
            raw_date = date_match.group(1).strip()
            # Normalize to YYYY-MM-DD
            try:
                if "-" in raw_date and len(raw_date.split("-")[0]) == 4:
                    report_date = raw_date
                elif "/" in raw_date:
                    parts = raw_date.split("/")
                    if len(parts[2]) == 4:
                        report_date = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            except Exception:
                report_date = raw_date

        if not report_date:
            report_date = datetime.utcnow().strftime("%Y-%m-%d")

        return {
            "patient_name": patient_name or "Alex Demo Patient",
            "patient_id": patient_id or "MS-2026-08892",
            "report_date": report_date,
        }

    @staticmethod
    def extract_laboratory_data(text: str) -> Dict[str, Any]:
        """
        Parses raw text to extract patient metadata and structured laboratory tests.
        Detects names, values, units, reference intervals, and status.
        """
        info = LabAnalyzer.extract_patient_info(text)
        detected_tests: List[Dict[str, Any]] = []
        found_test_keys = set()

        # Scan text for each standard test
        for test_key, test_meta in STANDARD_LAB_TESTS.items():
            aliases = test_meta["aliases"]
            pattern = r"(?i)(?:" + "|".join(re.escape(a) for a in aliases) + r")\s*[:\t|]?\s*(\d+(?:[\.,]\d+)?)"
            match = re.search(pattern, text)

            if match:
                raw_val = match.group(1).replace(",", "")
                try:
                    val = float(raw_val)
                except ValueError:
                    continue

                # Look for custom reference ranges only AFTER the matched value, on the same line or within 80 chars
                start_pos = match.end()
                line_end = text.find("\n", start_pos)
                end_pos = line_end if (line_end != -1 and (line_end - start_pos) < 100) else min(len(text), start_pos + 80)
                window = text[start_pos:end_pos]

                ref_min = test_meta["reference_min"]
                ref_max = test_meta["reference_max"]

                range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–—to]+\s*(\d+(?:\.\d+)?)", window)
                if range_match:
                    try:
                        r1 = float(range_match.group(1))
                        r2 = float(range_match.group(2))
                        # Validate reasonable reference range bounds
                        if r1 < r2:
                            ref_min = r1
                            ref_max = r2
                    except Exception:
                        pass
                else:
                    lt_match = re.search(r"<\s*(\d+(?:\.\d+)?)", window)
                    if lt_match:
                        try:
                            ref_max = float(lt_match.group(1))
                            ref_min = 0.0
                        except Exception:
                            pass

                status, is_crit = LabAnalyzer.evaluate_status(test_key, val, ref_min, ref_max)

                detected_tests.append({
                    "name": test_key,
                    "value": val,
                    "unit": test_meta["unit"],
                    "reference_min": ref_min,
                    "reference_max": ref_max,
                    "status": status,
                    "is_critical": is_crit,
                })
                found_test_keys.add(test_key)

        return {
            "patient_name": info["patient_name"],
            "patient_id": info["patient_id"],
            "report_date": info["report_date"],
            "report_type": "Lab Report",
            "tests": detected_tests,
        }
