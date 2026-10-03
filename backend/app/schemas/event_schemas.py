"""
Pydantic Schemas for Event-Driven Agent Architecture
Defines serialization models for Events, Agent Tasks, Execution Timelines,
and Real-Time System Status.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EventPublishRequest(BaseModel):
    event_type: str = Field(..., description="Healthcare event type, e.g. DOCUMENT_UPLOADED, CLAIM_CREATED")
    entity_id: str = Field(..., description="Identifier of the target entity")
    entity_type: Optional[str] = Field(None, description="Optional entity type (patient, document, claim, etc.)")
    user_id: Optional[int] = Field(None, description="User ID associated with event")
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Event payload data")
    idempotency_key: Optional[str] = Field(None, description="Optional unique client idempotency key")


class AgentTaskResponse(BaseModel):
    id: int
    task_id: str
    event_id: str
    agent_type: str
    entity_id: Optional[str] = None
    priority: str
    status: str
    input_context: Optional[Dict[str, Any]] = None
    output_result: Optional[Dict[str, Any]] = None
    retry_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class EventResponse(BaseModel):
    id: int
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    user_id: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    status: str
    retry_count: int
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    tasks: Optional[List[AgentTaskResponse]] = None

    class Config:
        from_attributes = True


class TaskTimelineItem(BaseModel):
    timestamp: str
    stage: str
    agent_type: Optional[str] = None
    status: str
    detail: str
    confidence: Optional[float] = None
    safety_check: Optional[Dict[str, Any]] = None


class AgentStatusResponse(BaseModel):
    system_status: str
    worker_running: bool
    queue_depth: int
    total_events_processed: int
    active_tasks_count: int
    completed_tasks_count: int
    failed_tasks_count: int
    registered_agents: List[str]
    active_websocket_connections: int
    timestamp: str


class EventListResponse(BaseModel):
    total: int
    events: List[EventResponse]


class AgentTaskListResponse(BaseModel):
    total: int
    tasks: List[AgentTaskResponse]
