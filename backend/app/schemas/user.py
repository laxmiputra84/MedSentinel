from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: Optional[str] = "USER"
    hospital_id: Optional[int] = None
    insurance_id: Optional[int] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = None
    schemes: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = None
    schemes: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
