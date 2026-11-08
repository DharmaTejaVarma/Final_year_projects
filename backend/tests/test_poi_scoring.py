import pytest
from fastapi.testclient import TestClient

try:
    from app.algorithms.poi_scoring import (
        ScoringWeights,
        calculate_baseline_score,
        calculate_budget_score,
        calculate_category_score,
        calculate_distance_score,
        calculate_final_score,
        calculate_preference_score,
        calculate_time_score,
        calculate_weather_score,
        generate_recommendation_explanation,
        rank_recommendations,
    )
    from app.main import app
except ImportError:
    from backend.app.algorithms.poi_scoring import (
        ScoringWeights,
        calculate_baseline_score,
        calculate_budget_score,
        calculate_category_score,
        calculate_distance_score,
        calculate_final_score,
        calculate_preference_score,
        calculate_time_score,
        calculate_weather_score,
        generate_recommendation_explanation,
        rank_recommendations,
    )
    from backend.app.main import app

client = TestClient(app)


# ==============================================================================
# 1. INDIVIDUAL SCORING FUNCTIONS
# ==============================================================================
def test_calculate_preference_score():
    """Verify preference scoring matches semantic categories and handles unrepresented places."""
    interests = ["Historical Places", "Food", "Photography"]

    # Direct match with historical fort
    score_fort = calculate_preference_score(
        user_interests=interests,
        place_categories=["heritage.fort", "tourism.sights"],
        place_name="Golconda Fort",
        place_description="Ancient citadel and landmark",
    )
    assert 0.8 <= score_fort <= 1.0

    # Match with dining/restaurant
    score_food = calculate_preference_score(
        user_interests=interests,
        place_categories=["catering.restaurant"],
        place_name="Paradise Biryani",
        place_description="Famous Hyderabadi dining",
    )
    assert 0.6 <= score_food <= 1.0

    # Unrelated venue
    score_unrelated = calculate_preference_score(
        user_interests=interests,
        place_categories=["commercial.gas_station"],
        place_name="Fuel Station",
        place_description="Automotive refill",
    )
    assert score_unrelated <= 0.25

    # Empty interests returns neutral 0.5
    score_empty = calculate_preference_score(
        user_interests=[],
        place_categories=["heritage.fort"],
    )
    assert score_empty == 0.5


def test_calculate_distance_score():
    """Verify distance suitability decays with radius and is strictly bounded in [0, 1]."""
    # 0 km (at destination center) -> maximum score 1.0
    assert calculate_distance_score(0.0, max_radius_km=25.0) == 1.0

    # 12.5 km (halfway) -> 0.5
    assert calculate_distance_score(12.5, max_radius_km=25.0) == 0.5

    # 25 km (at boundary) -> 0.0
    assert calculate_distance_score(25.0, max_radius_km=25.0) == 0.0

    # > 25 km (outside boundary) -> clamped 0.0
    assert calculate_distance_score(35.0, max_radius_km=25.0) == 0.0

    # Missing distance -> neutral 0.5
    assert calculate_distance_score(None) == 0.5

    # Negative distance -> clamped to 1.0
    assert calculate_distance_score(-5.0) == 1.0


def test_calculate_time_score():
    """Verify visit duration scoring and opening hours evaluation."""
    # Ideal visit (90 mins in an 8-hour touring day)
    score_ideal = calculate_time_score(visit_duration_mins=90, daily_available_hours=8.0)
    assert score_ideal >= 0.90

    # Very long visit (e.g. 10 hours exceeding 8 available hours)
    score_long = calculate_time_score(visit_duration_mins=600, daily_available_hours=8.0)
    assert score_long <= 0.40

    # Missing duration -> neutral 0.5
    assert calculate_time_score(None) == 0.5

    # Closed place -> 0.0
    score_closed = calculate_time_score(
        visit_duration_mins=60,
        opening_hours="Permanently closed",
        proposed_visit_hour=14,
    )
    assert score_closed == 0.0


