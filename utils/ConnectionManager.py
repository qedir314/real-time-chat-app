from typing import List, Dict, Optional
from fastapi import WebSocket
import asyncio
import json
import redis.asyncio as aioredis
import os


class ConnectionManager:
    """
    Room-aware, async-safe WebSocket connection manager with Redis pub/sub.
    Stores connections as: { room_id: [WebSocket, ...], ... }
    Uses Redis to sync messages across multiple server instances.
    """
    def __init__(self):
        self._rooms: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._redis_client: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._subscribed_rooms: set = set()
        self._listener_task: Optional[asyncio.Task] = None

    async def initialize_redis(self):
        """Initialize Redis connection for pub/sub"""
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        try:
            self._redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self._pubsub = self._redis_client.pubsub()
            print(f"✓ Redis connected: {redis_url}")
            # Start listener task
            self._listener_task = asyncio.create_task(self._redis_listener())
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("   Running in single-instance mode (no horizontal scaling)")
            self._redis_client = None
            self._pubsub = None

    async def _redis_listener(self):
        """Background task that listens for Redis pub/sub messages"""
        if not self._pubsub:
            return

        try:
            while True:
                try:
                    # Only try to get messages if we have subscriptions
                    if len(self._subscribed_rooms) > 0:
                        message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                        if message and message['type'] == 'message':
                            channel = message['channel']
                            data = message['data']

                            # Extract room_id from channel name (format: chat_room_{room_id})
                            if channel.startswith("chat_room_"):
                                room_id = channel[10:]  # Remove "chat_room_" prefix
                                await self._broadcast_local(data, room_id)
                    else:
                        # No subscriptions yet, just wait
                        await asyncio.sleep(1)
                except Exception as e:
                    # Only log if it's not the "no subscription" error
                    if "did you forget to call subscribe()" not in str(e):
                        print(f"Redis listener error: {e}")
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("Redis listener stopped")

    async def _broadcast_local(self, message: str, room_id: str):
        """Broadcast message only to local WebSocket connections (called by Redis listener)"""
        async with self._lock:
            conns = list(self._rooms.get(room_id, []))

        if conns:
            await asyncio.gather(
                *(self._safe_send(c, message) for c in conns),
                return_exceptions=True
            )

    async def _subscribe_to_room(self, room_id: str):
        """Subscribe to Redis channel for a room"""
        if self._pubsub and room_id not in self._subscribed_rooms:
            channel = f"chat_room_{room_id}"
            await self._pubsub.subscribe(channel)
            self._subscribed_rooms.add(room_id)
            print(f"📡 Subscribed to Redis channel: {channel}")

    async def connect(self, websocket: WebSocket, room_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            # Add to room
            if room_id not in self._rooms:
                self._rooms[room_id] = []
            self._rooms[room_id].append(websocket)

        # Subscribe to Redis channel for this room
        await self._subscribe_to_room(room_id)

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
        Publishes to Redis if available for multi-instance scaling.
        """
        # If Redis is available, publish to Redis (other instances will pick it up)
        if self._redis_client:
            try:
                channel = f"chat_room_{room_id}"
                await self._redis_client.publish(channel, message)
                print(f"📡 Published to Redis: {channel}")
            except Exception as e:
                print(f"⚠️  Redis publish failed: {e}, falling back to local broadcast")
                # Fall back to local broadcast if Redis fails
                await self._broadcast_local(message, room_id)
        else:
            # No Redis, just broadcast locally
            await self._broadcast_local(message, room_id)

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

    async def shutdown(self):
        """Cleanup Redis connections on shutdown"""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()

        if self._redis_client:
            await self._redis_client.close()

        print("✓ Redis connections closed")
