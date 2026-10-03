from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.rag.retrieval_service import RetrievalService
from app.rag.reranking_service import RerankingService
from app.rag.context_builder import ContextBuilder
from app.core.config import settings

class RAGPipeline:
    @staticmethod
    async def execute_rag_query(
        query: str,
        user_role: str,
        user_id: Optional[int] = None,
        user_hospital_id: Optional[int] = None,
        mode: str = "strict_private", # strict_private, internal_assistant, admin_analytics
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Executes complete Private RAG query pipeline:
        1. Retrieval with strict RBAC permission filtering
        2. Reranking of chunks
        3. Context generation
        4. Citations preparation
        """
        # 1. Retrieve Candidate Chunks
        retrieved_chunks = await RetrievalService.retrieve_relevant_knowledge(
            query=query,
            user_role=user_role,
            user_id=user_id,
            user_hospital_id=user_hospital_id,
            limit=8,
            score_threshold=0.08,
            db=db
        )

        # 2. Rerank Chunks
        reranked_chunks = RerankingService.rerank(query, retrieved_chunks, top_k=4)

        if not reranked_chunks:
            return {
                "context": "",
                "sources": [],
                "found_in_private_data": False,
                "chunks": []
            }

        # 3. Build RAG Prompt Context
        context_str = ContextBuilder.build_rag_context(reranked_chunks)

        # 4. Extract Structured Citations
        sources = []
        seen_docs = set()
        for ch in reranked_chunks:
            doc_id = ch.get("document_id")
            if doc_id not in seen_docs:
                seen_docs.add(doc_id)
                sources.append({
                    "dataset_id": ch.get("dataset_id"),
                    "document_id": doc_id,
                    "title": ch.get("title", "MedSentinel Verified Record"),
                    "confidence": ch.get("confidence", 0.85),
                    "hospital_id": ch.get("hospital_id")
                })

        return {
            "context": context_str,
            "sources": sources,
            "found_in_private_data": True,
            "chunks": reranked_chunks
        }
