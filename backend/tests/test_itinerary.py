import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

try:
    from app.algorithms.budget_calculator import calculate_itinerary_budget
    from app.algorithms.itinerary_optimizer import calculate_itinerary_utility
    from app.algorithms.itinerary_validator import (
        parse_opening_hours_window,
        validate_itinerary_plan,
    )
    from app.algorithms.weather_adjustment import (
        adjust_attraction_weather,
        evaluate_daily_weather_favorability,
        is_outdoor_venue,
    )
    from app.main import app
    from app.schemas.itinerary import (
        DailyWeatherSummary,
        ItineraryDayPlan,
        ItineraryStop,
        POIScheduleInput,
    )
except ImportError:
    from backend.app.algorithms.budget_calculator import calculate_itinerary_budget
    from backend.app.algorithms.itinerary_optimizer import calculate_itinerary_utility
    from backend.app.algorithms.itinerary_validator import (
        parse_opening_hours_window,
        validate_itinerary_plan,
    )
    from backend.app.algorithms.weather_adjustment import (
        adjust_attraction_weather,
        evaluate_daily_weather_favorability,
        is_outdoor_venue,
    )
    from backend.app.main import app
    from backend.app.schemas.itinerary import (
        DailyWeatherSummary,
        ItineraryDayPlan,
        ItineraryStop,
        POIScheduleInput,
    )

client = TestClient(app)

# Hyderabad Landmark POIs for testing
SAMPLE_ATTRACTIONS = [
    POIScheduleInput(
        id="golconda",
        name="Golconda Fort",
        latitude=17.3833,
        longitude=78.4011,
        category="heritage.fort",
        visit_duration_mins=90,
        opening_hours="09:00-17:30",
        is_opening_hours_verified=True,
        entrance_fee=25.0,
        is_fee_verified=True,
        is_outdoor=True,
    ),
    POIScheduleInput(
        id="qutb",
        name="Qutb Shahi Tombs",
        latitude=17.3942,
        longitude=78.3957,
        category="heritage.monument",
        visit_duration_mins=60,
        opening_hours="09:30-16:30",
        is_opening_hours_verified=True,
        entrance_fee=20.0,
        is_fee_verified=True,
        is_outdoor=True,
    ),
    POIScheduleInput(
        id="salarjung",
        name="Salar Jung Museum",
        latitude=17.3713,
        longitude=78.4804,
        category="museum",
        visit_duration_mins=120,
        opening_hours="10:00-17:00",
        is_opening_hours_verified=True,
        entrance_fee=50.0,
        is_fee_verified=True,
        is_outdoor=False,
    ),
    POIScheduleInput(
        id="charminar",
        name="Charminar",
        latitude=17.3616,
        longitude=78.4747,
        category="heritage.monument",
        visit_duration_mins=60,
        opening_hours="09:30-17:30",
        is_opening_hours_verified=True,
        entrance_fee=25.0,
        is_fee_verified=True,
        is_outdoor=True,
    ),
    POIScheduleInput(
        id="chowmahalla",
        name="Chowmahalla Palace",
        latitude=17.3578,
        longitude=78.4717,
        category="heritage.palace",
        visit_duration_mins=90,
        opening_hours="10:00-17:00",
        is_opening_hours_verified=True,
        entrance_fee=80.0,
        is_fee_verified=True,
        is_outdoor=False,
    ),
]


# ==============================================================================
# 1. WEATHER ADJUSTMENT ALGORITHM TESTS
# ==============================================================================
def test_outdoor_venue_classification():
    """Verify outdoor vs indoor classification correctly identifies venues."""
    assert is_outdoor_venue("heritage.fort", "Golconda Fort") is True
    assert is_outdoor_venue("garden", "NTR Gardens") is True
    assert is_outdoor_venue("museum", "Salar Jung Museum") is False
    assert is_outdoor_venue("heritage.palace", "Chowmahalla Palace") is False
    assert is_outdoor_venue("mall", "Inorbit Mall") is False


