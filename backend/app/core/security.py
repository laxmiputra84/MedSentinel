from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def normalize_role(role: Optional[str]) -> str:
    """Normalizes legacy or inconsistent role strings to canonical MedSentinel roles."""
    if not role:
        return "USER"
    r = role.strip().upper()
    if r in ["ADMIN", "SUPERADMIN", "SUPER_ADMINISTRATOR", "ADMINISTRATOR"]:
        return "SUPER_ADMIN"
    if r in ["HOSPITAL", "HOSPITALADMIN"]:
        return "HOSPITAL_ADMIN"
    if r in ["INSURANCE", "INSURANCEADMIN", "INSURER"]:
        return "INSURANCE_ADMIN"
    if r in ["PATIENT", "CLIENT"]:
        return "USER"
    return r

def create_access_token(subject: Union[str, Any], role: Optional[str] = None, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    canonical_role = normalize_role(role)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": canonical_role,
        "type": "access",
        "jti": uuid.uuid4().hex
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": uuid.uuid4().hex
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload and "role" in payload:
            payload["role"] = normalize_role(payload.get("role"))
        return payload
    except JWTError:
        return None

