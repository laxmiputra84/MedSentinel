from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.dependencies.auth import require_super_admin
from app.models import User, KnowledgeDataset
from app.models.ai_monitoring import AIRequestLog
from app.ai.provider import AIProvider
from app.rag.vector_store import VectorStore

router = APIRouter(prefix="/admin/ai-monitoring", tags=["Admin AI Monitoring"])

@router.get("/stats")
def get_ai_monitoring_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Returns live operational statistics: total queries, latency, tokens used,
    error breakdown, and provider health.
    """
    total_requests = db.query(AIRequestLog).count()
    success_requests = db.query(AIRequestLog).filter(AIRequestLog.status == "SUCCESS").count()
    error_requests = db.query(AIRequestLog).filter(AIRequestLog.status == "ERROR").count()
    rate_limited = db.query(AIRequestLog).filter(AIRequestLog.status == "RATE_LIMITED").count()

    avg_latency = db.query(func.avg(AIRequestLog.latency_ms)).scalar() or 0.0
    total_tokens = db.query(func.sum(AIRequestLog.tokens_used)).scalar() or 0

    total_datasets = db.query(KnowledgeDataset).count()
    active_datasets = db.query(KnowledgeDataset).filter(KnowledgeDataset.status == "READY").count()

    health = AIProvider.get_health()
    health["indexed_vectors"] = VectorStore.get_indexed_points_count()

    return {
        "total_requests": total_requests,
        "success_requests": success_requests,
        "error_requests": error_requests,
        "rate_limited_requests": rate_limited,
        "success_rate_percent": round((success_requests / max(total_requests, 1)) * 100, 1),
        "avg_latency_ms": round(float(avg_latency), 2),
        "total_tokens_used": int(total_tokens),
        "total_datasets": total_datasets,
        "active_datasets": active_datasets,
        "provider_health": health
    }

@router.get("/logs")
def get_ai_request_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """
    Retrieve paginated audit logs of AI queries, latency, and tool invocations.
    """
    query = db.query(AIRequestLog)
    if status_filter and status_filter != "ALL":
        query = query.filter(AIRequestLog.status == status_filter)

    total = query.count()
    logs = query.order_by(AIRequestLog.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = []
    for l in logs:
        items.append({
            "id": l.id,
            "user_id": l.user_id,
            "user_name": l.user.name if l.user else "System/Guest",
            "conversation_id": l.conversation_id,
            "request_type": l.request_type,
            "provider": l.provider,
            "model": l.model,
            "status": l.status,
            "latency_ms": l.latency_ms,
            "tokens_used": l.tokens_used,
            "datasets_used": l.datasets_used,
            "tools_used": l.tools_used,
            "error_code": l.error_code,
            "user_query_preview": l.user_query_preview,
            "created_at": l.created_at.isoformat() if l.created_at else ""
        })

    return {"total": total, "page": page, "limit": limit, "items": items}
