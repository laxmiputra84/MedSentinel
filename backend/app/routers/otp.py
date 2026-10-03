from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.otp_service import OtpService
from app.core.config import settings

router = APIRouter(tags=["OTP Verification"])

class SendOtpRequest(BaseModel):
    phone: str

class SendOtpResponse(BaseModel):
    success: bool
    message: str
    test_otp: str = ""

class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str

class VerifyOtpResponse(BaseModel):
    success: bool
    message: str

@router.post("/send-otp", response_model=SendOtpResponse)
async def send_otp(payload: SendOtpRequest, db: Session = Depends(get_db)):
    """Generate and dispatch a 6-digit OTP code to the requested phone number."""
    phone = payload.phone.strip()
    if not phone or len(phone) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid phone number with at least 8 digits is required."
        )

    otp_val, _ = OtpService.create_or_update_otp(db, phone)

    # Attempt SMS delivery via Twilio if configured
    msg = f"Your MedSentinel verification code is {otp_val}. Valid for 5 minutes."
    await OtpService.send_sms_notification(phone, msg)

    # Return test_otp in development/testing mode for ease of local testing
    test_otp_val = otp_val if settings.DEBUG or not settings.TWILIO_ACCOUNT_SID else ""

    return SendOtpResponse(
        success=True,
        message="OTP sent successfully",
        test_otp=test_otp_val
    )

@router.post("/verify-otp", response_model=VerifyOtpResponse)
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    """Verify a phone number against its submitted 6-digit OTP code."""
    phone = payload.phone.strip()
    submitted_otp = payload.otp.strip()

    if not phone or not submitted_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both phone number and OTP code are required."
        )

    is_valid = OtpService.verify_otp(db, phone, submitted_otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code. Please request a new one."
        )

    return VerifyOtpResponse(
        success=True,
        message="Phone number verified successfully"
    )
