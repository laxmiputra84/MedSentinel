"""
MedSentinel Agentic Architecture — Document Intelligence Agent
Identifies document categories (Lab Report, Prescription, Invoice, Insurance, etc.)
and determines downstream agent workflow routing.
"""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, WorkflowType
from app.agents.tools import classify_document_tool


class DocumentIntelligenceAgent(BaseAgent):
    """
    Specialized agent for medical document categorization and workflow type mapping.
    """

    def __init__(self):
        super().__init__(
            name="document_intelligence",
            role="Document Classification & Semantic Routing",
            description="Analyzes document text and metadata to classify clinical document type and determine required agent execution DAG.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        # 1. Determine text to classify: use state.extracted_text, filename, or context
        text = state.extracted_text or (context.get("text") if context else "") or ""
        filename = state.filename or (context.get("filename") if context else "") or ""

        # 2. Call Document Classification Tool
        res = await classify_document_tool(text=text, filename=filename)
        doc_type = res["document_type"]
        confidence = res["confidence"]

        # Store in state
        state.document_type = doc_type
        state.document_confidence = confidence

        # 3. Map to WorkflowType if AUTOMATIC
        suggested_workflow = WorkflowType.GENERAL_INQUIRY
        if doc_type in ["Lab Report", "Radiology Report", "Scan Report"]:
            suggested_workflow = WorkflowType.LAB_REPORT
        elif doc_type == "Prescription":
            suggested_workflow = WorkflowType.PRESCRIPTION
        elif doc_type in ["Medical Invoice", "Insurance Document"]:
            suggested_workflow = WorkflowType.INSURANCE_CLAIM
        elif doc_type == "Discharge Summary":
            suggested_workflow = WorkflowType.CLINICAL_SUMMARY

        if state.workflow_type == WorkflowType.AUTOMATIC:
            state.workflow_type = suggested_workflow

        finding = self.create_finding(
            title=f"Classified as {doc_type}",
            description=f"Document identified as '{doc_type}' with confidence {confidence * 100:.1f}%. Routing to {suggested_workflow.value} workflow.",
            category="DOCUMENT_INTELLIGENCE",
            confidence=confidence
        )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "document_type": doc_type,
                "confidence": confidence,
                "suggested_workflow": suggested_workflow.value,
            },
            findings=[finding]
        )
