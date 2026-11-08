import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

try:
    from app.core.security import hash_password, verify_password, decode_access_token
    from app.database.base import Base
    from app.database.connection import get_db
    from app.main import app
    from app.models import (
        User,
        UserPreference,
        Destination,
        Place,
        Trip,
        TripPreference,
        Itinerary,
        ItineraryDay,
        ItineraryPlace,
        Review,
        SavedPlace,
    )
except ImportError:
    from backend.app.core.security import hash_password, verify_password, decode_access_token
    from backend.app.database.base import Base
    from backend.app.database.connection import get_db
    from backend.app.main import app
    from backend.app.models import (
        User,
        UserPreference,
        Destination,
        Place,
        Trip,
        TripPreference,
        Itinerary,
        ItineraryDay,
        ItineraryPlace,
        Review,
        SavedPlace,
    )

from sqlalchemy.pool import StaticPool

# Use an in-memory SQLite database with StaticPool so all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database schema for each test and provide a session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Override get_db with the test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==============================================================================
# TEST 1 & 3: USER REGISTRATION & PASSWORD HASHING
# ==============================================================================
def test_user_registration_and_password_hashing(client, db_session):
    """Test 1: Register new user & Test 3: Password is saved as Argon2 hash, never plain text."""
    payload = {
        "full_name": "Alice Traveler",
        "email": "alice@travelsense.ai",
        "password": "SuperSecretPassword123!",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@travelsense.ai"
    assert data["user"]["full_name"] == "Alice Traveler"
    assert data["user"]["is_active"] is True
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]

    # Verify directly in database that password was hashed with Argon2
    user_in_db = db_session.query(User).filter(User.email == "alice@travelsense.ai").first()
    assert user_in_db is not None
    assert user_in_db.hashed_password != payload["password"]
    assert user_in_db.hashed_password.startswith("$argon2id$")
    assert verify_password(payload["password"], user_in_db.hashed_password) is True


# ==============================================================================
# TEST 2: DUPLICATE EMAIL REJECTION
# ==============================================================================
def test_duplicate_email_rejection(client):
    """Test 2: Reject registration when email is already registered."""
    payload = {
        "full_name": "Bob Smith",
        "email": "bob@travelsense.ai",
        "password": "Password123!",
    }
    # Initial registration
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Duplicate registration attempt
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    data = res2.json()
    assert data["status"] == "error"
    assert "already exists" in data["message"].lower()


