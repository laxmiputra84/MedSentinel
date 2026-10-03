import random
import base64
import httpx
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.otp import OtpCode
from app.core.config import settings

class OtpService:
    @staticmethod
    def generate_numeric_otp(digits: int = 6) -> str:
        return f"{random.randint(10**(digits-1), 10**digits - 1)}"

    @staticmethod
    def create_or_update_otp(db: Session, phone: str) -> Tuple[str, int]:
        # Delete/expire old entries for this phone
        existing_otp = db.query(OtpCode).filter(OtpCode.phone == phone).first()
        otp_val = OtpService.generate_numeric_otp(6)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        if existing_otp:
            existing_otp.otp_code = otp_val
            existing_otp.expires_at = expires_at
            existing_otp.is_verified = False
            existing_otp.attempts = 0
        else:
            new_otp = OtpCode(
                phone=phone,
                otp_code=otp_val,
                expires_at=expires_at,
                is_verified=False,
                attempts=0
            )
            db.add(new_otp)

        db.commit()
        return otp_val, 300

    @staticmethod
    def verify_otp(db: Session, phone: str, submitted_otp: str) -> bool:
        record = db.query(OtpCode).filter(OtpCode.phone == phone).first()
        if not record:
            return False

        now = datetime.now(timezone.utc)
        record_expires = record.expires_at.replace(tzinfo=timezone.utc) if record.expires_at.tzinfo is None else record.expires_at

        if record_expires <= now:
            db.delete(record)
            db.commit()
            return False

        if record.attempts >= 5:
            db.delete(record)
            db.commit()
            return False

        record.attempts += 1
        if record.otp_code == submitted_otp:
            record.is_verified = True
            record.verified_until = now + timedelta(minutes=5)
            db.commit()
            return True

        db.commit()
        return False

    @staticmethod
    def is_phone_verified(db: Session, phone: str) -> bool:
        record = db.query(OtpCode).filter(OtpCode.phone == phone, OtpCode.is_verified == True).first()
        if not record or not record.verified_until:
            return False

        now = datetime.now(timezone.utc)
        until = record.verified_until.replace(tzinfo=timezone.utc) if record.verified_until.tzinfo is None else record.verified_until
        if until > now:
            return True
        return False

    @staticmethod
    def consume_verification(db: Session, phone: str) -> None:
        record = db.query(OtpCode).filter(OtpCode.phone == phone).first()
        if record:
            db.delete(record)
            db.commit()

    @staticmethod
    async def send_sms_notification(phone: str, message: str) -> Tuple[bool, Optional[str]]:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_PHONE_NUMBER

        if not account_sid or not auth_token or not from_number:
            print(f"[SMS DEV] Twilio credentials not configured. Message to {phone}: {message}")
            return False, "Twilio not configured (dev mode)"

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        auth_header = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode("utf-8")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={"To": phone, "From": from_number, "Body": message}
                )
                if response.status_code in [200, 201]:
                    return True, None
                return False, response.text
            except Exception as e:
                return False, str(e)
