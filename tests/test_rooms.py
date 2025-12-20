import pytest
from fastapi.testclient import TestClient
from main import app
from config.database import users_collection, rooms_collection

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup():
    # Cleanup before/after tests
    users_collection.delete_many({"username": "testuser_rooms"})
    rooms_collection.delete_many({"name": "Test Room"})
    yield
    users_collection.delete_many({"username": "testuser_rooms"})
    rooms_collection.delete_many({"name": "Test Room"})

def test_room_flow():
    # 1. Signup
    response = client.post("/signup", json={
        "username": "testuser_rooms",
        "email": "testrooms@example.com",
        "password": "password123"
    })
    assert response.status_code == 200

    # 2. Login
    response = client.post("/signin", data={
        "username": "testrooms@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Room
    response = client.post("/rooms/create", json={"name": "Test Room"}, headers=headers)
    assert response.status_code == 200
    room_data = response.json()
    room_id = room_data["room_id"]
    assert room_data["name"] == "Test Room"
    
    # 4. Get Rooms
    response = client.get("/rooms", headers=headers)
    assert response.status_code == 200
    rooms = response.json()["rooms"]
    assert len(rooms) >= 1
    assert any(r["room_id"] == room_id for r in rooms)

    # 5. Connect WebSocket
    # Note: TestClient.websocket_connect might not support params directly in path easily if not carefully constructed?
    # It usually works.
    with client.websocket_connect(f"/ws/{room_id}?token={token}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "history"
        
        # Send message
        websocket.send_json({"type": "chat", "msg": "Hello Room"})
        
        # Receive broadcast (system join + my message)
        # Sequence might vary, but we expect both eventually.
        
        received = []
        try:
            # We expect at least 2 messages: "system joined" and "Hello Room"
            for _ in range(2):
                received.append(websocket.receive_json())
        except Exception:
            pass # In case timeout or something
            
        # Check for system join
        has_join = any(m.get("type") == "chat" and "joined" in m.get("msg", "") for m in received)
        # Check for my message
        has_msg = any(m.get("type") == "chat" and m.get("msg") == "Hello Room" for m in received)
        
        assert has_join
        assert has_msg