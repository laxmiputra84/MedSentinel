from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import require_super_admin
from app.models import User, Scheme
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/admin/schemes", tags=["Admin - Schemes"])

class SchemeCreateUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    coverage: Optional[str] = None
    eligibility: Optional[str] = None
    benefits: Optional[str] = None
    category: Optional[str] = "National Government"
    max_income: Optional[str] = None
    type: Optional[str] = "government"

@router.get("")
def list_schemes(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """List all government health schemes and eligibility criteria."""
    schemes = db.query(Scheme).all()
    return schemes

@router.post("", status_code=status.HTTP_201_CREATED)
def create_scheme(
    payload: SchemeCreateUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Create a new government health scheme."""
    scheme = Scheme(**payload.dict())
    db.add(scheme)
    db.commit()
    db.refresh(scheme)

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="SCHEME_CREATED",
        resource_type="Scheme",
        resource_id=str(scheme.id),
        new_value={"name": scheme.name}
    )

    return scheme

@router.put("/{scheme_id}")
def update_scheme(
    scheme_id: int,
    payload: SchemeCreateUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """Update government scheme criteria and benefits."""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheme not found.")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(scheme, key, value)

    db.commit()
    db.refresh(scheme)

    AuditLogService.log_action(
        db=db,
        admin_user_id=current_admin.id,
        action="SCHEME_UPDATED",
        resource_type="Scheme",
        resource_id=str(scheme.id),
        new_value={"name": scheme.name}
    )

    return scheme
