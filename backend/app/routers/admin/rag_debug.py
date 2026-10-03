from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_super_admin, require_any_admin
from app.models.user import User
from app.models.knowledge_base import (
    KnowledgeDataset,
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeProcessingLog
)
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.retrieval_service import RetrievalService
from app.rag.reranking_service import RerankingService

router = APIRouter(prefix="/admin/rag", tags=["Admin RAG Diagnostics & Search"])

class RAGDebugResponse(BaseModel):
    dataset_status: str
    document_count: int
    chunk_count: int
    embedding_count: int
    vector_count: int
    collection_name: str
    last_processing_error: Optional[str] = None

class TestSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    dataset_id: Optional[int] = Field(None, description="Optional dataset ID filter")
    score_threshold: Optional[float] = Field(0.08, description="Minimum similarity threshold")
    limit: Optional[int] = Field(6, description="Max candidate chunks to return")

class TestSearchChunk(BaseModel):
    id: str
    score: float
    confidence: float
    title: str
    content: str
    dataset_id: Optional[int] = None
    document_id: Optional[int] = None
    hospital_id: Optional[int] = None
    visibility: str
    metadata: Dict[str, Any]

class TestSearchResponse(BaseModel):
    query: str
    total_vectors_in_store: int
    dataset_filter: Optional[int] = None
    matched_count: int
    qdrant_healthy: bool
    retrieved_chunks: List[TestSearchChunk]

@router.get("/debug/{dataset_id}", response_model=RAGDebugResponse)
async def debug_dataset_rag(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    RAG diagnostic inspection endpoint for a specific knowledge dataset.
    Available exclusively to SUPER_ADMIN.
    """
    dataset = db.query(KnowledgeDataset).filter(KnowledgeDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset with ID {dataset_id} not found"
        )

    doc_count = db.query(KnowledgeDocument).filter(KnowledgeDocument.dataset_id == dataset.id).count()
    chunks = db.query(KnowledgeChunk).join(KnowledgeDocument).filter(KnowledgeDocument.dataset_id == dataset.id).all()
    chunk_count = len(chunks)
    embedding_count = sum(1 for c in chunks if c.embedding_reference)
    vector_count = VectorStore.get_dataset_vector_count(dataset.id)

    # Check for last failed processing log
    last_error_log = db.query(KnowledgeProcessingLog).filter(
        KnowledgeProcessingLog.dataset_id == dataset.id,
        KnowledgeProcessingLog.status == "FAILED"
    ).order_by(KnowledgeProcessingLog.processed_at.desc()).first()

    last_error = last_error_log.message if last_error_log else None

    return RAGDebugResponse(
        dataset_status=dataset.status,
        document_count=doc_count,
        chunk_count=chunk_count,
        embedding_count=embedding_count,
        vector_count=vector_count,
        collection_name=VectorStore.get_collection_name(),
        last_processing_error=last_error
    )

@router.post("/test-search", response_model=TestSearchResponse)
async def test_search_rag(
    body: TestSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_admin)
):
    """
    Executes a direct vector similarity test query against the private knowledge index.
    Returns ranked candidate chunks and similarity scores.
    """
    # Ensure vectors loaded
    if VectorStore.get_indexed_points_count() == 0:
        await VectorStore.hydrate_from_db(db)

    # 1. Generate query vector
    query_vector = await EmbeddingService.get_embedding(body.query)

    # 2. Search vectors
    candidates = await VectorStore.search_vectors(
        query_vector=query_vector,
        user_role=current_user.role or "SUPER_ADMIN",
        user_id=current_user.id,
        user_hospital_id=getattr(current_user, "hospital_id", None),
        limit=body.limit or 6,
        score_threshold=body.score_threshold or 0.08
    )

    # Apply dataset filter if specified
    if body.dataset_id:
        candidates = [c for c in candidates if c.get("dataset_id") == body.dataset_id]

    is_qdrant = await VectorStore.check_qdrant_health()

    results = [
        TestSearchChunk(
            id=c["id"],
            score=c["score"],
            confidence=c.get("confidence", c["score"]),
            title=c["title"],
            content=c["content"],
            dataset_id=c.get("dataset_id"),
            document_id=c.get("document_id"),
            hospital_id=c.get("hospital_id"),
            visibility=c.get("visibility", "USER_AUTHORIZED"),
            metadata=c.get("metadata", {})
        )
        for c in candidates
    ]

    return TestSearchResponse(
        query=body.query,
        total_vectors_in_store=VectorStore.get_indexed_points_count(),
        dataset_filter=body.dataset_id,
        matched_count=len(results),
        qdrant_healthy=is_qdrant,
        retrieved_chunks=results
    )
