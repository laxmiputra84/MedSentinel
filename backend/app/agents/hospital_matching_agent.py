"""
MedSentinel Agentic Architecture — Hospital Matching Agent
Connects the patient medical data pipeline to real hospital recommendations.
Derives medical condition and required clinical specialties strictly from actual patient records
and ranks verified matching hospitals by specialization, real Haversine distance, and verified facilities.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding
from app.services.patient_condition_service import PatientConditionService
from app.services.hospital_service import HospitalService


class HospitalMatchingAgent(BaseAgent):
    """
    Specialized agent that translates patient clinical evidence into
    ranked real hospital recommendations.
    """

    def __init__(self):
        super().__init__(
            name="hospital_matching",
            role="Patient Condition-Driven Hospital Matching & Geo-Ranking",
            description="Extracts condition evidence from multimodal patient data and identifies nearest matching verified hospitals.",
            version="1.0.0",
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        ctx = context or {}
        lat = ctx.get("latitude") or ctx.get("patient_latitude")
        lon = ctx.get("longitude") or ctx.get("patient_longitude")
        loc = ctx.get("location") or ctx.get("patient_location")
        radius_km = ctx.get("radius_km")
        is_avail = ctx.get("is_available")

        # 1. Evidence Extraction
        condition_res = PatientConditionService.extract_patient_condition_evidence(
            extracted_text=state.extracted_text,
            lab_results=state.lab_results,
            clinical_findings=state.clinical_findings,
            clinical_notes=ctx.get("clinical_notes"),
        )

        findings: List[ClinicalFinding] = []

        if not condition_res.has_sufficient_evidence:
            findings.append(
                self.create_finding(
                    title="Hospital Matching: Insufficient Evidence",
                    description="No diagnostic clinical markers or specific disease evidence detected to recommend specialized hospital facilities.",
                    category="HOSPITAL_MATCHING",
                    status="NORMAL",
                    confidence=0.90,
                )
            )
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={
                    "has_sufficient_evidence": False,
                    "matched_hospitals": [],
                    "message": "Insufficient patient evidence for specialized hospital recommendation.",
                },
                findings=findings,
            )

        # 2. Database Hospital Search & Geo-Ranking (if db session available)
        matched_hospitals: List[Dict[str, Any]] = []
        if db:
            match_res = HospitalService.recommend_hospitals_for_patient_condition(
                db=db,
                condition_analysis=condition_res,
                latitude=float(lat) if lat is not None else None,
                longitude=float(lon) if lon is not None else None,
                location=str(loc) if loc else None,
                radius_km=float(radius_km) if radius_km is not None else None,
                is_available=is_avail,
                limit=5,
            )
            matched_hospitals = match_res.get("hospitals", [])

        primary = condition_res.primary_condition
        cond_title = primary.condition_name if primary else "Clinical Condition"

        findings.append(
            self.create_finding(
                title=f"Hospital Matching: {cond_title}",
                description=(
                    f"Identified {len(matched_hospitals)} matching medical centers specialized in "
                    f"{', '.join(condition_res.recommended_specialties)} based on documented patient evidence."
                ),
                category="HOSPITAL_MATCHING",
                status="HIGH" if condition_res.requires_icu_or_critical_care else "NORMAL",
                confidence=primary.confidence if primary else 0.88,
            )
        )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "has_sufficient_evidence": True,
                "detected_condition": primary.model_dump() if primary else None,
                "recommended_specialties": condition_res.recommended_specialties,
                "matched_hospitals": matched_hospitals,
                "total_matched": len(matched_hospitals),
            },
            findings=findings,
        )
