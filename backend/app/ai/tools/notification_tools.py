from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models import User, Notification

def get_user_notifications_tool(
    db: Session,
    user: User,
    unread_only: bool = False
) -> Dict[str, Any]:
    """Retrieve recent notifications and alerts for the authenticated user."""
    query = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifs = query.order_by(Notification.created_at.desc()).limit(10).all()

    items = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "date": n.created_at.isoformat() if n.created_at else None
        }
        for n in notifs
    ]

    return {
        "user_email": user.email,
        "unread_count": sum(1 for n in items if not n["is_read"]),
        "notifications": items
    }
