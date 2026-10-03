from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.hospital import Hospital
from app.models.saved_item import SavedItem
from app.schemas.hospital import HospitalResponse, SavedHospitalCreate
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/saved-items", tags=["Saved Hospitals"])

@router.get("", response_model=List[HospitalResponse])
def get_user_saved_hospitals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all saved hospitals for the authenticated user."""
    return db.query(Hospital).join(
        SavedItem, SavedItem.hospital_id == Hospital.id
    ).filter(
        SavedItem.user_id == current_user.id
    ).all()

@router.post("", response_model=MessageResponse)
def save_hospital(
    data: SavedHospitalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bookmark a hospital for the authenticated user."""
    hospital = db.query(Hospital).filter(Hospital.id == data.hospital_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found"
        )

    existing = db.query(SavedItem).filter(
        SavedItem.user_id == current_user.id,
        SavedItem.hospital_id == data.hospital_id
    ).first()

    if existing:
        return MessageResponse(message="Hospital is already saved")

    new_saved = SavedItem(user_id=current_user.id, hospital_id=data.hospital_id)
    db.add(new_saved)
    db.commit()
    return MessageResponse(message="Hospital saved successfully")

@router.delete("/{hospital_id}", response_model=MessageResponse)
def remove_saved_hospital(
    hospital_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a bookmarked hospital from the authenticated user's saved list."""
    saved_item = db.query(SavedItem).filter(
        SavedItem.user_id == current_user.id,
        SavedItem.hospital_id == hospital_id
    ).first()

    if not saved_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved hospital item not found"
        )

    db.delete(saved_item)
    db.commit()
    return MessageResponse(message="Hospital removed from saved list")
