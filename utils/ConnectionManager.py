from typing import List, Dict, Optional
from fastapi import WebSocket
import asyncio
import json


class ConnectionManager:
    """
    Room-aware, async-safe WebSocket connection manager.
    Stores connections as: { room_id: [WebSocket, ...], ... }
    """
    def __init__(self):
        self._rooms: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(room_id, []).append(websocket)

    async def disconnect(self, websocket: WebSocket, room_id: Optional[str] = None) -> None:
        """
        Remove websocket from the specified room.
        If room_id is None, attempt to find the websocket in any room and remove it.
        """
        async with self._lock:
            if room_id is not None:
                conns = self._rooms.get(room_id)
                if conns and websocket in conns:
                    conns.remove(websocket)
                    if not conns:
                        self._rooms.pop(room_id, None)
            else:
                # find and remove from whichever room it's in
                found_rooms = []
                for rid, conns in list(self._rooms.items()):
                    if websocket in conns:
                        conns.remove(websocket)
                        if not conns:
                            found_rooms.append(rid)
                for rid in found_rooms:
                    self._rooms.pop(rid, None)
        # try to close socket (safe)
        try:
            await websocket.close()
        except Exception:
            pass

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        try:
            await websocket.send_text(message)
        except Exception:
            await self.disconnect(websocket)

    async def broadcast(self, message: str, room_id: str) -> None:
        """
        Broadcast plain text to all connections in a room.
        """
        async with self._lock:
            conns = list(self._rooms.get(room_id, []))
        if not conns:
            return
        await asyncio.gather(*(self._safe_send(c, message) for c in conns), return_exceptions=True)

    async def broadcast_json(self, obj, room_id: str) -> None:
        payload = json.dumps(obj)
        await self.broadcast(payload, room_id)

    async def _safe_send(self, connection: WebSocket, message: str) -> None:
        try:
            await connection.send_text(message)
        except Exception:
            await self.disconnect(connection)

    async def is_connected(self, websocket: WebSocket, room_id: Optional[str] = None) -> bool:
        async with self._lock:
            if room_id is not None:
                return websocket in self._rooms.get(room_id, [])
            return any(websocket in conns for conns in self._rooms.values())

    async def count(self, room_id: Optional[str] = None) -> int:
        async with self._lock:
            if room_id is not None:
                return len(self._rooms.get(room_id, []))
            return sum(len(conns) for conns in self._rooms.values())

    async def get_active_connections(self, room_id: Optional[str] = None) -> List[WebSocket]:
        async with self._lock:
            if room_id is not None:
                return list(self._rooms.get(room_id, []))
            # return flatten list of all connections
            result: List[WebSocket] = []
            for conns in self._rooms.values():
                result.extend(conns)
            return result