def test_weather_favorability_evaluation():
    """Verify rainy and storm forecasts trigger unfavorable classification."""
    # Sunny/clear weather
    favorable, mult, _ = evaluate_daily_weather_favorability({"precipitation_mm": 0.0, "weather_code": 1})
    assert favorable is True
    assert mult == 1.0

    # Rainy weather (precipitation >= 2mm or code 61)
    unfavorable, mult_rain, summary = evaluate_daily_weather_favorability({"precipitation_mm": 5.0, "weather_code": 61})
    assert unfavorable is False
    assert mult_rain <= 0.60
    assert "Precipitation forecasted" in summary


def test_attraction_weather_adjustment_preserves_preference():
    """Verify weather penalties reduce outdoor suitability but never silently drop the attraction."""
    rainy_weather = {"precipitation_mm": 6.5, "weather_code": 63}

    # Outdoor Fort on a rainy day
    score, warning, alternative = adjust_attraction_weather(
        poi_name="Golconda Fort",
        category="heritage.fort",
        is_outdoor=True,
        weather_data=rainy_weather,
        available_indoor_alternatives=["Salar Jung Museum", "Chowmahalla Palace"],
    )

    assert score < 1.0
    assert warning is not None
    assert "Golconda Fort" in warning
    assert "retained per your preferences" in warning
    assert alternative == "Salar Jung Museum"

    # Indoor Museum on the same rainy day should remain 1.0 with no warning
    score_indoor, warning_indoor, _ = adjust_attraction_weather(
        poi_name="Salar Jung Museum",
        category="museum",
        is_outdoor=False,
        weather_data=rainy_weather,
    )
    assert score_indoor == 1.0
    assert warning_indoor is None


# ==============================================================================
# 2. BUDGET CALCULATOR ALGORITHM TESTS
# ==============================================================================
def test_budget_calculator_missing_price_handling():
    """Verify missing prices are NOT assumed to be zero and conservative estimates are applied."""
    stops = [
        {"name": "Known Paid", "entrance_fee": 50.0, "is_fee_verified": True},
        {"name": "Missing Price Attraction", "entrance_fee": None, "is_fee_verified": False},
    ]

    res = calculate_itinerary_budget(
        total_budget=5000.0,
        travelers_count=2,
        total_days=1,
        total_distance_km=20.0,
        transportation="driving-car",
        stops_data=stops,
    )

    assert res.unknown_prices_count == 1
    assert res.has_unknown_expenses is True
    assert res.by_provenance.unknown > 0.0  # Missing price was conservatively estimated
    assert res.estimated_total_cost > 0.0


def test_budget_overrun_detection():
    """Verify insufficient budget accurately detects overrun and calculates deficit."""
    stops = [
        {"name": "Attraction 1", "entrance_fee": 100.0, "is_fee_verified": True},
        {"name": "Attraction 2", "entrance_fee": 150.0, "is_fee_verified": True},
    ]

    # Total estimated cost will comfortably exceed a tiny ₹500 budget
    res = calculate_itinerary_budget(
        total_budget=500.0,
        travelers_count=2,
        total_days=2,
        total_distance_km=40.0,
        transportation="driving-car",
        stops_data=stops,
    )

    assert res.is_budget_exceeded is True
    assert res.budget_overrun > 0.0
    assert res.remaining_budget < 0.0


# ==============================================================================
# 3. ITINERARY VALIDATOR ALGORITHM TESTS
# ==============================================================================
def test_opening_hours_parser():
    """Verify parser extracts open/close windows accurately."""
    window = parse_opening_hours_window("09:00-17:30")
    assert window == (540, 1050)

    window_spaces = parse_opening_hours_window("10:00 - 18:00")
    assert window_spaces == (600, 1080)

    assert parse_opening_hours_window(None) is None
    assert parse_opening_hours_window("Closed") is None


