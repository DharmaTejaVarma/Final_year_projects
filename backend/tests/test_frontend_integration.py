import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
    from app.services.ai_service import ai_service
    from app.services.recommendation_service import recommendation_service
    from app.services.itinerary_service import itinerary_service
except ImportError:
    from backend.app.main import app
    from backend.app.services.ai_service import ai_service
    from backend.app.services.recommendation_service import recommendation_service
    from backend.app.services.itinerary_service import itinerary_service

client = TestClient(app)


# ==============================================================================
# PHASE 8: FRONTEND-BACKEND INTEGRATION TESTS
# ==============================================================================

def test_health_endpoint_integration():
    """Verify frontend health status poller receives 200 OK and expected structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "running" in data["message"].lower()


def test_auth_workflow_integration():
    """Verify registration, login, profile fetch, and profile update for frontend session."""
    test_email = f"frontend_user_{pytest.__version__.replace('.', '_')}@example.com"

    # 1. Register
    reg_res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Frontend Traveler",
            "email": test_email,
            "password": "Password123!",
        },
    )
    if reg_res.status_code == 400:
        # If user already registered in prior test run, proceed to login
        pass
    else:
        assert reg_res.status_code == 201
        reg_data = reg_res.json()
        assert "access_token" in reg_data
        assert reg_data["user"]["full_name"] == "Test Frontend Traveler"

    # 2. Login
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": test_email,
            "password": "Password123!",
        },
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    token = login_data["access_token"]
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Fetch Profile
    profile_res = client.get("/api/users/profile", headers=headers)
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["email"] == test_email

    # 4. Update Profile
    update_res = client.put(
        "/api/users/profile",
        headers=headers,
        json={
            "full_name": "Updated Frontend Traveler",
            "preferences": {
                "preferred_categories": "Heritage, Palaces, Culinary",
                "preferred_transport": "Car",
            },
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["full_name"] == "Updated Frontend Traveler"
    assert update_res.json()["preferences"]["preferred_transport"] == "Car"


def test_natural_language_ai_flow_integration():
    """Verify frontend PlanTrip natural language parsing auto-fills all parameters."""
    query = "I want a relaxed 2-day trip to Hyderabad. I like historical places and good food. My budget is 5,000 INR."
    res = client.post("/api/ai/extract-preferences", json={"text": query})
    assert res.status_code == 200
    data = res.json()

    prefs = data["preferences"]
    assert prefs["destination"] == "Hyderabad"
    assert prefs["duration_days"] == 2
    assert prefs["budget"] == 5000.0
    assert "history" in prefs["interests"]
    assert "food" in prefs["interests"]
    assert prefs["travel_style"] == "relaxed"


def test_recommendations_and_itinerary_flow_integration():
    """Verify frontend can fetch POIs, select them, and generate a multi-day itinerary with geometry."""
    # 1. Fetch recommendations for Hyderabad
    rec_res = client.post(
        "/api/recommendations/recommend",
        json={
            "destination": "Hyderabad",
            "interests": ["Historical Places", "Food", "Culture"],
            "budget": 5000.0,
            "available_duration_days": 2,
            "transportation": "driving-car",
            "limit": 6,
        },
    )
    assert rec_res.status_code == 200
    recs = rec_res.json()["recommendations"]
    assert len(recs) >= 3

    # Pick top 4 attractions as selected by user in UI
    selected = [
        {
            "id": r["place_id"],
            "name": r["name"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "category": r["category"],
            "address": r.get("address", ""),
            "visit_duration_mins": r.get("estimated_duration_mins") or 90,
            "entrance_fee": r.get("entrance_fee"),
            "recommendation_score": r.get("final_score"),
        }
        for r in recs[:4]
    ]

    # 2. Generate multi-day itinerary with selected POIs
    itin_res = client.post(
        "/api/itinerary/generate",
        json={
            "destination": "Hyderabad",
            "start_date": "2026-11-15",
            "end_date": "2026-11-16",
            "travelers_count": 1,
            "budget": 5000.0,
            "daily_available_hours": 8.0,
            "transportation": "driving-car",
            "pace": "relaxed",
            "selected_attractions": selected,
        },
    )
    assert itin_res.status_code == 200
    itin = itin_res.json()

    assert itin["destination"] == "Hyderabad"
    assert itin["total_days"] == 2
    assert len(itin["days"]) == 2
    assert itin["total_distance_km"] >= 0.0
    assert "estimated_total_cost" in itin["budget_summary"]

    # Check route geometry exists for map polylines
    for day in itin["days"]:
        assert "geometry" in day
        assert len(day["stops"]) > 0


def test_ai_assistant_chat_flow_integration():
    """Verify frontend AI assistant conversation endpoint returns grounded facts & trace."""
    chat_res = client.post(
        "/api/ai/chat",
        json={
            "message": "What is the acoustic clapping system at Golconda Fort?",
            "destination_hint": "Hyderabad",
        },
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()

    assert "reply" in chat_data
    assert len(chat_data["reply"]) > 30
    assert len(chat_data["workflow_trace"]) > 0

