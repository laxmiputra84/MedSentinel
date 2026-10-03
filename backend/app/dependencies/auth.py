from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token, normalize_role
from app.models.user import User

security = HTTPBearer(auto_error=False)

def get_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    if credentials:
        return credentials.credentials

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token

    return None

def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # Normalize role on user object if needed
    if user.role:
        user.role = normalize_role(user.role)

    return user

def get_optional_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user and user.is_active:
        if user.role:
            user.role = normalize_role(user.role)
        return user

    return None

def require_role(allowed_roles: List[str]) -> Callable:
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = normalize_role(current_user.role)
        # SUPER_ADMIN has access to all admin operations
        if user_role == "SUPER_ADMIN":
            return current_user

        if user_role not in [r.upper() for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {allowed_roles} role(s)"
            )
        return current_user
    return role_checker

require_super_admin = require_role(["SUPER_ADMIN"])
require_hospital_admin = require_role(["HOSPITAL_ADMIN", "SUPER_ADMIN"])
require_insurance_admin = require_role(["INSURANCE_ADMIN", "SUPER_ADMIN"])
require_any_admin = require_role(["HOSPITAL_ADMIN", "INSURANCE_ADMIN", "SUPER_ADMIN"])
