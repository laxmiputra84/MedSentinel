import os
import json
import traceback
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.knowledge_base import (
    KnowledgeDataset,
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeProcessingLog
)
from app.rag.document_loader import DocumentLoader
from app.rag.chunking_service import ChunkingService
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import VectorStore

class IngestionService:
    @staticmethod
    async def process_dataset(dataset_id: int, db: Session) -> bool:
        """
        Executes end-to-end asynchronous dataset ingestion and vector indexing.
        """
        dataset = db.query(KnowledgeDataset).filter(KnowledgeDataset.id == dataset_id).first()
        if not dataset:
            return False

        def add_log(status: str, msg: str):
            log = KnowledgeProcessingLog(
                dataset_id=dataset.id,
                status=status,
                message=msg,
                processed_at=datetime.now(timezone.utc)
            )
            db.add(log)
            db.commit()

        try:
            dataset.status = "PROCESSING"
            db.commit()
            add_log("STARTED", f"Initiated ingestion for dataset '{dataset.name}' ({dataset.file_name})")

            # 1. Check file existence
            if not dataset.file_path or not os.path.exists(dataset.file_path):
                # If manual or non-existent file, create a default document from description
                documents_data = [{
                    "title": dataset.name,
                    "content": dataset.description or f"Dataset {dataset.name} metadata and records.",
                    "metadata": {"source": "manual_entry"}
                }]
            else:
                # 2. Extract and load structured documents
                add_log("EXTRACTING", f"Extracting text from {dataset.file_type} file...")
                documents_data = DocumentLoader.load_dataset_content(
                    file_path=dataset.file_path,
                    dataset_name=dataset.name,
                    file_type=dataset.file_type
                )

            if not documents_data:
                raise ValueError("No text content could be extracted from the uploaded document.")

            # Clear old documents/chunks for this dataset if reprocessing
            old_docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.dataset_id == dataset.id).all()
            for od in old_docs:
                db.delete(od)
            db.commit()
            await VectorStore.delete_by_dataset(dataset.id)

            # 3. Create Documents and Chunks
            add_log("CHUNKING", f"Partitioning {len(documents_data)} sections into semantic chunks...")
            all_chunks_to_embed = []
            vector_points_to_upsert = []

            for doc_dict in documents_data:
                doc = KnowledgeDocument(
                    dataset_id=dataset.id,
                    title=doc_dict["title"],
                    content=doc_dict["content"],
                    meta_info=json.dumps(doc_dict.get("metadata", {})),
                    visibility=dataset.visibility
                )
                db.add(doc)
                db.flush() # get doc.id

                # Generate Chunks
                chunks_info = ChunkingService.create_chunks_with_metadata(
                    document_id=doc.id,
                    dataset_id=dataset.id,
                    document_title=doc.title,
                    content=doc.content,
                    hospital_id=dataset.hospital_id,
                    organization_id=dataset.organization_id,
                    visibility=dataset.visibility,
                    source=dataset.source_type
                )

                for ch in chunks_info:
                    chunk_obj = KnowledgeChunk(
                        document_id=doc.id,
                        chunk_index=ch["chunk_index"],
                        content=ch["content"],
                        meta_info=json.dumps(ch["meta_info"])
                    )
                    db.add(chunk_obj)
                    db.flush()

                    vector_id = f"ds_{dataset.id}_doc_{doc.id}_chk_{chunk_obj.id}"
                    chunk_obj.embedding_reference = vector_id
                    all_chunks_to_embed.append((chunk_obj, vector_id, ch["meta_info"]))

            db.commit()

            # 4. Generate Embeddings & Index in Vector Store
            add_log("EMBEDDING", f"Generating vector embeddings for {len(all_chunks_to_embed)} chunks...")
            for chunk_obj, vec_id, meta in all_chunks_to_embed:
                emb = await EmbeddingService.get_embedding(chunk_obj.content)
                meta["content"] = chunk_obj.content
                vector_points_to_upsert.append({
                    "id": vec_id,
                    "vector": emb,
                    "payload": meta
                })

            if not vector_points_to_upsert:
                raise ValueError("No valid vector chunks could be extracted or embedded for this dataset.")

            await VectorStore.upsert_points(vector_points_to_upsert)

            indexed_count = VectorStore.get_dataset_vector_count(dataset.id)
            if indexed_count == 0:
                raise ValueError("Vector store indexing verification returned 0 active vectors.")

            dataset.status = "READY"
            db.commit()
            add_log("COMPLETED", f"Successfully indexed {len(vector_points_to_upsert)} chunks in private vector store.")
            return True

        except Exception as e:
            trace = traceback.format_exc()
            dataset.status = "FAILED"
            db.commit()
            add_log("FAILED", f"Processing error: {str(e)}\n{trace[:300]}")
            return False
