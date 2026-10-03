from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import require_super_admin
from app.models import User, Notification
from app.services.notification_service import NotificationService
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/admin/notifications", tags=["Admin - Notifications"])

class BroadcastNotificationRequest(BaseModel):
    title: str
    message: str
    type: Optional[str] = "alert" # alert, info, update
    target_user_id: Optional[int] = None # None means broadcast to all active users

@router.get("")
def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """List system notification log across users."""
    total = db.query(Notification).count()
    notifs = db.query(Notification).order_by(Notification.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "id": n.id,
            "user_id": n.user_id,
            "recipient_name": n.user.name if n.user else "Patient",
            "recipient_email": n.user.email if n.user else "N/A",
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None
        }
        for n in notifs
    ]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items
    }

@router.post("/broadcast", status_code=status.HTTP_201_CREATED)
def broadcast_notification(
    payload: BroadcastNotificationRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Broadcast an alert or announcement to all users or a specific recipient."""
    created_count = 0
    if payload.target_user_id:
        target = db.query(User).filter(User.id == payload.target_user_id).first()
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found.")
        NotificationService.create_notification(
            db=db,
            user_id=target.id,
            title=payload.title,
            message=payload.message,
            type=payload.type or "alert"
        )
        created_count = 1
    else:
        active_users = db.query(User).filter(User.is_active == True).all()
        for u in active_users:
            NotificationService.create_notification(
                db=db,
                user_id=u.id,
                title=payload.title,
                message=payload.message,
                type=payload.type or "alert"
            )
        created_count = len(active_users)

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="NOTIFICATION_BROADCAST",
        resource_type="Notification",
        new_value={"title": payload.title, "recipients_count": created_count}
    )

    return {
        "message": f"Broadcast successfully delivered to {created_count} user(s).",
        "recipients_count": created_count
    }
