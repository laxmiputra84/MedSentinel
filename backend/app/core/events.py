"""
MedSentinel Event System Constants & Enumerations
Defines all supported healthcare event types, entity classifications,
and task states for the production event-driven architecture.
"""

from enum import Enum
from typing import Set


class EventType(str, Enum):
    # Patient events
    PATIENT_CREATED = "PATIENT_CREATED"
    PATIENT_UPDATED = "PATIENT_UPDATED"

    # Document events
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_UPDATED = "DOCUMENT_UPDATED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    DOCUMENT_DUPLICATE_DETECTED = "DOCUMENT_DUPLICATE_DETECTED"

    # Laboratory events
    LAB_REPORT_RECEIVED = "LAB_REPORT_RECEIVED"
    LAB_ANALYSIS_COMPLETED = "LAB_ANALYSIS_COMPLETED"
    CRITICAL_LAB_VALUE_DETECTED = "CRITICAL_LAB_VALUE_DETECTED"

    # Appointment events
    APPOINTMENT_CREATED = "APPOINTMENT_CREATED"
    APPOINTMENT_UPDATED = "APPOINTMENT_UPDATED"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"

    # Insurance events
    CLAIM_CREATED = "CLAIM_CREATED"
    CLAIM_UPDATED = "CLAIM_UPDATED"
    FRAUD_FLAG_DETECTED = "FRAUD_FLAG_DETECTED"

    # Agent events
    AGENT_TASK_CREATED = "AGENT_TASK_CREATED"
    AGENT_TASK_STARTED = "AGENT_TASK_STARTED"
    AGENT_TASK_COMPLETED = "AGENT_TASK_COMPLETED"
    AGENT_TASK_FAILED = "AGENT_TASK_FAILED"


class EventStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EntityType(str, Enum):
    PATIENT = "patient"
    DOCUMENT = "document"
    LAB_RESULT = "lab_result"
    APPOINTMENT = "appointment"
    CLAIM = "claim"
    AGENT_TASK = "agent_task"
    USER = "user"


# Set of recognized event types for validation
SUPPORTED_EVENT_TYPES: Set[str] = {e.value for e in EventType}

# Mapping of event types to default entity types
DEFAULT_ENTITY_TYPES = {
    EventType.PATIENT_CREATED.value: EntityType.PATIENT.value,
    EventType.PATIENT_UPDATED.value: EntityType.PATIENT.value,
    EventType.DOCUMENT_UPLOADED.value: EntityType.DOCUMENT.value,
    EventType.DOCUMENT_UPDATED.value: EntityType.DOCUMENT.value,
    EventType.DOCUMENT_VERIFIED.value: EntityType.DOCUMENT.value,
    EventType.DOCUMENT_DUPLICATE_DETECTED.value: EntityType.DOCUMENT.value,
    EventType.LAB_REPORT_RECEIVED.value: EntityType.DOCUMENT.value,
    EventType.LAB_ANALYSIS_COMPLETED.value: EntityType.LAB_RESULT.value,
    EventType.CRITICAL_LAB_VALUE_DETECTED.value: EntityType.LAB_RESULT.value,
    EventType.APPOINTMENT_CREATED.value: EntityType.APPOINTMENT.value,
    EventType.APPOINTMENT_UPDATED.value: EntityType.APPOINTMENT.value,
    EventType.APPOINTMENT_CANCELLED.value: EntityType.APPOINTMENT.value,
    EventType.CLAIM_CREATED.value: EntityType.CLAIM.value,
    EventType.CLAIM_UPDATED.value: EntityType.CLAIM.value,
    EventType.FRAUD_FLAG_DETECTED.value: EntityType.CLAIM.value,
    EventType.AGENT_TASK_CREATED.value: EntityType.AGENT_TASK.value,
    EventType.AGENT_TASK_STARTED.value: EntityType.AGENT_TASK.value,
    EventType.AGENT_TASK_COMPLETED.value: EntityType.AGENT_TASK.value,
    EventType.AGENT_TASK_FAILED.value: EntityType.AGENT_TASK.value,
}
