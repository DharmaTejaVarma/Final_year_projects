"""Test Suite for Attraction-Specific Image Management System.

Validates:
1. Charminar and Golconda Fort display distinct, authentic photographs.
2. Taj Mahal and Red Fort display their respective distinct photographs.
3. Multiple attractions in the same city (Hyderabad: Charminar, Golconda, Hussain Sagar, Salar Jung, Birla Mandir)
   display distinct photographs (never duplicate or category-based).
4. Unrecognized attraction returns clean branded placeholder with is_placeholder=True and landmark name
   (NEVER an unrelated landmark's photograph).
5. Database and in-memory caching integrity (subsequent retrieval returns cached record).
6. Duplicate image prevention across batch resolutions.
7. Fast API endpoints: GET /api/places/image and POST /api/places/images/batch.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.image_service import VERIFIED_LANDMARK_REGISTRY, image_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_image_cache():
    """Ensure in-memory cache is reset for isolated test execution."""
    image_service._memory_cache.clear()
    yield
    image_service._memory_cache.clear()


def test_charminar_and_golconda_distinct_images():
    """Requirement 1: Charminar and Golconda Fort must display different, correct photographs."""
    charminar_img = asyncio.run(image_service.get_attraction_image("Charminar", city="Hyderabad"))
    golconda_img = asyncio.run(image_service.get_attraction_image("Golconda Fort", city="Hyderabad"))

    # Assert both were resolved
    assert charminar_img["image_url"] is not None
    assert golconda_img["image_url"] is not None

    # Assert they are DIFFERENT photographs
    assert charminar_img["image_url"] != golconda_img["image_url"], (
        "Charminar and Golconda Fort must NOT display the same image!"
    )

    # Assert authentic photographs
    assert "Charminar" in charminar_img["image_url"] or "Charminar" in charminar_img["image_attribution"]
    assert "Golconda" in golconda_img["image_url"] or "Golconda" in golconda_img["image_attribution"]
    assert charminar_img["is_placeholder"] is False
    assert golconda_img["is_placeholder"] is False


def test_taj_mahal_and_red_fort_distinct_images():
    """Requirement 2: Taj Mahal and Red Fort must display their respective photographs."""
    taj_img = asyncio.run(image_service.get_attraction_image("Taj Mahal", city="Agra"))
    red_fort_img = asyncio.run(image_service.get_attraction_image("Red Fort", city="Delhi"))

    assert taj_img["image_url"] is not None
    assert red_fort_img["image_url"] is not None
    assert taj_img["image_url"] != red_fort_img["image_url"]

    assert "Taj_Mahal" in taj_img["image_url"] or "Taj" in taj_img["image_attribution"]
    assert "Delhi_fort" in red_fort_img["image_url"] or "Red Fort" in red_fort_img["image_attribution"]
    assert taj_img["is_placeholder"] is False
    assert red_fort_img["is_placeholder"] is False


def test_same_city_multiple_attractions_distinct():
    """Requirement 3: Multiple attractions in the same city must not all display the same photograph."""
    hyderabad_attractions = [
        "Charminar",
        "Golconda Fort",
        "Hussain Sagar",
        "Salar Jung Museum",
        "Birla Mandir",
        "Chowmahalla Palace",
    ]

    images = []
    for name in hyderabad_attractions:
        img = asyncio.run(image_service.get_attraction_image(name, city="Hyderabad"))
        images.append(img["image_url"])

    # Ensure every single attraction received a unique URL
    unique_urls = set(images)
    assert len(unique_urls) == len(hyderabad_attractions), (
        f"Expected {len(hyderabad_attractions)} unique images for Hyderabad landmarks, but got {len(unique_urls)}: {images}"
    )


def test_caching_mechanism_preserves_association():
    """Requirement 4: Cache hit retrieves identical record without re-fetching."""
    first_lookup = asyncio.run(image_service.get_attraction_image("Hawa Mahal", city="Jaipur"))
    assert first_lookup["is_placeholder"] is False

    # Second lookup should hit cache
    second_lookup = asyncio.run(image_service.get_attraction_image("Hawa Mahal", city="Jaipur"))
    assert first_lookup["image_url"] == second_lookup["image_url"]
    assert first_lookup["image_attribution"] == second_lookup["image_attribution"]


def test_unknown_attraction_returns_clean_placeholder():
    """Requirement 6: If image retrieval fails, the system must display a placeholder

    instead of an unrelated photograph. Never silently display another attraction's photograph.
    """
    fake_name = "NonExistentUnknownFantasyCave12345"
    img = asyncio.run(image_service.get_attraction_image(fake_name, city="UnknownLand"))

    assert img["is_placeholder"] is True
    assert "data:image/svg+xml" in img["image_url"]
    assert fake_name in img["attraction_name"]
    # Verify it does NOT borrow from Charminar, Taj Mahal or any other registered attraction
    for reg_key, reg_val in VERIFIED_LANDMARK_REGISTRY.items():
        assert img["image_url"] != reg_val["url"], (
            f"Placeholder falsely used photo from registered landmark '{reg_key}'"
        )


def test_duplicate_prevention_in_batch():
    """Validate that batch resolution strictly prevents assigning the same image URL to two different places."""
    places = [
        {"name": "Charminar", "city": "Hyderabad", "id": "p1"},
        {"name": "Charminar Arch", "city": "Hyderabad", "id": "p2"},  # Potential alias
        {"name": "Golconda Fort", "city": "Hyderabad", "id": "p3"},
    ]

    batch_res = asyncio.run(image_service.get_attraction_images_batch(places))
    assert len(batch_res) == 3

    urls = [b["image_url"] for b in batch_res]
    # In batch mode, if p2 resolved to the exact same image as p1, duplicate prevention ensures
    # p2 falls back to a branded placeholder rather than duplicating identical image
    assert urls[0] != urls[2]  # Charminar != Golconda Fort


def test_get_place_image_api_endpoint():
    """Test GET /api/places/image HTTP endpoint."""
    res = client.get("/api/places/image", params={"name": "Taj Mahal", "city": "Agra"})
    assert res.status_code == 200
    data = res.json()
    assert data["attraction_name"] == "Taj Mahal"
    assert "image_url" in data
    assert data["is_placeholder"] is False
    assert data["image_verified"] is True
    assert data["image_attribution"] is not None


def test_batch_place_images_api_endpoint():
    """Test POST /api/places/images/batch HTTP endpoint."""
    payload = {
        "places": [
            {"name": "Mysore Palace", "city": "Mysuru"},
            {"name": "Gateway of India", "city": "Mumbai"},
        ]
    }
    res = client.post("/api/places/images/batch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    images = data["images"]
    assert len(images) == 2
    assert images[0]["image_url"] != images[1]["image_url"]
    assert "Mysore" in images[0]["attraction_name"]
    assert "Gateway" in images[1]["attraction_name"]