# ==============================================================================
# TEST 4 & 6: SUCCESSFUL LOGIN & JWT TOKEN GENERATION
# ==============================================================================
def test_successful_login_and_jwt_generation(client):
    """Test 4: Login with valid credentials & Test 6: Verify JWT token structure and claims."""
    register_payload = {
        "full_name": "Charlie Explorer",
        "email": "charlie@travelsense.ai",
        "password": "MySecretPassword456!",
    }
    client.post("/api/auth/register", json=register_payload)

    login_payload = {
        "email": "charlie@travelsense.ai",
        "password": "MySecretPassword456!",
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "charlie@travelsense.ai"

    # Decode and verify JWT claims
    token = data["access_token"]
    decoded = decode_access_token(token)
    assert decoded is not None
    assert "sub" in decoded
    assert decoded["sub"] == str(data["user"]["id"])
    assert decoded["type"] == "access_token"
    assert "exp" in decoded


# ==============================================================================
# TEST 5: INVALID PASSWORD REJECTION
# ==============================================================================
def test_invalid_password_rejection(client):
    """Test 5: Reject login with incorrect password."""
    client.post("/api/auth/register", json={
        "full_name": "Diana Ross",
        "email": "diana@travelsense.ai",
        "password": "CorrectPassword123!",
    })

    # Wrong password attempt
    response = client.post("/api/auth/login", json={
        "email": "diana@travelsense.ai",
        "password": "WrongPassword999!",
    })
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "error"
    assert "invalid email or password" in data["message"].lower()


# ==============================================================================
# TEST 7: PROTECTED PROFILE ACCESS
# ==============================================================================
def test_protected_profile_access(client):
    """Test 7: Accessing /api/users/profile requires a valid JWT token."""
    # 1. Access without token should fail with 401
    unauth_res = client.get("/api/users/profile")
    assert unauth_res.status_code == 401

    # 2. Register & obtain token
    reg_res = client.post("/api/auth/register", json={
        "full_name": "Evan Wright",
        "email": "evan@travelsense.ai",
        "password": "Password789!",
    })
    token = reg_res.json()["access_token"]

    # 3. Access with valid token
    headers = {"Authorization": f"Bearer {token}"}
    profile_res = client.get("/api/users/profile", headers=headers)
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["email"] == "evan@travelsense.ai"
    assert profile_data["full_name"] == "Evan Wright"
    assert profile_data["preferences"] is not None

    # 4. Access with forged/invalid token should fail with 401
    bad_headers = {"Authorization": "Bearer invalid.token.payload"}
    bad_res = client.get("/api/users/profile", headers=bad_headers)
    assert bad_res.status_code == 401


# ==============================================================================
# TEST 8: PROFILE & PREFERENCE UPDATE
# ==============================================================================
def test_profile_update(client):
    """Test 8: Update user profile and preferences."""
    reg_res = client.post("/api/auth/register", json={
        "full_name": "Fiona Gallagher",
        "email": "fiona@travelsense.ai",
        "password": "PasswordFiona!",
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "full_name": "Fiona G. Updated",
        "preferences": {
            "preferred_categories": "Adventure, Hiking, Mountains",
            "preferred_activities": "Trekking, Rock Climbing",
            "preferred_transport": "Rental 4x4",
            "preferred_budget": "Luxury",
            "preferred_travel_style": "Thrill-Seeker",
        },
    }
    update_res = client.put("/api/users/profile", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    updated_data = update_res.json()

    assert updated_data["full_name"] == "Fiona G. Updated"
    assert updated_data["preferences"]["preferred_travel_style"] == "Thrill-Seeker"
    assert updated_data["preferences"]["preferred_budget"] == "Luxury"
    assert updated_data["preferences"]["preferred_transport"] == "Rental 4x4"


# ==============================================================================
# TEST 9: DATABASE RELATIONSHIPS & CASCADES
# ==============================================================================
def test_database_relationships_and_cascades(db_session):
    """Test 9: Verify 1-to-many, 1-to-1, foreign keys, and cascade deletes."""
    # 1. Create User with UserPreference
    user = User(
        full_name="George Travel",
        email="george@travelsense.ai",
        hashed_password=hash_password("PasswordGeorge123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    user_pref = UserPreference(
        user_id=user.id,
        preferred_categories="Culture",
        preferred_travel_style="Backpacker",
    )
    db_session.add(user_pref)

    # 2. Create Destination and Place
    destination = Destination(
        name="Kyoto",
        country="Japan",
        latitude=35.0116,
        longitude=135.7681,
        description="Historic cultural capital of Japan with thousands of classical Buddhist temples.",
    )
    db_session.add(destination)
    db_session.flush()

    place = Place(
        destination_id=destination.id,
        name="Fushimi Inari Shrine",
        category="Shinto Shrine",
        description="Famous for thousands of vermilion torii gates.",
        latitude=34.9671,
        longitude=135.7727,
    )
    db_session.add(place)
    db_session.flush()

    # 3. Create Trip and TripPreference
    trip = Trip(
        user_id=user.id,
        destination_id=destination.id,
        start_date=date(2027, 4, 1),
        end_date=date(2027, 4, 7),
        budget=2500.0,
        travelers_count=2,
        status="planned",
    )
    db_session.add(trip)
    db_session.flush()

    trip_pref = TripPreference(
        trip_id=trip.id,
        pace="moderate",
        interests="Temples, Cherry Blossoms, Ramen",
    )
    db_session.add(trip_pref)

    # 4. Create Itinerary, Day, and Place
    itinerary = Itinerary(
        trip_id=trip.id,
        title="7-Day Kyoto Spring Exploration",
        total_estimated_cost=2100.0,
        total_distance=45.0,
        total_duration=56.0,
    )
    db_session.add(itinerary)
    db_session.flush()

    itinerary_day = ItineraryDay(
        itinerary_id=itinerary.id,
        day_number=1,
        travel_date=date(2027, 4, 1),
    )
    db_session.add(itinerary_day)
    db_session.flush()

    itinerary_place = ItineraryPlace(
        itinerary_day_id=itinerary_day.id,
        place_id=place.id,
        visit_order=1,
        arrival_time="09:00",
        departure_time="11:30",
    )
    db_session.add(itinerary_place)

    # 5. Create Review and SavedPlace
    review = Review(
        user_id=user.id,
        place_id=place.id,
        rating=5.0,
        review_text="Breathtaking morning walk through the torii gates!",
    )
    saved_place = SavedPlace(
        user_id=user.id,
        place_id=place.id,
    )
    db_session.add_all([review, saved_place])
    db_session.commit()

    # Assert model navigations & relationships work
    assert user.preferences.preferred_travel_style == "Backpacker"
    assert len(user.trips) == 1
    assert user.trips[0].destination.name == "Kyoto"
    assert len(user.trips[0].itineraries) == 1
    assert len(user.trips[0].itineraries[0].days) == 1
    assert len(user.trips[0].itineraries[0].days[0].places) == 1
    assert user.trips[0].itineraries[0].days[0].places[0].place.name == "Fushimi Inari Shrine"
    assert len(place.reviews) == 1
    assert place.reviews[0].rating == 5.0
    assert len(user.saved_places) == 1

    # Assert cascade delete: deleting user cascades to delete user's preferences, trips, reviews, saved places
    user_id = user.id
    db_session.delete(user)
    db_session.commit()

    assert db_session.query(User).filter(User.id == user_id).first() is None
    assert db_session.query(UserPreference).filter(UserPreference.user_id == user_id).first() is None
    assert db_session.query(Trip).filter(Trip.user_id == user_id).first() is None
    assert db_session.query(Review).filter(Review.user_id == user_id).first() is None
    assert db_session.query(SavedPlace).filter(SavedPlace.user_id == user_id).first() is None
    # Destination & place remain intact
    assert db_session.query(Destination).filter(Destination.name == "Kyoto").first() is not None
    assert db_session.query(Place).filter(Place.name == "Fushimi Inari Shrine").first() is not None
