import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.anyio
async def test_root_page():
    """Test root page loads."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        # Adjust expected status: 200 for page, 307 for redirect to login
        assert response.status_code in [200, 307]
