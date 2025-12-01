from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
import uvicorn
from ConnectionManager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()
templates = Jinja2Templates(directory="templates")


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
            await manager.broadcast_json({"user": username, "message": text}, room_id)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, room_id)
        await manager.broadcast_json({"user": "system", "message": f"{username} left"}, room_id)
    except Exception:
        await manager.disconnect(websocket, room_id)


@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str):
    # accept and register socket into specified room
    await manager.connect(websocket, room_id)
    await manager.broadcast_json({"user": "system", "message": f"{username} joined"}, room_id)
    try:
        while True:
            text = await websocket.receive_text()
            await manager.broadcast_json({"user": username, "message": text}, room_id)
    except WebSocketDisconnect:
        # remove from the known room and announce leave
        await manager.disconnect(websocket, room_id)
        await manager.broadcast_json({"user": "system", "message": f"{username} left"}, room_id)
    except Exception:
        # best-effort cleanup on unexpected errors
        await manager.disconnect(websocket, room_id)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
