from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve current user's profile and medical info."""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile, emergency contact, blood group, allergies, and schemes."""
    if update_data.name is not None:
        current_user.name = update_data.name
    if update_data.phone is not None:
        current_user.phone = update_data.phone
    if update_data.blood_group is not None:
        current_user.blood_group = update_data.blood_group
    if update_data.allergies is not None:
        current_user.allergies = update_data.allergies
    if update_data.emergency_contact is not None:
        current_user.emergency_contact = update_data.emergency_contact
    if update_data.schemes is not None:
        current_user.schemes = update_data.schemes

    db.commit()
    db.refresh(current_user)
    return current_user
