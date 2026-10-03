from typing import Optional
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    MessageResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.core.events import EventType
from app.services.event_bus import publish_event

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with email, name, phone, and secure hashed password."""
    user = AuthService.register_user(db, request)

    # Publish PATIENT_CREATED Event
    publish_event(
        event_type=EventType.PATIENT_CREATED.value,
        entity_id=user.id,
        user_id=user.id,
        payload={"name": user.name, "email": user.email, "role": user.role},
        entity_type="patient",
        db=db,
        sync=False,
    )

    return user

@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate user with email and password and return Access & Refresh tokens."""
    token_data = AuthService.login_user(db, request)
    
    # Optionally set httpOnly cookie for extra browser security
    response.set_cookie(
        key="access_token",
        value=token_data.access_token,
        httponly=True,
        samesite="lax",
        secure=False, # Set to True in production with HTTPS
        max_age=15 * 60
    )
    return token_data

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: TokenRefreshRequest, response: Response, db: Session = Depends(get_db)):
    """Rotate and refresh access token using valid refresh token."""
    token_data = AuthService.refresh_access_token(db, request.refresh_token)
    response.set_cookie(
        key="access_token",
        value=token_data.access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=15 * 60
    )
    return token_data

@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    payload: Optional[TokenRefreshRequest] = None,
    db: Session = Depends(get_db)
):
    """Logout user and revoke refresh token."""
    if payload and payload.refresh_token:
        AuthService.revoke_refresh_token(db, payload.refresh_token)
    
    response.delete_cookie("access_token")
    return MessageResponse(message="Logged out successfully")

@router.get("/me", response_model=UserResponse)
def get_authenticated_user(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user profile via JWT."""
    return current_user
