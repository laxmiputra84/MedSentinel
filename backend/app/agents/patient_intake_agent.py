"""
MedSentinel Agentic Architecture — Patient Intake Agent
Normalizes patient information, validates mandatory demographics, and retrieves
known patient context without inventing non-existent data.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding
from app.models.patient import Patient
from app.models.user import User


class PatientIntakeAgent(BaseAgent):
    """
    Specialized agent responsible for patient context normalization and demographic ingestion.
    """

    def __init__(self):
        super().__init__(
            name="patient_intake",
            role="Patient Context & Demographic Ingestion",
            description="Normalizes patient identity, retrieves linked patient records, and verifies mandatory profile attributes.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        patient_data: Dict[str, Any] = {}
        missing_fields = []

        # 1. Resolve Patient from Database if DB session and patient_id/user_id available
        if db:
            patient_record = None
            if state.patient_id:
                patient_record = db.query(Patient).filter(Patient.id == state.patient_id).first()
            elif state.user_id:
                patient_record = db.query(Patient).filter(Patient.user_id == state.user_id).first()
                if not patient_record:
                    # Look up User
                    user_record = db.query(User).filter(User.id == state.user_id).first()
                    if user_record:
                        state.patient_name = user_record.name
                        patient_data["user_email"] = user_record.email
                        patient_data["user_role"] = user_record.role

            if patient_record:
                state.patient_id = patient_record.id
                state.patient_name = patient_record.name or state.patient_name
                patient_data["patient_code"] = patient_record.patient_code
                patient_data["blood_group"] = getattr(patient_record, "blood_group", None)
                patient_data["emergency_contact"] = getattr(patient_record, "emergency_contact", None)
                patient_data["dob"] = getattr(patient_record, "dob", None)
                patient_data["gender"] = getattr(patient_record, "gender", None)

        # 2. Check for extracted patient identifiers from context
        if not state.patient_name:
            if context and context.get("patient_name"):
                state.patient_name = context["patient_name"]
            else:
                missing_fields.append("patient_name")

        if not state.patient_id and not state.user_id:
            missing_fields.append("patient_id")

        patient_data["normalized_name"] = state.patient_name or "Anonymous Patient"
        patient_data["has_profile"] = bool(state.patient_id or state.user_id)
        patient_data["missing_fields"] = missing_fields

        findings = []
        if patient_data.get("blood_group"):
            findings.append(
                self.create_finding(
                    title="Patient Demographic Baseline",
                    description=f"Verified profile for {patient_data['normalized_name']} (Blood Group: {patient_data['blood_group']})",
                    category="PATIENT_PROFILE",
                    confidence=0.98
                )
            )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data=patient_data,
            findings=findings
        )
