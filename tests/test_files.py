import pytest
from fastapi.testclient import TestClient
from main import app
from config.database import users_collection, rooms_collection, files_collection
import io

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup():
    # Cleanup before/after tests
    users_collection.delete_many({"username": "testuser_files"})
    rooms_collection.delete_many({"name": "Test File Room"})
    files_collection.delete_many({"uploader": "testuser_files"})
    yield
    users_collection.delete_many({"username": "testuser_files"})
    rooms_collection.delete_many({"name": "Test File Room"})
    files_collection.delete_many({"uploader": "testuser_files"})


def test_file_upload_flow():
    # 1. Signup
    response = client.post("/api/signup", json={
        "username": "testuser_files",
        "password": "password123"
    })
    assert response.status_code == 200

    # 2. Login
    response = client.post("/api/signin", data={
        "username": "testuser_files",
        "password": "password123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Room
    response = client.post("/api/rooms/create", json={"name": "Test File Room"}, headers=headers)
    assert response.status_code == 200
    room_id = response.json()["room_id"]

    # 4. Upload a text file
    file_content = b"Hello, this is a test file!"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    data = {"room_id": room_id}
    
    response = client.post("/api/files/upload", files=files, data=data, headers=headers)
    assert response.status_code == 200
    file_data = response.json()
    assert file_data["original_name"] == "test.txt"
    assert file_data["content_type"] == "text/plain"
    assert file_data["size"] == len(file_content)
    file_id = file_data["file_id"]

    # 5. Get file info
    response = client.get(f"/api/files/{file_id}/info", headers=headers)
    assert response.status_code == 200
    info = response.json()
    assert info["original_name"] == "test.txt"
    assert info["uploader"] == "testuser_files"

    # 6. Download file
    response = client.get(f"/api/files/{file_id}", headers=headers)
    assert response.status_code == 200
    assert response.content == file_content


def test_file_upload_invalid_type():
    # 1. Signup & Login
    users_collection.delete_many({"username": "testuser_files2"})
    
    client.post("/api/signup", json={
        "username": "testuser_files2",
        "password": "password123"
    })
    response = client.post("/api/signin", data={
        "username": "testuser_files2",
        "password": "password123"
    })
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Room
    response = client.post("/api/rooms/create", json={"name": "Test File Room 2"}, headers=headers)
    room_id = response.json()["room_id"]

    # 3. Try to upload invalid file type
    files = {"file": ("malicious.exe", io.BytesIO(b"bad content"), "application/x-msdownload")}
    data = {"room_id": room_id}
    
    response = client.post("/api/files/upload", files=files, data=data, headers=headers)
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]

    # Cleanup
    users_collection.delete_many({"username": "testuser_files2"})
    rooms_collection.delete_many({"name": "Test File Room 2"})
