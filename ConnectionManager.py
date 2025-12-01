from typing import List
from fastapi import WebSocket
import asyncio
import json


class ConnectionManager:
    """
    Thread-safe manager for WebSocket connections.
    Provides connect/disconnect, personal send, text/json broadcast, and helpers.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        # attempt close if still open (safe)
        try:
            await websocket.close()
        except Exception:
            pass

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """
        Send a text message to a single websocket. Removes the connection on failure.
        """
        try:
            await websocket.send_text(message)
        except Exception:
            await self.disconnect(websocket)

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a text message to all active connections.
        """
        async with self._lock:
            conns = list(self.active_connections)
        if not conns:
            return
        await asyncio.gather(*(self._safe_send(c, message) for c in conns), return_exceptions=True)

    async def broadcast_json(self, obj) -> None:
        """
        Broadcast a JSON-serializable object to all active connections.
        """
        payload = json.dumps(obj)
        await self.broadcast(payload)

    async def _safe_send(self, connection: WebSocket, message: str) -> None:
        try:
            await connection.send_text(message)
        except Exception:
            # on failure, remove the broken connection
            await self.disconnect(connection)

    async def is_connected(self, websocket: WebSocket) -> bool:
        async with self._lock:
            return websocket in self.active_connections

    async def count(self) -> int:
        async with self._lock:
            return len(self.active_connections)

    async def get_active_connections(self) -> List[WebSocket]:
        async with self._lock:
            return list(self.active_connections)
