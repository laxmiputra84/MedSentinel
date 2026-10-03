from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import require_super_admin
from app.models import User
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])

class UserAdminUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None # USER, HOSPITAL_ADMIN, INSURANCE_ADMIN, SUPER_ADMIN
    is_active: Optional[bool] = None
    hospital_id: Optional[int] = None
    insurance_id: Optional[int] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = None

@router.get("")
def list_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """List, search, and filter all registered users across the platform."""
    query = db.query(User)
    if search:
        s = f"%{search}%"
        query = query.filter((User.name.ilike(s)) | (User.email.ilike(s)) | (User.phone.ilike(s)))
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "is_active": u.is_active,
            "hospital_id": u.hospital_id,
            "insurance_id": u.insurance_id,
            "blood_group": u.blood_group,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items
    }

@router.get("/{user_id}")
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Retrieve detailed user profile for administration."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "hospital_id": user.hospital_id,
        "insurance_id": user.insurance_id,
        "blood_group": user.blood_group,
        "allergies": user.allergies,
        "emergency_contact": user.emergency_contact,
        "schemes": user.schemes,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None
    }

@router.put("/{user_id}")
def update_user(
    user_id: int,
    payload: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Update user information, assign roles, or toggle active status with self-protection."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Critical Self-Protection: Super Admin cannot downgrade their own role or deactivate themselves
    if user.id == current_admin.id:
        if payload.role and payload.role != "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Protection: You cannot remove your own SUPER_ADMIN role."
            )
        if payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Protection: You cannot deactivate your own administrative account."
            )

    old_data = {"name": user.name, "role": user.role, "is_active": user.is_active}

    if payload.name is not None:
        user.name = payload.name
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.role is not None:
        if payload.role not in ["USER", "HOSPITAL_ADMIN", "INSURANCE_ADMIN", "SUPER_ADMIN"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role specified.")
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.hospital_id is not None:
        user.hospital_id = payload.hospital_id
    if payload.insurance_id is not None:
        user.insurance_id = payload.insurance_id
    if payload.blood_group is not None:
        user.blood_group = payload.blood_group
    if payload.allergies is not None:
        user.allergies = payload.allergies
    if payload.emergency_contact is not None:
        user.emergency_contact = payload.emergency_contact

    db.commit()
    db.refresh(user)

    # Log action
    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="USER_UPDATED",
        resource_type="User",
        resource_id=str(user.id),
        old_value=old_data,
        new_value={"name": user.name, "role": user.role, "is_active": user.is_active}
    )

    return {"message": "User updated successfully.", "user_id": user.id, "role": user.role, "is_active": user.is_active}

@router.patch("/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Quickly toggle active/inactive status of a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Protection: You cannot deactivate your own administrative account."
        )

    user.is_active = not user.is_active
    db.commit()

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="USER_STATUS_TOGGLED",
        resource_type="User",
        resource_id=str(user.id),
        new_value={"is_active": user.is_active}
    )

    return {"message": f"User status set to {'active' if user.is_active else 'inactive'}.", "is_active": user.is_active}
