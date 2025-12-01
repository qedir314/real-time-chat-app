from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from ConnectionManager import ConnectionManager
from config import messages_collection
import json
from datetime import datetime

app = FastAPI()
manager = ConnectionManager()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/history/{room_id}")
async def get_chat_history(room_id: str):
    """Retrieve last 50 messages from a room"""
    messages = list(
        messages_collection.find({"room_id": room_id})
        .sort("timestamp", -1)
        .limit(50)
    )
    # Reverse to get chronological order and remove MongoDB _id
    return [{"user": msg["user"], "msg": msg["msg"], "timestamp": msg["timestamp"]} for msg in reversed(messages)]


async def save_message(room_id: str, user: str, msg: str):
    """Save message to database"""
    messages_collection.insert_one({
        "room_id": room_id,
        "user": user,
        "msg": msg,
        "timestamp": datetime.utcnow()
    })


@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str):
    await manager.connect(websocket, room_id)

    # Load and send chat history to the connected user
    messages = list(
        messages_collection.find({"room_id": room_id})
        .sort("timestamp", -1)
        .limit(50)
    )
    messages_reversed = list(reversed(messages))
    await websocket.send_json({
        "type": "history",
        "messages": [{"user": msg["user"], "msg": msg["msg"]} for msg in messages_reversed]
    })

    await manager.broadcast_json({"type": "chat", "user": "system", "msg": f"{username} joined"}, room_id)
    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
                if data.get("type") == "chat":
                    await save_message(room_id, data.get("user"), data.get("msg"))
                    await manager.broadcast_json({"type": "chat", "user": data.get("user"), "msg": data.get("msg")},
                                                 room_id)
                elif data.get("type") == "typing":
                    await manager.broadcast_json(
                        {"type": "typing", "user": data.get("user"), "status": data.get("status")}, room_id)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
        await manager.broadcast_json({"type": "chat", "user": "system", "msg": f"{username} left"}, room_id)


@app.websocket("/ws/{username}")
async def websocket_default_room(websocket: WebSocket, username: str):
    """Fallback for clients that connect to /ws/{username} — put them in 'general' room."""
    room_id = "general"
    await manager.connect(websocket, room_id)
    # Send chat history
    history = await get_chat_history(room_id)
    await websocket.send_json({"type": "history", "messages": history})
    await manager.broadcast_json({"user": "system", "message": f"{username} joined"}, room_id)
    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
                if data.get("type") == "chat":
                    await save_message(room_id, data.get("user"), data.get("msg"))
                    await manager.broadcast_json({"type": "chat", "user": data.get("user"), "msg": data.get("msg")}, room_id)
                elif data.get("type") == "typing":
                    await manager.broadcast_json({"type": "typing", "user": data.get("user"), "status": data.get("status")}, room_id)
            except json.JSONDecodeError:
                await save_message(room_id, username, text)
                await manager.broadcast_json({"user": username, "message": text}, room_id)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
        await manager.broadcast_json({"user": "system", "message": f"{username} left"}, room_id)
    except Exception:
        await manager.disconnect(websocket, room_id)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
