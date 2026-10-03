from datetime import datetime, timezone, timedelta
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings

class AuthService:
    @staticmethod
    def register_user(db: Session, request: UserRegisterRequest) -> User:
        clean_email = request.email.strip().lower()
        existing_user = db.query(User).filter(func.lower(User.email) == clean_email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )

        hashed_password = get_password_hash(request.password)
        new_user = User(
            name=request.name.strip(),
            email=clean_email,
            phone=request.phone.strip() if request.phone else None,
            hashed_password=hashed_password,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def login_user(db: Session, request: UserLoginRequest) -> TokenResponse:
        identifier = request.email.strip()
        clean_digits = "".join(ch for ch in identifier if ch.isdigit())
        
        # Strip common formatting chars from stored phone in DB
        clean_db_phone = func.replace(func.replace(func.replace(User.phone, " ", ""), "+", ""), "-", "")
        
        phone_match_clauses = [User.phone == identifier]
        if clean_digits and len(clean_digits) >= 6:
            phone_match_clauses.append(clean_db_phone.like(f"%{clean_digits}%"))

        user = db.query(User).filter(
            or_(
                func.lower(User.email) == identifier.lower(),
                *phone_match_clauses
            )
        ).first()

        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        access_token = create_access_token(subject=str(user.id), role=user.role)
        refresh_token_str = create_refresh_token(subject=str(user.id))

        # Store refresh token in DB
        refresh_token_entry = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(refresh_token_entry)
        db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            user_id=user.id,
            name=user.name,
            email=user.email,
            role=user.role or "USER"
        )

    @staticmethod
    def refresh_access_token(db: Session, refresh_token_str: str) -> TokenResponse:
        payload = decode_token(refresh_token_str)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject"
            )

        db_token = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token_str,
            RefreshToken.revoked == False
        ).first()

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or already revoked"
            )

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Rotate refresh token: revoke old one and issue a new one
        db_token.revoked = True
        
        new_access_token = create_access_token(subject=str(user.id), role=user.role)
        new_refresh_token_str = create_refresh_token(subject=str(user.id))

        new_db_token = RefreshToken(
            user_id=user.id,
            token=new_refresh_token_str,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(new_db_token)
        db.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token_str,
            token_type="bearer",
            user_id=user.id,
            name=user.name,
            email=user.email,
            role=user.role or "USER"
        )

    @staticmethod
    def revoke_refresh_token(db: Session, refresh_token_str: str) -> None:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token_str).first()
        if db_token:
            db_token.revoked = True
            db.commit()
