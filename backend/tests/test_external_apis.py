import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

try:
    from app.main import app
    from app.services.ors_service import ors_service
    from app.utils.cache import api_cache
except ImportError:
    from backend.app.main import app
    from backend.app.services.ors_service import ors_service
    from backend.app.utils.cache import api_cache

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure in-memory cache is cleared between tests."""
    api_cache.clear()
    yield
    api_cache.clear()


# ==============================================================================
# 1. GEOAPIFY DESTINATIONS SEARCH TESTS
# ==============================================================================
def test_destination_search_success():
    """Test geocoding a destination with live Geoapify API."""
    response = client.get("/api/destinations/search?q=Tokyo&limit=3")
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "Tokyo"
    assert data["total"] >= 1
    assert data["source"] in ("live", "cached")
    
    first = data["results"][0]
    assert "latitude" in first
    assert "longitude" in first
    assert -90 <= first["latitude"] <= 90
    assert -180 <= first["longitude"] <= 180
    assert first["country"] is not None


def test_destination_search_cache():
    """Test that subsequent identical search hits the in-memory cache."""
    # First call: live
    res1 = client.get("/api/destinations/search?q=Kyoto&limit=2")
    assert res1.status_code == 200
    assert res1.json()["source"] == "live"

    # Second call: cached
    res2 = client.get("/api/destinations/search?q=Kyoto&limit=2")
    assert res2.status_code == 200
    assert res2.json()["source"] == "cached"
    assert res2.json()["results"] == res1.json()["results"]


def test_destination_search_invalid_empty():
    """Test empty query parameter rejection."""
    response = client.get("/api/destinations/search?q=")
    assert response.status_code in (400, 422)


# ==============================================================================
# 2. GEOAPIFY PLACES & ATTRACTIONS SEARCH TESTS
# ==============================================================================
def test_places_search_attractions():
    """Test tourist attractions search around Tokyo coordinates."""
    params = {
        "latitude": 35.6762,
        "longitude": 139.6503,
        "radius": 5000,
        "type": "attraction",
        "limit": 5,
    }
    response = client.get("/api/places/search", params=params)
    assert response.status_code == 200
    data = response.json()

    assert data["total"] > 0
    assert len(data["places"]) > 0
    first_place = data["places"][0]
    assert "place_id" in first_place
    assert "name" in first_place
    assert first_place["name"] != ""
    assert -90 <= first_place["latitude"] <= 90
    assert -180 <= first_place["longitude"] <= 180


def test_places_search_restaurants():
    """Test restaurant search around Tokyo coordinates."""
    params = {
        "latitude": 35.6762,
        "longitude": 139.6503,
        "radius": 3000,
        "type": "restaurant",
        "limit": 5,
    }
    response = client.get("/api/places/search", params=params)
    assert response.status_code == 200
    data = response.json()

    assert data["total"] > 0
    assert len(data["places"]) > 0
    for place in data["places"]:
        assert any("catering" in cat for cat in place["categories"]) or "restaurant" in place["category"].lower()


def test_places_search_invalid_coordinates():
    """Test rejection of out-of-bounds latitude/longitude."""
    # Latitude > 90
    response = client.get("/api/places/search?latitude=105.0&longitude=139.0")
    assert response.status_code in (400, 422)

    # Longitude < -180
    response2 = client.get("/api/places/search?latitude=35.0&longitude=-200.0")
    assert response2.status_code in (400, 422)


def test_place_details_endpoint():
    """Test retrieving details of a place found from search."""
    # 1. Search a place to get its ID
    search_res = client.get("/api/places/search?latitude=35.6762&longitude=139.6503&limit=1")
    assert search_res.status_code == 200
    places = search_res.json()["places"]
    assert len(places) > 0
    target_id = places[0]["place_id"]

    # 2. Query place details
    details_res = client.get(f"/api/places/{target_id}")
    assert details_res.status_code == 200
    data = details_res.json()
    assert "place" in data
    assert data["place"]["place_id"] == target_id
    assert data["place"]["name"] != ""


# ==============================================================================
# 3. OPENROUTESERVICE ROUTE CALCULATION TESTS
# ==============================================================================
def test_route_calculation_two_coordinates():
    """Test route calculation between Tokyo Station and Senso-ji."""
    payload = {
        "coordinates": [
            {"latitude": 35.6812, "longitude": 139.7671},  # Tokyo Station
            {"latitude": 35.7148, "longitude": 139.7967},  # Senso-ji
        ],
        "profile": "driving-car",
    }
    response = client.post("/api/routes/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["distance_km"] > 0.0
    assert data["duration_minutes"] > 0.0
    assert data["waypoints_count"] == 2
    assert len(data["geometry"]) >= 2
    assert "is_mocked" in data
    assert data["source"] in ("live", "mocked")
    if data["is_mocked"]:
        assert "ORS_API_KEY" in data["summary_note"] or "simulated" in data["summary_note"].lower()


def test_route_calculation_multiple_coordinates():
    """Test multi-stop route between three waypoints."""
    payload = {
        "coordinates": [
            {"latitude": 35.6812, "longitude": 139.7671},  # Tokyo Station
            {"latitude": 35.6586, "longitude": 139.7454},  # Tokyo Tower
            {"latitude": 35.7148, "longitude": 139.7967},  # Senso-ji
        ],
        "profile": "foot-walking",
    }
    response = client.post("/api/routes/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["waypoints_count"] == 3
    assert data["distance_km"] > 0.0
    assert data["duration_minutes"] > 0.0


def test_route_calculation_insufficient_coordinates():
    """Test rejection when fewer than two waypoints are provided."""
    payload = {
        "coordinates": [
            {"latitude": 35.6812, "longitude": 139.7671}
        ],
        "profile": "driving-car",
    }
    response = client.post("/api/routes/calculate", json=payload)
    assert response.status_code == 422


# ==============================================================================
# 4. OPEN-METEO WEATHER FORECAST TESTS
# ==============================================================================
def test_weather_forecast_live():
    """Test live weather forecast retrieval from Open-Meteo."""
    response = client.get("/api/weather/forecast?latitude=35.6762&longitude=139.6503")
    assert response.status_code == 200
    data = response.json()

    assert data["latitude"] is not None
    assert data["longitude"] is not None
    assert data["current"] is not None
    assert "temperature_celsius" in data["current"]
    assert "condition" in data["current"]
    assert len(data["daily"]) >= 7

    # Verify daily forecast fields
    first_day = data["daily"][0]
    assert "date" in first_day
    assert "max_temp_celsius" in first_day
    assert "min_temp_celsius" in first_day
    assert "condition" in first_day


def test_weather_forecast_date_range():
    """Test weather forecast query with start_date and end_date."""
    today = date.today()
    start_d = today + timedelta(days=1)
    end_d = today + timedelta(days=3)

    response = client.get(
        f"/api/weather/forecast?latitude=48.8566&longitude=2.3522&start_date={start_d}&end_date={end_d}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["daily"]) == 3


def test_weather_forecast_invalid_date_order():
    """Test rejection when start_date is later than end_date."""
    response = client.get(
        "/api/weather/forecast?latitude=48.8566&longitude=2.3522&start_date=2026-12-10&end_date=2026-12-05"
    )
    assert response.status_code == 400
    data = response.json()
    assert "cannot be later" in data["message"].lower()

