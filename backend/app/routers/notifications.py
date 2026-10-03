from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.dependencies.auth import get_current_user
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve notifications for the current authenticated user."""
    return NotificationService.get_user_notifications(db=db, user_id=current_user.id)

@router.patch("/{notification_id}/read", response_model=Dict[str, str])
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a single notification as read."""
    success = NotificationService.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return {"message": "Notification marked as read"}

@router.patch("/read-all", response_model=Dict[str, int])
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all unread notifications as read for current user."""
    count = NotificationService.mark_all_as_read(db=db, user_id=current_user.id)
    return {"updated_count": count}
