import json
import time
import uuid
from locust import HttpUser, task, between, events
import websocket

class ChatUser(HttpUser):
    wait_time = between(1, 3) # Wait 1-3 seconds between sending messages
    
    def on_start(self):
        """Executed when a simulated user starts."""
        # 1. Register/Login to get a token
        self.username = f"load_user_{uuid.uuid4().hex[:8]}"
        self.password = "password123"
        self.email = f"{self.username}@example.com"
        
        # Signup
        self.client.post("/signup", json={
            "username": self.username,
            "email": self.email,
            "password": self.password
        })
        
        # Signin
        response = self.client.post("/signin", data={
            "username": self.username,
            "password": self.password
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            
            # 2. Create a unique room for this user to ensure they are the owner/member
            room_name = f"LoadTest_{self.username}"
            create_res = self.client.post("/rooms/create", json={"name": room_name}, headers={"Authorization": f"Bearer {self.token}"})
            
            if create_res.status_code == 200:
                perf_room_id = create_res.json()["room_id"]
            else:
                print(f"Failed to create room: {create_res.text}")
                self.token = None
                return

            # 3. Setup WebSocket connection
            ws_host = self.host.replace("http://", "").replace("https://", "")
            self.ws_url = f"ws://{ws_host}/ws/{perf_room_id}?token={self.token}"
            
            # Initialize WS
            try:
                self.ws = websocket.create_connection(self.ws_url)
            except Exception as e:
                print(f"WS Connection failed: {e}")
                self.token = None
        else:
            self.token = None

    def on_stop(self):
        if hasattr(self, 'ws'):
            self.ws.close()

    @task
    def send_message(self):
        if hasattr(self, 'ws') and self.ws.connected:
            start_time = time.time()
            try:
                msg = json.dumps({"type": "chat", "msg": f"Stress test message from {self.username}"})
                self.ws.send(msg)
                
                # We count this as a successful "request" for Locust stats
                events.request.fire(
                    request_type="WebSocket",
                    name="Send Message",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=len(msg),
                    exception=None
                )
            except Exception as e:
                events.request.fire(
                    request_type="WebSocket",
                    name="Send Message",
                    response_time=(time.time() - start_time) * 1000,
                    response_length=0,
                    exception=e
                )

    @task(1)
    def receive_messages(self):
        """Check for incoming messages (simulating background listener)"""
        if hasattr(self, 'ws') and self.ws.connected:
            self.ws.settimeout(0.1)
            try:
                while True:
                    self.ws.recv()
            except websocket.WebSocketTimeoutException:
                pass
            except Exception:
                pass
