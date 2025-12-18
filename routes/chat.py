import json
from datetime import datetime, UTC

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends

from auth.core import get_user_from_token, get_current_active_user
from config.database import messages_collection
from utils.ConnectionManager import ConnectionManager
from utils.chatbot import ai_bot

router = APIRouter()
manager = ConnectionManager()


async def save_message(room_id: str, user: str, msg: str):
    """Save message to database"""
    messages_collection.insert_one(
        {"room_id": room_id, "user": user, "msg": msg, "timestamp": datetime.now(UTC)}
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
                    message_text = data.get("msg", "")
                    await save_message(room_id, username, message_text)
                    await manager.broadcast_json(
                        {"type": "chat", "user": username, "msg": message_text},
                        room_id,
                    )

                    # Check if AI bot should respond
                    if ai_bot.should_respond(message_text):
                        print(f"Bot triggered by message: '{message_text}'")
                        # Send typing indicator for bot
                        await manager.broadcast_json(
                            {"type": "typing", "user": "AI_Bot", "status": True},
                            room_id,
                        )

                        # Get AI response
                        bot_response = await ai_bot.get_response(message_text, username)
                        print(f"Bot response received: {bot_response}")

                        # Stop typing indicator
                        await manager.broadcast_json(
                            {"type": "typing", "user": "AI_Bot", "status": False},
                            room_id,
                        )

                        if bot_response:
                            print(f"Broadcasting bot response to room {room_id}")
                            # Save and broadcast bot response
                            await save_message(room_id, "AI_Bot", bot_response)
                            await manager.broadcast_json(
                                {"type": "chat", "user": "AI_Bot", "msg": bot_response},
                                room_id,
                            )
                        else:
                            print("Bot response was None or empty, not broadcasting")

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
async def get_rooms(current_user: dict = Depends(get_current_active_user)):
    try:
        # Get all unique room IDs from messages - synchronous operation
        messages = list(messages_collection.find({}, {"room_id": 1}))
        rooms = list(set(msg.get("room_id") for msg in messages if msg.get("room_id")))

        # Ensure 'general' is always included
        if not rooms:
            rooms = ["general"]
        elif "general" not in rooms:
            rooms.insert(0, "general")

        print(f"Returning rooms for {current_user['username']}: {rooms}")
        return {"rooms": rooms}
    except Exception as e:
        print(f"Error fetching rooms: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")
