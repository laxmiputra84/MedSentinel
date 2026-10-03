import os
import json
import math
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings

class VectorStorePoint:
    def __init__(
        self,
        id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ):
        self.id = id
        self.vector = vector
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "vector": self.vector,
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorStorePoint":
        return cls(
            id=data["id"],
            vector=data["vector"],
            payload=data["payload"]
        )

class VectorStore:
    """
    Hybrid Vector Store providing:
    1. Qdrant REST/gRPC client integration
    2. High-performance local in-memory vector index with persistence and DB auto-hydration
    """
    _local_store: Dict[str, VectorStorePoint] = {}
    _is_qdrant_available: Optional[bool] = None
    _storage_file: str = os.path.join(os.getcwd(), "uploads", "vector_store", "index.json")

    @classmethod
    def _save_to_disk(cls):
        try:
            os.makedirs(os.path.dirname(cls._storage_file), exist_ok=True)
            data = {pid: pt.to_dict() for pid, pt in cls._local_store.items()}
            temp_file = f"{cls._storage_file}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
            if os.path.exists(cls._storage_file):
                os.remove(cls._storage_file)
            os.rename(temp_file, cls._storage_file)
        except Exception as e:
            pass

    @classmethod
    def load_from_disk(cls) -> int:
        try:
            if os.path.exists(cls._storage_file):
                with open(cls._storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cls._local_store = {pid: VectorStorePoint.from_dict(val) for pid, val in data.items()}
                return len(cls._local_store)
        except Exception:
            pass
        return 0

    @classmethod
    async def hydrate_from_db(cls, db: Session) -> int:
        """
        Ensures all chunks belonging to READY/APPROVED datasets in MySQL are indexed in the vector store.
        """
        from app.models.knowledge_base import KnowledgeDataset, KnowledgeDocument, KnowledgeChunk
        from app.rag.embedding_service import EmbeddingService

        cls.load_from_disk()

        ready_datasets = db.query(KnowledgeDataset).filter(
            KnowledgeDataset.status.in_(["READY", "APPROVED"])
        ).all()
        ready_dataset_ids = {ds.id for ds in ready_datasets}

        # Purge disabled or non-existent datasets from local store
        stale_pids = [
            pid for pid, pt in cls._local_store.items()
            if pt.payload.get("dataset_id") not in ready_dataset_ids
        ]
        for pid in stale_pids:
            cls._local_store.pop(pid, None)

        points_to_save = []
        for ds in ready_datasets:
            docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.dataset_id == ds.id).all()
            for doc in docs:
                chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).all()
                for chk in chunks:
                    vec_id = chk.embedding_reference or f"ds_{ds.id}_doc_{doc.id}_chk_{chk.id}"
                    if vec_id in cls._local_store:
                        continue

                    meta = {}
                    try:
                        if chk.meta_info:
                            meta = json.loads(chk.meta_info)
                    except Exception:
                        pass
                    meta["content"] = chk.content
                    meta["dataset_id"] = ds.id
                    meta["document_id"] = doc.id
                    meta["document_title"] = doc.title
                    meta["visibility"] = ds.visibility
                    meta["hospital_id"] = ds.hospital_id
                    meta["allowed_roles"] = ["SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN", "USER"]

                    emb = await EmbeddingService.get_embedding(chk.content)
                    points_to_save.append({
                        "id": vec_id,
                        "vector": emb,
                        "payload": meta
                    })

        if points_to_save or stale_pids:
            if points_to_save:
                await cls.upsert_points(points_to_save)
            else:
                cls._save_to_disk()

        return len(cls._local_store)

    @classmethod
    async def check_qdrant_health(cls) -> bool:
        """Checks if Qdrant instance is reachable."""
        try:
            url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/healthz"
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(url)
                cls._is_qdrant_available = (res.status_code == 200)
                return cls._is_qdrant_available
        except Exception:
            cls._is_qdrant_available = False
            return False

    @classmethod
    async def upsert_points(cls, points: List[Dict[str, Any]]) -> bool:
        """
        Upserts vector points.
        Each item in points: {"id": str, "vector": List[float], "payload": dict}
        """
        # Save to local store
        for p in points:
            cls._local_store[p["id"]] = VectorStorePoint(
                id=p["id"],
                vector=p["vector"],
                payload=p["payload"]
            )
        cls._save_to_disk()

        # Attempt Qdrant upsert if available
        try:
            is_qdrant = await cls.check_qdrant_health()
            if is_qdrant:
                from qdrant_client import QdrantClient
                from qdrant_client.models import PointStruct, Distance, VectorParams
                client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=3.0)
                
                # Ensure collection exists
                collections = client.get_collections().collections
                exists = any(c.name == settings.QDRANT_COLLECTION for c in collections)
                if not exists:
                    client.create_collection(
                        collection_name=settings.QDRANT_COLLECTION,
                        vectors_config=VectorParams(size=len(points[0]["vector"]), distance=Distance.COSINE)
                    )
                
                q_points = [
                    PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
                    for p in points
                ]
                client.upsert(collection_name=settings.QDRANT_COLLECTION, points=q_points)
        except Exception:
            pass

        return True

    @classmethod
    async def delete_by_dataset(cls, dataset_id: int) -> int:
        """Deletes all indexed vectors belonging to a dataset."""
        to_delete = [
            pid for pid, p in cls._local_store.items()
            if p.payload.get("dataset_id") == dataset_id
        ]
        for pid in to_delete:
            cls._local_store.pop(pid, None)

        cls._save_to_disk()

        try:
            if cls._is_qdrant_available:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=2.0)
                client.delete(
                    collection_name=settings.QDRANT_COLLECTION,
                    points_selector=Filter(
                        must=[FieldCondition(key="dataset_id", match=MatchValue(value=dataset_id))]
                    )
                )
        except Exception:
            pass

        return len(to_delete)

    @classmethod
    async def search_vectors(
        cls,
        query_vector: List[float],
        user_role: str,
        user_id: Optional[int] = None,
        user_hospital_id: Optional[int] = None,
        limit: int = 6,
        score_threshold: float = 0.08
    ) -> List[Dict[str, Any]]:
        """
        Executes strict permission-filtered vector similarity search.
        Matches only datasets and chunks permitted for user_role and user_hospital_id.
        """
        # Ensure points loaded
        if len(cls._local_store) == 0:
            cls.load_from_disk()

        candidates: List[Dict[str, Any]] = []

        # Local cosine similarity scan with strict RBAC filtering
        for pid, pt in cls._local_store.items():
            payload = pt.payload

            # 1. RBAC Check: Allowed Roles
            allowed_roles = payload.get("allowed_roles", [])
            if allowed_roles and user_role not in allowed_roles and user_role != "SUPER_ADMIN":
                continue

            # 2. Visibility and Hospital Isolation Check
            vis = payload.get("visibility", "USER_AUTHORIZED")
            if vis == "SUPER_ADMIN_ONLY" and user_role != "SUPER_ADMIN":
                continue

            if vis == "PRIVATE_ADMIN" and user_role not in ["SUPER_ADMIN", "HOSPITAL_ADMIN", "INSURANCE_ADMIN"]:
                continue

            if vis == "PRIVATE_HOSPITAL":
                chunk_hosp = payload.get("hospital_id")
                if user_role != "SUPER_ADMIN" and (not user_hospital_id or user_hospital_id != chunk_hosp):
                    continue

            # 3. Compute Cosine Similarity
            dot_product = sum(a * b for a, b in zip(query_vector, pt.vector))
            norm_q = math.sqrt(sum(a * a for a in query_vector))
            norm_v = math.sqrt(sum(b * b for b in pt.vector))
            similarity = dot_product / (norm_q * norm_v) if (norm_q > 0 and norm_v > 0) else 0.0

            if similarity >= score_threshold:
                candidates.append({
                    "id": pid,
                    "score": round(similarity, 4),
                    "confidence": round(similarity, 2),
                    "content": payload.get("content", ""),
                    "title": payload.get("document_title", "Knowledge Document"),
                    "dataset_id": payload.get("dataset_id"),
                    "document_id": payload.get("document_id"),
                    "hospital_id": payload.get("hospital_id"),
                    "visibility": vis,
                    "metadata": payload
                })

        # Sort descending by similarity score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:limit]

    @classmethod
    def get_indexed_points_count(cls) -> int:
        """Returns total active vector count in index."""
        if len(cls._local_store) == 0:
            cls.load_from_disk()
        return len(cls._local_store)

    @classmethod
    def get_dataset_vector_count(cls, dataset_id: int) -> int:
        """Returns number of indexed vectors for a dataset."""
        if len(cls._local_store) == 0:
            cls.load_from_disk()
        return sum(1 for pt in cls._local_store.values() if pt.payload.get("dataset_id") == dataset_id)

    @classmethod
    def get_collection_name(cls) -> str:
        """Returns configured Qdrant collection name."""
        return settings.QDRANT_COLLECTION

