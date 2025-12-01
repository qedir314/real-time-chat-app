from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

html = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>WebSocket Echo</title>
  </head>
  <body>
    <h3>WebSocket Echo</h3>
    <input id="msg" placeholder="Type message" />
    <button id="send">Send</button>
    <div id="log" style="white-space:pre-wrap;margin-top:1rem;"></div>

    <script>
      const log = (t) => { document.getElementById('log').textContent += t + '\\n'; };
      const protocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
      const ws = new WebSocket(protocol + location.host + '/ws');

      ws.addEventListener('open', () => log('Connected'));
      ws.addEventListener('message', (e) => log('Server: ' + e.data));
      ws.addEventListener('close', () => log('Disconnected'));

      document.getElementById('send').onclick = () => {
        const input = document.getElementById('msg');
        if (!ws || ws.readyState !== WebSocket.OPEN) { log('Socket not open'); return; }
        ws.send(input.value);
        log('You: ' + input.value);
        input.value = '';
      };
    </script>
  </body>
</html>
"""

@app.get("/")
async def index():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # crucial: accept the connection
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)  # echo back immediately
    except WebSocketDisconnect:
        # client disconnected; exit the loop
        return

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