def test_validator_detects_opening_hour_conflict():
    """Verify validator flags visits outside verified operating hours."""
    stop_early = ItineraryStop(
        stop_order=1,
        name="Late Museum",
        latitude=17.37,
        longitude=78.48,
        arrival_time="08:00",
        departure_time="09:30",
        visit_duration_mins=90,
        travel_duration_mins=10.0,
        travel_distance_km=5.0,
        opening_hours="10:00-17:00",
        entrance_fee_per_person=50.0,
        total_entrance_fee=50.0,
    )

    day = ItineraryDayPlan(
        day_number=1,
        date="2026-11-10",
        weather=DailyWeatherSummary(date="2026-11-10"),
        stops=[stop_early],
        meal_breaks=[],
        daily_distance_km=5.0,
        daily_travel_time_mins=10.0,
        daily_visit_time_mins=90.0,
        daily_total_duration_mins=100.0,
        daily_estimated_cost=50.0,
        stops_count=1,
    )

    res = validate_itinerary_plan(
        destination="Hyderabad",
        start_date="2026-11-10",
        end_date="2026-11-10",
        budget=5000.0,
        daily_available_hours=8.0,
        days=[day],
    )

    conflict_violations = [v for v in res.violations if v.rule == "VISIT_BEFORE_OPENING"]
    assert len(conflict_violations) >= 1


def test_validator_detects_invalid_date_chronology():
    """Verify validator rejects end_date earlier than start_date."""
    res = validate_itinerary_plan(
        destination="Hyderabad",
        start_date="2026-11-15",
        end_date="2026-11-10",
        budget=5000.0,
        daily_available_hours=8.0,
        days=[],
    )
    assert res.is_valid is False
    assert any(v.rule == "DATE_CHRONOLOGY" for v in res.violations)


# ==============================================================================
# 4. ITINERARY UTILITY OBJECTIVE FUNCTION TESTS
# ==============================================================================
def test_utility_objective_calculation():
    """Verify multi-criteria utility score evaluates formula U(I) = aR + bW + cT + dDv - lTr - mC."""
    stop1 = ItineraryStop(
        stop_order=1,
        name="Fort",
        latitude=17.38,
        longitude=78.40,
        category="heritage.fort",
        arrival_time="09:00",
        departure_time="10:30",
        visit_duration_mins=90,
        travel_duration_mins=15.0,
        travel_distance_km=8.0,
        entrance_fee_per_person=25.0,
        total_entrance_fee=25.0,
        weather_suitability_score=1.0,
    )
    day = ItineraryDayPlan(
        day_number=1,
        date="2026-11-10",
        weather=DailyWeatherSummary(date="2026-11-10"),
        stops=[stop1],
        meal_breaks=[],
        daily_distance_km=8.0,
        daily_travel_time_mins=15.0,
        daily_visit_time_mins=90.0,
        daily_total_duration_mins=105.0,
        daily_estimated_cost=25.0,
        stops_count=1,
    )

    budget_res = calculate_itinerary_budget(
        total_budget=5000.0,
        travelers_count=1,
        total_days=1,
        total_distance_km=8.0,
        transportation="driving-car",
        stops_data=[{"name": "Fort", "entrance_fee": 25.0, "is_fee_verified": True}],
    )

    util = calculate_itinerary_utility(
        days=[day],
        budget_result=budget_res,
        daily_available_hours=8.0,
    )

    assert 0.0 <= util.overall_utility_score <= 1.0
    assert "U(I) =" in util.formula_summary
    assert util.weather_component == 1.0


