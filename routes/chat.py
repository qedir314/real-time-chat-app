import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Request, HTTPException
from fastapi.templating import Jinja2Templates

from auth.core import get_user_from_token
from config.database import messages_collection
from utils.ConnectionManager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()
templates = Jinja2Templates(directory="templates")


async def save_message(room_id: str, user: str, msg: str):
    """Save message to database"""
    messages_collection.insert_one(
        {"room_id": room_id, "user": user, "msg": msg, "timestamp": datetime.utcnow()}
    )


@router.get("/history/{room_id}")
async def get_chat_history(room_id: str):
    """Retrieve last 50 messages from a room"""
    messages = list(
        messages_collection.find({"room_id": room_id})
        .sort("timestamp", -1)
        .limit(50)
    )
    return [
        {
            "user": msg["user"],
            "msg": msg["msg"],
            "timestamp": msg["timestamp"].isoformat(),
        }
        for msg in reversed(messages)
    ]


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
        websocket: WebSocket, room_id: str, token: str = Query(...)
):
    user = await get_user_from_token(token)
    if not user:
        await websocket.close(code=1008)
        return

    username = user["username"]
    await manager.connect(websocket, room_id)
    history = await get_chat_history(room_id)
    await websocket.send_json({"type": "history", "messages": history})
    await manager.broadcast_json(
        {"type": "chat", "user": "system", "msg": f"{username} joined"}, room_id
    )
    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
                if data.get("type") == "chat":
                    await save_message(room_id, username, data.get("msg"))
                    await manager.broadcast_json(
                        {"type": "chat", "user": username, "msg": data.get("msg")},
                        room_id,
                    )
                elif data.get("type") == "typing":
                    await manager.broadcast_json(
                        {
                            "type": "typing",
                            "user": username,
                            "status": data.get("status"),
                        },
                        room_id,
                    )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
        await manager.broadcast_json(
            {"type": "chat", "user": "system", "msg": f"{username} left"}, room_id
        )


@router.get("/rooms")
async def get_rooms(request: Request):
    token = request.cookies.get("access_token")
    print(f"Token from cookies: {token}")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        user = await get_user_from_token(token)
        print(f"User from token: {user}")

        if user:
            # Get all unique room IDs from messages - synchronous operation
            messages = list(messages_collection.find({}, {"room_id": 1}))
            rooms = list(set(msg.get("room_id") for msg in messages if msg.get("room_id")))

            # Ensure 'general' is always included
            if not rooms:
                rooms = ["general"]
            elif "general" not in rooms:
                rooms.insert(0, "general")

            print(f"Returning rooms: {rooms}")
            return {"rooms": rooms}
        else:
            raise HTTPException(status_code=401, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching rooms: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=401, detail="Invalid token")