def test_calculate_weather_score():
    """Verify outdoor vs indoor response to precipitation and clear skies."""
    outdoor_categories = ["tourism.attraction.viewpoint", "leisure.park"]
    indoor_categories = ["entertainment.museum", "catering.restaurant"]

    # Rainy conditions (code 61, 5.0mm precipitation)
    w_outdoor_rain = calculate_weather_score(
        weather_code=61,
        precipitation_mm=5.0,
        place_categories=outdoor_categories,
    )
    w_indoor_rain = calculate_weather_score(
        weather_code=61,
        precipitation_mm=5.0,
        place_categories=indoor_categories,
    )
    # Indoor places should score significantly higher than outdoor during rain
    assert w_indoor_rain > w_outdoor_rain
    assert w_outdoor_rain <= 0.35
    assert w_indoor_rain >= 0.90

    # Clear sunny conditions (code 0, 0.0mm precipitation)
    w_outdoor_clear = calculate_weather_score(
        weather_code=0,
        precipitation_mm=0.0,
        place_categories=outdoor_categories,
    )
    assert w_outdoor_clear >= 0.95

    # Missing weather data -> neutral 0.5
    assert calculate_weather_score(None, None, outdoor_categories) == 0.5


def test_calculate_budget_score():
    """Verify budget scoring without inventing fees."""
    # Free attraction -> maximum score 1.0
    assert calculate_budget_score(entrance_fee=0.0, user_budget=5000.0, total_trip_days=2) == 1.0

    # Modest fee (₹100 out of ₹2500 daily budget = 4%) -> high score 0.95
    score_modest = calculate_budget_score(entrance_fee=100.0, user_budget=5000.0, total_trip_days=2)
    assert score_modest >= 0.90

    # Severe budget violation (₹6000 fee exceeding ₹5000 total budget) -> penalty 0.05
    score_expensive = calculate_budget_score(entrance_fee=6000.0, user_budget=5000.0, total_trip_days=2)
    assert score_expensive <= 0.10

    # Missing fee or budget -> neutral 0.5 (do NOT invent missing fees)
    assert calculate_budget_score(entrance_fee=None, user_budget=5000.0) == 0.5
    assert calculate_budget_score(entrance_fee=100.0, user_budget=None) == 0.5


def test_calculate_category_score():
    """Verify category compatibility and diversification."""
    place_cats = ["heritage.monument", "tourism.sights"]
    target_cats = ["Historical Places", "Photography"]

    score_match = calculate_category_score(place_cats, target_cats)
    assert score_match >= 0.85

    score_unrelated = calculate_category_score(["commercial.supermarket"], target_cats)
    assert score_unrelated <= 0.55


# ==============================================================================
# 2. WEIGHT NORMALIZATION & FINAL SCORING
# ==============================================================================
def test_weight_normalization():
    """Verify weights strictly sum to 1.00 even when custom values are provided."""
    # Default weights
    w_default = ScoringWeights()
    norm_def = w_default.normalized()
    total_def = (
        norm_def.preference
        + norm_def.distance
        + norm_def.time
        + norm_def.weather
        + norm_def.category
        + norm_def.budget
    )
    assert round(total_def, 6) == 1.00

    # Custom weights (e.g. 60, 10, 10, 10, 5, 5)
    w_custom = ScoringWeights(preference=6.0, distance=1.0, time=1.0, weather=1.0, category=0.5, budget=0.5)
    norm_custom = w_custom.normalized()
    total_custom = (
        norm_custom.preference
        + norm_custom.distance
        + norm_custom.time
        + norm_custom.weather
        + norm_custom.category
        + norm_custom.budget
    )
    assert round(total_custom, 6) == 1.00
    assert norm_custom.preference == 0.60

    # Invalid all-zero weights raise ValueError
    with pytest.raises(ValueError):
        ScoringWeights(0, 0, 0, 0, 0, 0).normalized()


def test_calculate_final_score_manual_verification():
    """Verify R(p_i) = sum(w_k * x_ik) matches exact manual arithmetic."""
    weights = ScoringWeights(
        preference=0.30,
        distance=0.15,
        time=0.15,
        weather=0.15,
        category=0.15,
        budget=0.10,
    )
    factors = {
        "preference": 1.0,
        "distance": 0.8,
        "time": 0.9,
        "weather": 0.7,
        "category": 0.8,
        "budget": 1.0,
    }
    # Expected: 0.30*1.0 + 0.15*0.8 + 0.15*0.9 + 0.15*0.7 + 0.15*0.8 + 0.10*1.0
    # = 0.30 + 0.12 + 0.135 + 0.105 + 0.12 + 0.10 = 0.8800
    score = calculate_final_score(factors, weights)
    assert score == 0.88


