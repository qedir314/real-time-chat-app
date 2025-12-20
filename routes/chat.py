import json
from datetime import datetime, UTC

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends
from starlette.concurrency import run_in_threadpool

from auth.core import get_user_from_token, get_current_active_user
from config.database import messages_collection, rooms_collection
from utils.ConnectionManager import ConnectionManager
from utils.chatbot import ai_bot

router = APIRouter()
manager = ConnectionManager()


def save_message(room_id: str, user: str, msg: str):
    """Save message to database"""
    messages_collection.insert_one(
        {"room_id": room_id, "user": user, "msg": msg, "timestamp": datetime.now(UTC)}
    )


@router.get("/history/{room_id}")
def get_chat_history(room_id: str, current_user: dict = Depends(get_current_active_user)):
    """Retrieve last 50 messages from a room"""
    # Check membership
    room = rooms_collection.find_one({"room_id": room_id})
    if room and current_user["_id"] not in room.get("members", []):
         raise HTTPException(status_code=403, detail="Not a member of this room")

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
    user = await run_in_threadpool(get_user_from_token, token)
    if not user:
        await websocket.close(code=1008)
        return

    # Check membership
    def check_membership():
        return rooms_collection.find_one({"room_id": room_id})
    
    room = await run_in_threadpool(check_membership)
    
    if room:
         if str(user["_id"]) not in room.get("members", []):
             print(f"User {user['username']} denied access to room {room_id}")
             await websocket.close(code=1008)
             return
    else:
        # Strict check: if room doesn't exist, close.
        await websocket.close(code=1008)
        return

    username = user["username"]
    await manager.connect(websocket, room_id)
    
    # Manually fetch history to send on connect
    def fetch_history():
        msgs = list(
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
            for msg in reversed(msgs)
        ]

    history = await run_in_threadpool(fetch_history)
    
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
                    await run_in_threadpool(save_message, room_id, username, message_text)
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
                            await run_in_threadpool(save_message, room_id, "AI_Bot", bot_response)
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
def get_rooms(current_user: dict = Depends(get_current_active_user)):
    try:
        user_id = current_user["_id"]
        cursor = rooms_collection.find({"members": user_id})
        
        rooms_data = []
        for doc in cursor:
            room_info = {
                "room_id": doc["room_id"],
                "name": doc["name"],
                "owner_id": doc["owner_id"]
            }
            if doc["owner_id"] == user_id:
                room_info["invite_code"] = doc.get("invite_code")
            rooms_data.append(room_info)
            
        return {"rooms": rooms_data}
    except Exception as e:
        print(f"Error fetching rooms: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")
