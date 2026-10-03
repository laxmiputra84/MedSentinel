from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.dependencies.auth import require_super_admin
from app.models import User, AdminAuditLog

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin - Audit Logs"])

@router.get("")
def list_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Retrieve full audit log history for Super Admin oversight."""
    query = db.query(AdminAuditLog).options(
        joinedload(AdminAuditLog.admin_user)
    )
    if action:
        query = query.filter(AdminAuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter(AdminAuditLog.resource_type == resource_type)

    total = query.count()
    logs = query.order_by(AdminAuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "id": l.id,
            "admin_name": l.admin_user.name if l.admin_user else "System",
            "admin_email": l.admin_user.email if l.admin_user else "system@medsentinel.internal",
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "old_value": l.old_value,
            "new_value": l.new_value,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat() if l.created_at else None
        }
        for l in logs
    ]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items
    }
