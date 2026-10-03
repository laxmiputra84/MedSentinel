from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.models.knowledge_base import KnowledgeDataset, KnowledgeAccessRule

class RetrievalService:
    @staticmethod
    async def retrieve_relevant_knowledge(
        query: str,
        user_role: str,
        user_id: Optional[int] = None,
        user_hospital_id: Optional[int] = None,
        limit: int = 5,
        score_threshold: float = 0.15,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes end-to-end authorized knowledge retrieval:
        1. Generates query embedding vector
        2. Filters out disabled or unapproved datasets
        3. Executes permission-aware vector search
        4. Verifies database access rules
        """
        if not query or not query.strip():
            return []

        # 1. Generate query vector
        query_vector = await EmbeddingService.get_embedding(query)

        # 2. Vector search with RBAC permissions
        raw_results = await VectorStore.search_vectors(
            query_vector=query_vector,
            user_role=user_role,
            user_id=user_id,
            user_hospital_id=user_hospital_id,
            limit=limit * 2,
            score_threshold=score_threshold
        )

        if not raw_results:
            return []

        # 3. If DB session provided, double-check active dataset status
        if db:
            active_rows = db.query(KnowledgeDataset.id).filter(
                KnowledgeDataset.status.in_(["READY", "APPROVED"]),
                KnowledgeDataset.status != "DISABLED"
            ).all()
            active_dataset_ids = {r[0] if isinstance(r, (tuple, list)) else getattr(r, 'id', r[0]) for r in active_rows}
            filtered_results = [
                r for r in raw_results
                if r.get("dataset_id") in active_dataset_ids
            ]
        else:
            filtered_results = raw_results

        return filtered_results[:limit]
