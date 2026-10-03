from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class KnowledgeDatasetBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    visibility: str = "USER_AUTHORIZED"
    source_type: str = "ADMIN_UPLOAD"
    hospital_id: Optional[int] = None
    organization_id: Optional[int] = None

class KnowledgeDatasetCreate(KnowledgeDatasetBase):
    pass

class KnowledgeDatasetOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    source_type: str
    uploaded_by: Optional[int] = None
    status: str
    visibility: str
    hospital_id: Optional[int] = None
    organization_id: Optional[int] = None
    document_count: Optional[int] = 0
    chunk_count: Optional[int] = 0
    vector_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class KnowledgeDocumentOut(BaseModel):
    id: int
    dataset_id: int
    title: str
    content: str
    visibility: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class KnowledgeChunkOut(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    embedding_reference: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class KnowledgeProcessingLogOut(BaseModel):
    id: int
    dataset_id: int
    status: str
    message: Optional[str] = None
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class HospitalImageOut(BaseModel):
    id: int
    hospital_id: int
    file_path: str
    image_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    ai_generated_caption: Optional[str] = None
    is_approved_by_admin: bool
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