# ==============================================================================
# 5. ENDPOINT INTEGRATION TESTS
# ==============================================================================
def test_generate_one_day_itinerary():
    """Test POST /api/itinerary/generate with single day plan."""
    payload = {
        "destination": "Hyderabad",
        "start_date": "2026-11-10",
        "end_date": "2026-11-10",
        "travelers_count": 2,
        "budget": 6000.0,
        "daily_available_hours": 8.0,
        "transportation": "driving-car",
        "start_time": "09:00",
        "attractions": [p.model_dump() for p in SAMPLE_ATTRACTIONS[:3]],
    }

    res = client.post("/api/itinerary/generate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["destination"] == "Hyderabad"
    assert data["total_days"] == 1
    assert data["itinerary_id"].startswith("itin_")
    assert len(data["days"]) == 1

    day1 = data["days"][0]
    assert day1["day_number"] == 1
    assert len(day1["stops"]) == 3
    assert day1["daily_distance_km"] > 0.0

    # Verify chronological sequence
    assert day1["stops"][0]["arrival_time"] == "09:00"
    assert day1["stops"][0]["departure_time"] > day1["stops"][0]["arrival_time"]

    # Verify Budget
    b = data["budget_summary"]
    assert b["total_budget"] == 6000.0
    assert b["estimated_total_cost"] > 0.0
    assert b["is_budget_exceeded"] is False

    # Verify Utility U(I)
    assert "overall_utility_score" in data["utility"]
    assert data["utility"]["overall_utility_score"] > 0.0


def test_generate_multi_day_itinerary():
    """Test POST /api/itinerary/generate across 3 days with accommodation."""
    payload = {
        "destination": "Hyderabad",
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "travelers_count": 2,
        "budget": 25000.0,
        "daily_available_hours": 8.0,
        "transportation": "driving-car",
        "start_time": "09:00",
        "include_accommodation": True,
        "accommodation_type": "standard",
        "attractions": [p.model_dump() for p in SAMPLE_ATTRACTIONS],
    }

    res = client.post("/api/itinerary/generate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["total_days"] == 3
    assert len(data["days"]) == 3
    assert data["budget_summary"]["by_category"]["accommodation"] > 0.0


def test_get_itinerary_by_id():
    """Test GET /api/itinerary/{itinerary_id} retrieves previously generated plan."""
    payload = {
        "destination": "Hyderabad",
        "start_date": "2026-11-10",
        "end_date": "2026-11-10",
        "travelers_count": 1,
        "budget": 5000.0,
        "attractions": [SAMPLE_ATTRACTIONS[0].model_dump()],
    }

    gen_res = client.post("/api/itinerary/generate", json=payload)
    assert gen_res.status_code == 200
    itin_id = gen_res.json()["itinerary_id"]

    get_res = client.get(f"/api/itinerary/{itin_id}")
    assert get_res.status_code == 200
    assert get_res.json()["itinerary_id"] == itin_id

    # 404 for nonexistent ID
    res_404 = client.get("/api/itinerary/itin_nonexistent999")
    assert res_404.status_code == 404


def test_validate_itinerary_endpoint():
    """Test POST /api/itinerary/validate endpoint."""
    payload = {
        "destination": "Hyderabad",
        "start_date": "2026-11-10",
        "end_date": "2026-11-10",
        "budget": 5000.0,
        "daily_available_hours": 8.0,
        "days": [
            {
                "day_number": 1,
                "date": "2026-11-10",
                "weather": {"date": "2026-11-10"},
                "stops": [
                    {
                        "stop_order": 1,
                        "name": "Charminar",
                        "latitude": 17.3616,
                        "longitude": 78.4747,
                        "arrival_time": "09:30",
                        "departure_time": "10:30",
                        "visit_duration_mins": 60,
                        "travel_duration_mins": 10.0,
                        "travel_distance_km": 5.0,
                        "entrance_fee_per_person": 25.0,
                        "total_entrance_fee": 25.0,
                    }
                ],
                "meal_breaks": [],
                "daily_distance_km": 5.0,
                "daily_travel_time_mins": 10.0,
                "daily_visit_time_mins": 60.0,
                "daily_total_duration_mins": 70.0,
                "daily_estimated_cost": 25.0,
                "stops_count": 1,
            }
        ],
    }

    res = client.post("/api/itinerary/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert data["can_generate"] is True


def test_itinerary_validation_rejection_invalid_dates():
    """Test validation rejection when dates are invalid or reversed."""
    payload = {
        "destination": "Hyderabad",
        "start_date": "2026-11-20",
        "end_date": "2026-11-10",
        "budget": 5000.0,
        "days": [],
    }
    # Schema validation catches end_date < start_date
    res = client.post("/api/itinerary/generate", json=payload)
    assert res.status_code == 422

