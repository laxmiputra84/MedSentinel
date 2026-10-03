import os
import aiofiles
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_super_admin
from app.models import User, KnowledgeDataset, KnowledgeDocument, KnowledgeChunk, KnowledgeProcessingLog
from app.schemas.knowledge_base import (
    KnowledgeDatasetOut,
    KnowledgeDocumentOut,
    KnowledgeChunkOut,
    KnowledgeProcessingLogOut
)
from app.rag.ingestion_service import IngestionService
from app.rag.vector_store import VectorStore

router = APIRouter(prefix="/admin/datasets", tags=["Admin Knowledge Base"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "datasets")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("", response_model=List[KnowledgeDatasetOut])
def list_datasets(
    status_filter: Optional[str] = Query(None, alias="status"),
    visibility_filter: Optional[str] = Query(None, alias="visibility"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all knowledge datasets with RBAC filtering.
    """
    query = db.query(KnowledgeDataset)
    if status_filter and status_filter != "ALL":
        query = query.filter(KnowledgeDataset.status == status_filter)
    if visibility_filter and visibility_filter != "ALL":
        query = query.filter(KnowledgeDataset.visibility == visibility_filter)

    # Hospital admin restriction
    if current_user.role == "HOSPITAL_ADMIN" and hasattr(current_user, "hospital_id") and current_user.hospital_id:
        query = query.filter(KnowledgeDataset.hospital_id == current_user.hospital_id)

    datasets = query.order_by(KnowledgeDataset.created_at.desc()).all()

    # Precompute aggregate counts in single SQL passes
    doc_counts = dict(
        db.query(KnowledgeDocument.dataset_id, func.count(KnowledgeDocument.id))
        .group_by(KnowledgeDocument.dataset_id)
        .all()
    )
    chunk_counts = dict(
        db.query(KnowledgeDocument.dataset_id, func.count(KnowledgeChunk.id))
        .join(KnowledgeChunk, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .group_by(KnowledgeDocument.dataset_id)
        .all()
    )

    results = []
    for d in datasets:
        doc_count = doc_counts.get(d.id, 0)
        chunk_count = chunk_counts.get(d.id, 0)
        vec_count = VectorStore.get_dataset_vector_count(d.id)
        
        d_out = KnowledgeDatasetOut(
            id=d.id,
            name=d.name,
            description=d.description,
            file_name=d.file_name,
            file_type=d.file_type,
            source_type=d.source_type,
            uploaded_by=d.uploaded_by,
            status=d.status,
            visibility=d.visibility,
            hospital_id=d.hospital_id,
            organization_id=d.organization_id,
            document_count=doc_count,
            chunk_count=chunk_count,
            vector_count=vec_count,
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        results.append(d_out)
    return results

@router.post("/upload", response_model=KnowledgeDatasetOut)
async def upload_dataset(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    visibility: str = Form("USER_AUTHORIZED"),
    source_type: str = Form("ADMIN_UPLOAD"),
    hospital_id: Optional[int] = Form(None),
    organization_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and ingest a dataset (PDF, DOCX, CSV, XLSX, TXT).
    Admin uploads are automatically set to READY after processing.
    Employee uploads may require admin review if review workflow is active.
    """
    saved_file_path = None
    file_type = "MANUAL"
    filename = None

    if file:
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower().replace(".", "")
        file_type = ext.upper() if ext else "TXT"

        saved_file_path = os.path.join(UPLOAD_DIR, f"{int(os.times().elapsed)}_{filename}")
        async with aiofiles.open(saved_file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

    # Initial status
    initial_status = "PENDING_REVIEW" if (current_user.role == "USER" or source_type == "EMPLOYEE_UPLOAD") else "UPLOADED"

    dataset = KnowledgeDataset(
        name=name,
        description=description,
        file_name=filename,
        file_type=file_type,
        file_path=saved_file_path,
        source_type=source_type,
        uploaded_by=current_user.id,
        status=initial_status,
        visibility=visibility,
        hospital_id=hospital_id,
        organization_id=organization_id
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Automatically process if admin upload
    if initial_status == "UPLOADED":
        await IngestionService.process_dataset(dataset.id, db)
        db.refresh(dataset)

    return dataset

@router.post("/{dataset_id}/approve")
async def approve_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Approve a pending employee dataset and trigger vector indexing."""
    dataset = db.query(KnowledgeDataset).filter(KnowledgeDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset.status = "APPROVED"
    db.commit()

    await IngestionService.process_dataset(dataset.id, db)
    return {"message": f"Dataset '{dataset.name}' approved and indexed."}

@router.post("/{dataset_id}/reject")
def reject_dataset(
    dataset_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Reject a dataset from being indexed into the private AI knowledge base."""
    dataset = db.query(KnowledgeDataset).filter(KnowledgeDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset.status = "REJECTED"
    db.commit()
    return {"message": f"Dataset '{dataset.name}' rejected."}

@router.post("/{dataset_id}/reprocess")
async def reprocess_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Re-extract, re-chunk, and re-index dataset into vector store."""
    dataset = db.query(KnowledgeDataset).filter(KnowledgeDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    success = await IngestionService.process_dataset(dataset.id, db)
    return {"message": f"Dataset '{dataset.name}' reprocessed.", "success": success}

@router.patch("/{dataset_id}/toggle-status")
def toggle_dataset_status(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enable or disable dataset from AI retrieval without deleting files."""
    dataset = db.query(KnowledgeDataset).filter(KnowledgeDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset.status = "DISABLED" if dataset.status != "DISABLED" else "READY"
    db.commit()
    return {"status": dataset.status, "message": f"Dataset status changed to {dataset.status}"}

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Completely delete dataset, documents, chunks, vectors, and physical files."""
    dataset = db.query(KnowledgeDataset).filter(KnowledgeDataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Delete physical file
    if dataset.file_path and os.path.exists(dataset.file_path):
        try:
            os.remove(dataset.file_path)
        except Exception:
            pass

    # Delete vectors from VectorStore
    await VectorStore.delete_by_dataset(dataset.id)

    db.delete(dataset)
    db.commit()
    return None

@router.get("/{dataset_id}/documents", response_model=List[KnowledgeDocumentOut])
def get_dataset_documents(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """View extracted document sections."""
    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.dataset_id == dataset_id).all()
    return docs

@router.get("/{dataset_id}/chunks", response_model=List[KnowledgeChunkOut])
def get_dataset_chunks(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """View generated semantic chunks and vector references."""
    chunks = db.query(KnowledgeChunk).join(KnowledgeDocument).filter(
        KnowledgeDocument.dataset_id == dataset_id
    ).all()
    return chunks

@router.get("/{dataset_id}/logs", response_model=List[KnowledgeProcessingLogOut])
def get_dataset_logs(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """View processing and indexing log history for dataset."""
    logs = db.query(KnowledgeProcessingLog).filter(
        KnowledgeProcessingLog.dataset_id == dataset_id
    ).order_by(KnowledgeProcessingLog.processed_at.desc()).all()
    return logs
