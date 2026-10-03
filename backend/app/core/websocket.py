"""
WebSocket Connection Manager for MedSentinel Event-Driven Architecture.
Provides real-time broadcasting of healthcare events, active agent steps,
task statuses, progress updates, and error alerts to frontend clients.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("medsentinel.websocket")


class ConnectionManager:
    def __init__(self):
        # Active connections: map websocket -> user_id (or None)
        self.active_connections: Dict[WebSocket, Optional[int]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None):
        await websocket.accept()
        async with self._lock:
            self.active_connections[websocket] = user_id
        logger.info(f"WebSocket connected. Total active: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                del self.active_connections[websocket]
        logger.info(f"WebSocket disconnected. Remaining: {len(self.active_connections)}")

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)

    async def broadcast(self, message: dict):
        """
        Broadcasts message to all connected clients.
        Automatically cleans up disconnected or broken sockets.
        """
        if not self.active_connections:
            return

        payload = json.dumps(message)
        dead_sockets: List[WebSocket] = []

        async with self._lock:
            for ws in list(self.active_connections.keys()):
                try:
                    await ws.send_text(payload)
                except Exception as exc:
                    logger.debug(f"Failed to send to websocket: {exc}")
                    dead_sockets.append(ws)

            for dead in dead_sockets:
                if dead in self.active_connections:
                    del self.active_connections[dead]

    async def send_to_user(self, user_id: int, message: dict):
        """Sends a message strictly to the specified user's connection(s)."""
        payload = json.dumps(message)
        dead_sockets: List[WebSocket] = []

        async with self._lock:
            for ws, uid in list(self.active_connections.items()):
                if uid == user_id:
                    try:
                        await ws.send_text(payload)
                    except Exception:
                        dead_sockets.append(ws)

            for dead in dead_sockets:
                if dead in self.active_connections:
                    del self.active_connections[dead]


# Global WebSocket Connection Manager Singleton
ws_manager = ConnectionManager()
