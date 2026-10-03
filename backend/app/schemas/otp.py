from pydantic import BaseModel
from typing import Optional

class SendOtpRequest(BaseModel):
    phone: str

class SendOtpResponse(BaseModel):
    message: str
    expires_in: int = 300
    test_otp: Optional[str] = None
    success: bool = True

class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str

class VerifyOtpResponse(BaseModel):
    message: str
    success: bool = True
