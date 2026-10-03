import os
import aiofiles
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User, Hospital, HospitalImage
from app.schemas.knowledge_base import HospitalImageOut

router = APIRouter(prefix="/admin/hospitals", tags=["Admin Hospital Media"])

HOSPITAL_UPLOADS_ROOT = os.path.join(os.getcwd(), "uploads", "hospitals")
os.makedirs(HOSPITAL_UPLOADS_ROOT, exist_ok=True)

@router.get("/{hospital_id}/media", response_model=List[HospitalImageOut])
def list_hospital_media(
    hospital_id: int,
    image_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all registered photos, documents, and facility assets for a hospital."""
    query = db.query(HospitalImage).filter(HospitalImage.hospital_id == hospital_id)
    if image_type and image_type != "ALL":
        query = query.filter(HospitalImage.image_type == image_type)
    return query.order_by(HospitalImage.created_at.desc()).all()

@router.post("/{hospital_id}/media/upload", response_model=HospitalImageOut)
async def upload_hospital_media(
    hospital_id: int,
    image_type: str = Form("GALLERY"), # LOGO, COVER, GALLERY, FACILITY, DOCTOR, DOCUMENT
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and register media for a hospital facility.
    Organizes files into structured storage: uploads/hospitals/{hospital_id}/{image_type}/
    """
    hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    sub_dir = os.path.join(HOSPITAL_UPLOADS_ROOT, str(hospital_id), image_type.lower())
    os.makedirs(sub_dir, exist_ok=True)

    filename = file.filename
    dest_path = os.path.join(sub_dir, f"{int(os.times().elapsed)}_{filename}")
    async with aiofiles.open(dest_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    rel_path = os.path.relpath(dest_path, os.getcwd()).replace("\\", "/")

    media_obj = HospitalImage(
        hospital_id=hospital_id,
        file_path=rel_path,
        image_type=image_type.upper(),
        title=title or filename,
        description=description,
        is_approved_by_admin=True,
        uploaded_by=current_user.id,
        is_active=True
    )
    db.add(media_obj)
    db.commit()
    db.refresh(media_obj)
    return media_obj

@router.delete("/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hospital_media(
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a hospital media asset and its local storage file."""
    img = db.query(HospitalImage).filter(HospitalImage.id == media_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Media not found")

    full_path = os.path.join(os.getcwd(), img.file_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except Exception:
            pass

    db.delete(img)
    db.commit()
    return None
