from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

class AppointmentCreate(BaseModel):
    hospital_id: Optional[int] = None
    name: str
    phone: str
    email: EmailStr
    preferred_date: str
    preferred_time: str
    department: str
    reason: Optional[str] = None

class AppointmentRescheduleRequest(BaseModel):
    preferred_date: str
    preferred_time: str
    reason: Optional[str] = None

class AppointmentCancelRequest(BaseModel):
    cancellation_reason: Optional[str] = "Patient requested cancellation"

class AppointmentStatusUpdateRequest(BaseModel):
    status: str # PENDING, CONFIRMED, COMPLETED, CANCELLED
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    hospital_id: Optional[int] = None
    name: str
    phone: str
    email: str
    preferred_date: str
    preferred_time: str
    department: str
    reason: Optional[str] = None
    status: str
    notes: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AvailableSlotResponse(BaseModel):
    date: str
    department: str
    available_slots: List[str]
