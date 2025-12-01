from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from ConnectionManager import ConnectionManager
import json

app = FastAPI()
manager = ConnectionManager()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/{username}")
async def websocket_default_room(websocket: WebSocket, username: str):
    """Fallback for clients that connect to /ws/{username} — put them in 'general' room."""
    room_id = "general"
    await manager.connect(websocket, room_id)
    await manager.broadcast_json({"user": "system", "message": f"{username} joined"}, room_id)
    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
                if data.get("type") == "chat":
                    await manager.broadcast_json({"type": "chat", "user": data.get("user"), "msg": data.get("msg")}, room_id)
                elif data.get("type") == "typing":
                    await manager.broadcast_json({"type": "typing", "user": data.get("user"), "status": data.get("status")}, room_id)
            except json.JSONDecodeError:
                await manager.broadcast_json({"user": username, "message": text}, room_id)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
        await manager.broadcast_json({"user": "system", "message": f"{username} left"}, room_id)
    except Exception:
        await manager.disconnect(websocket, room_id)


@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str):
    await manager.connect(websocket, room_id)
    await manager.broadcast_json({"user": "system", "message": f"{username} joined"}, room_id)
    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
                if data.get("type") == "chat":
                    await manager.broadcast_json({"type": "chat", "user": data.get("user"), "msg": data.get("msg")}, room_id)
                elif data.get("type") == "typing":
                    await manager.broadcast_json({"type": "typing", "user": data.get("user"), "status": data.get("status")}, room_id)
            except json.JSONDecodeError:
                await manager.broadcast_json({"user": username, "message": text}, room_id)
    except WebSocketDisconnect:
        await manager.broadcast_json({"user": "system", "message": f"{username} left the room"}, room_id)
        await manager.disconnect(websocket, room_id)
    except Exception:
        await manager.disconnect(websocket, room_id)




if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
