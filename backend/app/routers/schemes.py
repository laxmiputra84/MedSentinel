from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.scheme import Scheme
from app.schemas.scheme import SchemeResponse

router = APIRouter(prefix="/schemes", tags=["Government Schemes"])

@router.get("", response_model=List[SchemeResponse])
def list_schemes(db: Session = Depends(get_db)):
    """Retrieve all available government healthcare schemes."""
    return db.query(Scheme).all()

@router.get("/{scheme_id}", response_model=SchemeResponse)
def get_scheme_by_id(scheme_id: int, db: Session = Depends(get_db)):
    """Retrieve details for a specific government scheme."""
    scheme = db.query(Scheme).filter(Scheme.id == scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found"
        )
    return scheme
