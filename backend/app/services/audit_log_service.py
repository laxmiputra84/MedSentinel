import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.audit_log import AdminAuditLog

class AuditLogService:
    @staticmethod
    def log_action(
        db: Session,
        admin_user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        ip_address: Optional[str] = None
    ) -> Optional[AdminAuditLog]:
        """Creates an audit trail record for sensitive administrative operations."""
        if not settings.ENABLE_ADMIN_AUDIT_LOGS:
            return None

        old_val_str = json.dumps(old_value) if isinstance(old_value, (dict, list)) else (str(old_value) if old_value is not None else None)
        new_val_str = json.dumps(new_value) if isinstance(new_value, (dict, list)) else (str(new_value) if new_value is not None else None)

        log = AdminAuditLog(
            admin_user_id=admin_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            old_value=old_val_str,
            new_value=new_val_str,
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
