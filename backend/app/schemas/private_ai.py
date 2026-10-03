from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class PrivateChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    mode: str = "strict_private" # strict_private, internal_assistant, admin_analytics

class KnowledgeSourceCitation(BaseModel):
    dataset_id: Optional[int] = None
    document_id: Optional[int] = None
    title: str
    confidence: float
    hospital_id: Optional[int] = None

class PrivateChatResponse(BaseModel):
    conversation_id: str
    response: str
    sources: List[KnowledgeSourceCitation] = []
    found_in_private_data: bool = True
    mode: str = "strict_private"
    suggested_actions: List[Dict[str, Any]] = []

class AIHealthResponse(BaseModel):
    ai_enabled: bool
    provider: str
    model: str
    configured: bool
    status: str
    rag_enabled: bool
    vector_db_provider: str
    indexed_vectors: int = 0
