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
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket)
    await manager.broadcast_json({"user": "system", "message": f"{username} joined"})
    try:
        while True:
            text = await websocket.receive_text()
            await manager.broadcast_json({"user": username, "message": text})
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        await manager.broadcast_json({"user": "system", "message": f"{username} left"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
