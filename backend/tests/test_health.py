import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
except ImportError:
    from backend.app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Test GET /api/health returns 200 OK with expected payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "TravelSenseAI backend is running"


def test_root_endpoint():
    """Test GET / returns basic metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TravelSenseAI"
    assert data["status"] == "online"
    assert data["health"] == "/api/health"


def test_not_found_endpoint():
    """Test 404 error response matches centralized format."""
    response = client.get("/api/non-existent-route")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "error"

