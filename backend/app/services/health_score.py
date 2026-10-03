from typing import List, Dict, Any, Tuple

class HealthScoreEngine:
    @staticmethod
    def calculate_scores(tests: List[Dict[str, Any]]) -> Tuple[int, int, str, int]:
        """
        Calculates (health_score, risk_score, risk_level, abnormal_tests_count).
        Risk levels:
          0–20:   LOW
          21–50:  MODERATE
          51–75:  HIGH
          76–100: CRITICAL
        """
        if not tests:
            return 95, 10, "LOW", 0

        abnormal_count = 0
        critical_count = 0
        mild_abnormal_count = 0

        for t in tests:
            st = t.get("status", "NORMAL").upper()
            if st == "CRITICAL" or t.get("is_critical"):
                critical_count += 1
                abnormal_count += 1
            elif st in ["HIGH", "LOW"]:
                mild_abnormal_count += 1
                abnormal_count += 1

        # Base risk calculation
        # Each mild abnormal adds 12-15 points
        # Each critical abnormal adds 35-45 points
        calculated_risk = (mild_abnormal_count * 14) + (critical_count * 40)
        risk_score = min(100, max(5, calculated_risk))

        # Health score is inversely proportional
        health_score = max(5, min(100, 100 - int(risk_score * 0.85)))

        if risk_score <= 20:
            risk_level = "LOW"
        elif risk_score <= 50:
            risk_level = "MODERATE"
        elif risk_score <= 75:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return health_score, risk_score, risk_level, abnormal_count

    @staticmethod
    def generate_health_summary(tests: List[Dict[str, Any]], risk_level: str) -> str:
        """
        Generates a clear, patient-friendly health summary based on abnormal findings.
        Adheres strictly to medical safety: does not provide a medical diagnosis,
        and includes a mandatory disclaimer.
        """
        abnormals = [t for t in tests if t.get("status") in ["LOW", "HIGH", "CRITICAL"]]

        if not abnormals:
            return (
                "AI HEALTH SUMMARY\n\n"
                "All analyzed laboratory test parameters appear within standard biological reference intervals.\n\n"
                "Overall Pattern:\n"
                "Routine screening shows stable hematological and biochemical markers.\n\n"
                "Important:\n"
                "This analysis is for informational and decision-support purposes only. "
                "It does not provide a medical diagnosis. "
                "Please consult a qualified healthcare professional."
            )

        bullet_points = []
        pattern_clues = []

        for t in abnormals:
            name = t.get("name", "Test")
            status = t.get("status", "Abnormal")
            val = t.get("value")
            unit = t.get("unit", "")
            bullet_points.append(f"• {name} is {status.lower()} ({val} {unit}).")

            if name in ["WBC", "Neutrophils", "CRP"]:
                pattern_clues.append("inflammatory or immune response")
            elif name in ["Hemoglobin", "RBC Count", "PCV"]:
                pattern_clues.append("erythrocyte / red blood cell index variation")
            elif name in ["Fasting Blood Glucose", "HbA1c"]:
                pattern_clues.append("glycemic regulation")
            elif name in ["Serum Creatinine", "BUN", "eGFR"]:
                pattern_clues.append("renal / kidney metabolic markers")
            elif name in ["ALT", "AST", "Total Bilirubin"]:
                pattern_clues.append("hepatic / liver enzyme markers")
            elif name in ["Potassium", "Sodium", "Calcium"]:
                pattern_clues.append("serum electrolyte balance")

        unique_clues = list(set(pattern_clues))
        if unique_clues:
            pattern_text = f"The observed variations may correlate with {', '.join(unique_clues)}."
        else:
            pattern_text = "The laboratory findings show specific values outside typical reference thresholds."

        critical_note = ""
        if risk_level == "CRITICAL" or any(t.get("status") == "CRITICAL" for t in abnormals):
            critical_note = (
                "\n\nALERT:\n"
                "One or more parameters are in a critical range. Prompt clinical evaluation by a medical provider is recommended."
            )

        summary = (
            "AI HEALTH SUMMARY\n\n"
            "Abnormal Results Detected:\n\n"
            + "\n".join(bullet_points)
            + f"\n\nOverall Pattern:\n{pattern_text}"
            + critical_note
            + "\n\nImportant:\n"
            "This analysis is for informational and decision-support purposes only. "
            "It does not provide a medical diagnosis. "
            "Please consult a qualified healthcare professional."
        )

        return summary
