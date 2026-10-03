"""
MedSentinel Agentic Architecture — Redis Event Bus
High-throughput event infrastructure supporting Redis Pub/Sub with resilient in-memory fallback.
Streams real-time agent lifecycle events to Next.js via Server-Sent Events (SSE).
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger("medsentinel.events")


class AgentEventType(str, Enum):
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    PLAN_CREATED = "PLAN_CREATED"
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_PROGRESS = "AGENT_PROGRESS"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    RETRY_STARTED = "RETRY_STARTED"
    REPLAN_STARTED = "REPLAN_STARTED"
    SAFETY_REVIEW = "SAFETY_REVIEW"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"
    WORKFLOW_CANCELLED = "WORKFLOW_CANCELLED"


class RedisEventBus:
    """
    Dual-mode Event Bus:
    - Primary: Redis Pub/Sub across multi-node workers
    - Fallback: High-performance Asyncio Queues when Redis is unavailable
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self._redis_client = None
        self._redis_connected = False
        self._connection_checked = False
        
        # In-memory pub/sub & replay buffers
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._event_history: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def _get_redis(self):
        """Attempts connection to Redis if not checked yet."""
        if not self._connection_checked:
            self._connection_checked = True
            try:
                import redis.asyncio as aioredis
                client = aioredis.from_url(self.redis_url, socket_timeout=1.5)
                await client.ping()
                self._redis_client = client
                self._redis_connected = True
                logger.info("Connected to Redis Event Bus successfully at %s", self.redis_url)
            except Exception as e:
                self._redis_connected = False
                logger.info("Redis not reachable (%s); operating in High-Performance Local Asyncio Event Mode.", str(e))
        return self._redis_client if self._redis_connected else None

    async def publish(
        self,
        workflow_id: str,
        event_type: AgentEventType | str,
        data: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Publishes an event to Redis (if enabled) and local subscriber queues.
        Persists into MySQL workflow_events table if db session provided.
        """
        evt_name = event_type.value if isinstance(event_type, AgentEventType) else str(event_type)
        payload = {
            "workflow_id": workflow_id,
            "event": evt_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        # 1. Append to in-memory replay buffer (last 100 events per workflow)
        if workflow_id not in self._event_history:
            self._event_history[workflow_id] = []
        self._event_history[workflow_id].append(payload)
        if len(self._event_history[workflow_id]) > 100:
            self._event_history[workflow_id].pop(0)

        # 2. Publish to local asyncio subscribers
        queues = self._subscribers.get(workflow_id, [])
        for q in list(queues):
            try:
                await q.put(payload)
            except Exception:
                pass

        # 3. Publish to Redis if available
        redis_client = await self._get_redis()
        if redis_client:
            try:
                channel = f"workflow:{workflow_id}"
                await redis_client.publish(channel, json.dumps(payload))
                await redis_client.publish("workflows:all", json.dumps(payload))
            except Exception as re:
                logger.warning("Failed to publish to Redis channel: %s", str(re))

        # 4. Durable persistence to MySQL
        if db:
            try:
                from app.models.workflow import WorkflowEventRecord
                evt_rec = WorkflowEventRecord(
                    workflow_id=workflow_id,
                    event_type=evt_name,
                    payload_json=json.dumps(data)
                )
                db.add(evt_rec)
                db.commit()
            except Exception as dbe:
                logger.warning("Failed to record workflow event to DB: %s", str(dbe))
                try:
                    db.rollback()
                except Exception:
                    pass

        return payload

    async def subscribe(self, workflow_id: str) -> AsyncGenerator[str, None]:
        """
        Yields Server-Sent Events (SSE) for a workflow.
        First replays existing history, then streams live events.
        """
        queue: asyncio.Queue = asyncio.Queue()

        if workflow_id not in self._subscribers:
            self._subscribers[workflow_id] = []
        self._subscribers[workflow_id].append(queue)

        try:
            # 1. Replay historical events
            past_events = list(self._event_history.get(workflow_id, []))
            for evt in past_events:
                yield f"event: {evt['event']}\ndata: {json.dumps(evt['data'])}\n\n"
                evt_name = str(evt.get("event", "")).upper()
                if evt_name in ["WORKFLOW_COMPLETED", "WORKFLOW_FAILED", "WORKFLOW_CANCELLED"]:
                    return

            # 2. Stream live events
            while True:
                try:
                    evt = await asyncio.wait_for(queue.get(), timeout=3.0)
                    yield f"event: {evt['event']}\ndata: {json.dumps(evt['data'])}\n\n"
                    evt_name = str(evt.get("event", "")).upper()
                    if evt_name in ["WORKFLOW_COMPLETED", "WORKFLOW_FAILED", "WORKFLOW_CANCELLED"]:
                        break
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            if workflow_id in self._subscribers and queue in self._subscribers[workflow_id]:
                self._subscribers[workflow_id].remove(queue)

    def get_event_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Returns the in-memory or persisted event history for a workflow."""
        return list(self._event_history.get(workflow_id, []))


# Global singleton instance
redis_event_bus = RedisEventBus()
