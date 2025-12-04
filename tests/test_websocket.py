import pytest
from fastapi.testclient import TestClient
from main import app


class TestWebSocket:
    def test_websocket_unauthenticated_rejected(self):
        """Test that WebSocket without auth is rejected."""
        client = TestClient(app)

        from starlette.websockets import WebSocketDisconnect
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/general"):
                pass  # Should disconnect immediately

    def test_websocket_with_auth(self):
        """Test WebSocket connects with valid JWT."""
        client = TestClient(app)

        # Login first - adjust endpoint and fields to match your auth
        response = client.post("/login", data={
            "username": "testuser",
            "password": "testpassword"
        }, follow_redirects=False)

        # Check if login succeeded (redirect or 200)
        if response.status_code not in [200, 302, 303, 307]:
            pytest.skip("Login failed - ensure test user exists")

        # Cookies are now on client automatically
        # Connect to a room - use your actual room path
        with client.websocket_connect("/ws/general") as websocket:
            websocket.send_json({
                "type": "message",
                "content": "Hello"
            })
            data = websocket.receive_json()
            assert data is not None
