import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from config.database import users_collection

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture(autouse=True)
async def cleanup_db():
    # Setup: Clean up test user before test
    users_collection.delete_one({"username": "testdeleteuser"})
    yield
    # Teardown: Clean up test user after test
    users_collection.delete_one({"username": "testdeleteuser"})

@pytest.mark.anyio
async def test_delete_account(client):
    # 1. Signup
    signup_data = {
        "username": "testdeleteuser",
        "password": "password123"
    }
    response = await client.post("/api/signup", json=signup_data)
    assert response.status_code == 200
    
    # 2. Login to get token
    login_data = {
        "username": "testdeleteuser",
        "password": "password123"
    }
    response = await client.post("/api/signin", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Verify user exists (call /me)
    response = await client.get("/api/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testdeleteuser"
    
    # 4. Delete Account
    response = await client.delete("/api/delete_account", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Account deleted successfully"
    
    # 5. Verify user is gone (login should fail)
    response = await client.post("/api/signin", data=login_data)
    assert response.status_code == 401