# ==============================================================================
# 3. RANKING & TIE-BREAKING
# ==============================================================================
def test_rank_recommendations_and_tie_breaking():
    """Verify rank_recommendations assigns 1-based ranks and handles ties."""
    candidates = [
        {
            "name": "Place C",
            "final_score": 0.75,
            "factor_scores": {"preference": 0.70, "distance": 0.80},
        },
        {
            "name": "Place A",
            "final_score": 0.92,
            "factor_scores": {"preference": 0.95, "distance": 0.90},
        },
        {
            "name": "Place B",
            "final_score": 0.75,
            "factor_scores": {"preference": 0.85, "distance": 0.60},  # Higher preference tie-breaker
        },
    ]

    ranked = rank_recommendations(candidates)
    assert ranked[0]["name"] == "Place A"
    assert ranked[0]["rank"] == 1

    # Place B wins tie-breaker over Place C due to higher preference score
    assert ranked[1]["name"] == "Place B"
    assert ranked[1]["rank"] == 2

    assert ranked[2]["name"] == "Place C"
    assert ranked[2]["rank"] == 3


# ==============================================================================
# 4. PREFERENCE CHANGES & EXPLANATION GENERATION
# ==============================================================================
def test_preference_changes_shift_scores():
    """Verify changing user interests shifts POI preference scores."""
    fort_categories = ["heritage.fort", "tourism.sights"]

    # History interest gives high score to Fort
    score_history = calculate_preference_score(["History"], fort_categories)

    # Nightlife interest gives low score to Fort
    score_nightlife = calculate_preference_score(["Nightlife"], fort_categories)

    assert score_history > score_nightlife
    assert score_history >= 0.8
    assert score_nightlife <= 0.25


def test_generate_recommendation_explanation():
    """Verify explanation generator produces clear, human-readable justification."""
    factors = {
        "preference": 0.95,
        "distance": 0.85,
        "time": 0.90,
        "weather": 0.85,
        "category": 0.80,
        "budget": 0.95,
    }
    explanation = generate_recommendation_explanation(
        place_name="Golconda Fort",
        factor_scores=factors,
        user_interests=["Historical Places", "Photography"],
    )
    assert "Golconda Fort was recommended because" in explanation
    assert "historical places" in explanation.lower()
    assert "available travel schedule" in explanation.lower() or "weather" in explanation.lower()


# ==============================================================================
# 5. BASELINE EVALUATION
# ==============================================================================
def test_baseline_comparison():
    """Verify pure preference baseline computation."""
    assert calculate_baseline_score(0.85) == 0.85
    assert calculate_baseline_score(1.5) == 1.0  # Clamped
    assert calculate_baseline_score(-0.2) == 0.0  # Clamped


# ==============================================================================
# 6. END-TO-END HYDERABAD RECOMMENDATION ENDPOINT TEST
# ==============================================================================
def test_recommendation_endpoint_hyderabad():
    """Test full context-aware recommendation for Hyderabad matching user prompt input."""
    payload = {
        "destination": "Hyderabad",
        "interests": ["Historical Places", "Food", "Photography"],
        "budget": 5000.0,
        "available_duration_days": 2,
        "transportation": "Car",
        "daily_touring_hours": 8.0,
        "max_distance_km": 35.0,
        "limit": 5,
    }

    response = client.post("/api/recommendations/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["destination"] == "Hyderabad"
    assert "latitude" in data["destination_coordinates"]
    assert "longitude" in data["destination_coordinates"]
    assert data["total_recommended"] > 0
    assert len(data["recommendations"]) <= 5

    # Check top recommendation structure
    top = data["recommendations"][0]
    assert top["rank"] == 1
    assert "name" in top
    assert "final_score" in top
    assert 0.0 <= top["final_score"] <= 1.0
    assert "baseline_preference_score" in top
    assert "explanation" in top
    assert "was recommended because" in top["explanation"]

    # Verify all 6 factor scores are present and bounded in [0, 1]
    fs = top["factor_scores"]
    for factor in ["preference", "distance", "time", "weather", "category", "budget"]:
        assert factor in fs
        assert 0.0 <= fs[factor] <= 1.0

    # Verify baseline comparison metrics
    assert "baseline_comparison" in data
    assert "rank_displacements" in data["baseline_comparison"]
    assert "summary" in data["baseline_comparison"]

