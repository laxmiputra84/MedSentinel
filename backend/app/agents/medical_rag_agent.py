"""
MedSentinel Agentic Architecture — Medical RAG Agent
Retrieves trusted, tenant-isolated clinical evidence and literature references
from the Private RAG system with strict RBAC enforcement and anti-hallucination safeguards.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding
from app.agents.tools import query_medical_rag_tool


class MedicalRAGAgent(BaseAgent):
    """
    Specialized agent for retrieving cited, RBAC-filtered clinical knowledge.
    """

    def __init__(self):
        super().__init__(
            name="medical_rag",
            role="Private Medical Knowledge Retrieval & Citation Evidence",
            description="Queries private clinical knowledge datasets for cited reference evidence with hospital multi-tenant isolation.",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        # 1. Formulate focused clinical query based on findings or abnormal lab tests
        abnormal_names = [t["name"] for t in state.lab_results if t.get("status") in ["LOW", "HIGH", "CRITICAL"]]

        if abnormal_names:
            query = f"Clinical reference guidelines for abnormal {', '.join(abnormal_names[:3])}"
        elif state.document_type and state.document_type != "Other":
            query = f"Clinical diagnostic and management guidelines for {state.document_type}"
        else:
            query = "Standard clinical laboratory reference intervals and patient monitoring"

        # 2. Call Medical RAG Tool
        rag_res = await query_medical_rag_tool(
            query=query,
            user_role=state.user_role or "USER",
            user_id=state.user_id,
            user_hospital_id=state.hospital_id,
            mode="strict_private",
            db=db
        )

        sources = rag_res.get("sources", [])
        context_str = rag_res.get("context", "")
        found_in_private = rag_res.get("found_in_private_data", False)

        state.retrieved_evidence = sources
        state.rag_context = context_str

        findings: List[ClinicalFinding] = []

        if found_in_private and sources:
            source_titles = [s.get("title", "Clinical Protocol") for s in sources]
            findings.append(
                self.create_finding(
                    title="Cited Clinical Reference Retrieved",
                    description=(
                        f"Retrieved {len(sources)} verified reference citations from private clinical knowledge: "
                        f"{', '.join(source_titles[:3])}."
                    ),
                    category="EVIDENCE_CITATION",
                    status="NORMAL",
                    evidence="; ".join([f"Doc #{s.get('document_id')}: {s.get('title')}" for s in sources]),
                    confidence=0.92
                )
            )
        else:
            findings.append(
                self.create_finding(
                    title="Knowledge Base Evidence Query",
                    description="No direct hospital-specific knowledge chunks matched the search criteria. Standard baseline guidelines apply.",
                    category="EVIDENCE_CITATION",
                    status="NORMAL",
                    confidence=0.80
                )
            )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "query": query,
                "sources_count": len(sources),
                "found_in_private_data": found_in_private,
                "sources": sources,
            },
            findings=findings
        )
