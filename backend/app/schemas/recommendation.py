from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
import json

class RecommendationResponse(BaseModel):
    id: int
    user_id: int
    patient_id: Optional[int] = None
    recommendation_type: str
    priority: str
    title: str
    description: Optional[str] = None
    reason: Optional[str] = None
    confidence: float
    sources: List[str] = Field(default_factory=list)
    status: str
    related_document_id: Optional[int] = None
    related_claim_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("sources", mode="before")
    def parse_sources(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [v]
        return ["RULE_BASED"]

    model_config = ConfigDict(from_attributes=True)

class RecommendationStatusUpdate(BaseModel):
    status: str = Field(..., description="ACTIVE, VIEWED, DISMISSED, or COMPLETED")

    @field_validator("status")
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"ACTIVE", "VIEWED", "DISMISSED", "COMPLETED"}
        upper = v.upper()
        if upper not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return upper

class RelatedDocumentItem(BaseModel):
    document_id: int
    document_code: Optional[str] = None
    original_name: str
    doc_type: str
    similarity: float
    suggested_actions: List[str] = Field(default_factory=list)

class RelatedDocumentRecommendationResponse(BaseModel):
    patient_id: Optional[int] = None
    related_documents: List[RelatedDocumentItem] = Field(default_factory=list)
