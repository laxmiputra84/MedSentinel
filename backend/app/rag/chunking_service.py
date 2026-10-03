import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class ChunkingService:
    @staticmethod
    def chunk_text(
        content: str,
        chunk_size: int = 500, # words
        chunk_overlap: int = 80 # words
    ) -> List[str]:
        """
        Splits text content into semantic chunks with sliding-window word overlap.
        Preserves natural paragraph boundaries where possible.
        """
        if not content or not content.strip():
            return []

        paragraphs = content.split("\n\n")
        chunks: List[str] = []
        current_words: List[str] = []

        for p in paragraphs:
            p_words = p.strip().split()
            if not p_words:
                continue

            if len(current_words) + len(p_words) <= chunk_size:
                current_words.extend(p_words)
            else:
                if current_words:
                    chunks.append(" ".join(current_words))
                    # Retain overlap from end of current chunk
                    current_words = current_words[-chunk_overlap:] if len(current_words) > chunk_overlap else []
                # If paragraph itself is larger than chunk_size, split by sliding window
                while len(p_words) > chunk_size:
                    chunk_slice = p_words[:chunk_size]
                    chunks.append(" ".join(chunk_slice))
                    p_words = p_words[chunk_size - chunk_overlap:]
                current_words.extend(p_words)

        if current_words:
            chunks.append(" ".join(current_words))

        return chunks

    @staticmethod
    def create_chunks_with_metadata(
        document_id: int,
        dataset_id: int,
        document_title: str,
        content: str,
        hospital_id: Optional[int] = None,
        organization_id: Optional[int] = None,
        visibility: str = "USER_AUTHORIZED",
        allowed_roles: Optional[List[str]] = None,
        source: str = "ADMIN_UPLOAD"
    ) -> List[Dict[str, Any]]:
        """
        Splits document into indexed chunks with security and authorization metadata attached.
        """
        raw_chunks = ChunkingService.chunk_text(content)
        chunk_records = []

        now_iso = datetime.now(timezone.utc).isoformat()
        roles_list = allowed_roles if allowed_roles else ["SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN", "USER"]

        for idx, chunk_str in enumerate(raw_chunks):
            meta = {
                "dataset_id": dataset_id,
                "document_id": document_id,
                "document_title": document_title,
                "hospital_id": hospital_id,
                "organization_id": organization_id,
                "visibility": visibility,
                "allowed_roles": roles_list,
                "source": source,
                "chunk_index": idx,
                "created_at": now_iso
            }

            chunk_records.append({
                "document_id": document_id,
                "chunk_index": idx,
                "content": chunk_str,
                "meta_info": meta
            })

        return chunk_records
