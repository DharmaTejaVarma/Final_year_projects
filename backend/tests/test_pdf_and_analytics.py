import io
import os
import pytest
from fastapi.testclient import TestClient

try:
    from app.main import app
    from app.services.analytics_service import analytics_service
    from app.services.itinerary_service import ITINERARY_CACHE
    from app.services.pdf_service import pdf_service
except ImportError:
    from backend.app.main import app
    from backend.app.services.analytics_service import analytics_service
    from backend.app.services.itinerary_service import ITINERARY_CACHE
    from backend.app.services.pdf_service import pdf_service

client = TestClient(app)


@pytest.fixture
def sample_itinerary():
    """Sample realistic 2-day Hyderabad itinerary."""
    return {
        "itinerary_id": "itin_test_hyd_001",
        "destination": "Hyderabad",
        "start_date": "2026-11-10",
        "end_date": "2026-11-11",
        "total_days": 2,
        "travelers_count": 2,
        "transportation": "driving-car",
        "pace": "moderate",
        "total_attractions_scheduled": 4,
        "total_distance_km": 28.5,
        "total_travel_time_mins": 75.0,
        "total_visit_time_mins": 360.0,
        "feasibility_status": "feasible",
        "budget_summary": {
            "total_budget": 6000.0,
            "estimated_total_cost": 4200.0,
            "cost_per_traveler": 2100.0,
            "remaining_budget": 1800.0,
            "budget_overrun": 0.0,
            "is_within_budget": True,
            "by_category": {
                "transportation": 750.0,
                "entrance_fees": 350.0,
                "food": 1600.0,
                "accommodation": 1200.0,
                "contingency_buffer": 300.0,
            },
        },
        "days": [
            {
                "day_number": 1,
                "date": "2026-11-10",
                "theme": "Historical Fortresses & Royal Tombs",
                "daily_distance_km": 16.2,
                "daily_travel_time_mins": 42.0,
                "daily_visit_time_mins": 180.0,
                "daily_total_duration_mins": 222.0,
                "daily_estimated_cost": 2150.0,
                "weather": {
                    "date": "2026-11-10",
                    "temperature_celsius": 26.5,
                    "condition": "Partly cloudy",
                    "precipitation_mm": 0.0,
                    "is_outdoor_favorable": True,
                },
                "stops": [
                    {
                        "name": "Golconda Fort",
                        "category": "Historical Fort",
                        "arrival_time": "09:30",
                        "departure_time": "11:30",
                        "visit_duration_mins": 120,
                        "travel_distance_km": 8.5,
                        "travel_duration_mins": 25.0,
                        "entrance_fee_per_person": 25.0,
                        "total_entrance_fee": 50.0,
                        "fee_status": "verified",
                        "opening_hours_status": "verified",
                        "recommendation_score": 0.94,
                        "is_outdoor": True,
                    },
                    {
                        "name": "Qutb Shahi Tombs",
                        "category": "Architecture & Heritage",
                        "arrival_time": "12:00",
                        "departure_time": "13:00",
                        "visit_duration_mins": 60,
                        "travel_distance_km": 2.2,
                        "travel_duration_mins": 8.0,
                        "entrance_fee_per_person": 20.0,
                        "total_entrance_fee": 40.0,
                        "fee_status": "verified",
                        "opening_hours_status": "verified",
                        "recommendation_score": 0.88,
                        "is_outdoor": True,
                    },
                ],
                "meal_breaks": [
                    {
                        "name": "Lunch Break",
                        "time_window": "13:00-14:00",
                        "duration_mins": 60,
                        "allocated_cost": 600.0,
                    }
                ],
            },
            {
                "day_number": 2,
                "date": "2026-11-11",
                "theme": "Old City Charms & Palatial Grandeur",
                "daily_distance_km": 12.3,
                "daily_travel_time_mins": 33.0,
                "daily_visit_time_mins": 180.0,
                "daily_total_duration_mins": 213.0,
                "daily_estimated_cost": 2050.0,
                "weather": {
                    "date": "2026-11-11",
                    "temperature_celsius": 27.0,
                    "condition": "Sunny",
                    "precipitation_mm": 0.0,
                    "is_outdoor_favorable": True,
                },
                "stops": [
                    {
                        "name": "Charminar",
                        "category": "Monuments",
                        "arrival_time": "10:00",
                        "departure_time": "11:00",
                        "visit_duration_mins": 60,
                        "travel_distance_km": 6.8,
                        "travel_duration_mins": 18.0,
                        "entrance_fee_per_person": 25.0,
                        "total_entrance_fee": 50.0,
                        "fee_status": "verified",
                        "opening_hours_status": "verified",
                        "recommendation_score": 0.91,
                        "is_outdoor": False,
                    },
                    {
                        "name": "Chowmahalla Palace",
                        "category": "Royal Palace",
                        "arrival_time": "11:30",
                        "departure_time": "13:30",
                        "visit_duration_mins": 120,
                        "travel_distance_km": 1.5,
                        "travel_duration_mins": 6.0,
                        "entrance_fee_per_person": 80.0,
                        "total_entrance_fee": 160.0,
                        "fee_status": "verified",
                        "opening_hours_status": "verified",
                        "recommendation_score": 0.89,
                        "is_outdoor": False,
                    },
                ],
                "meal_breaks": [
                    {
                        "name": "Lunch Break",
                        "time_window": "13:30-14:30",
                        "duration_mins": 60,
                        "allocated_cost": 600.0,
                    }
                ],
            },
        ],
        "general_notes": [
            "Dress modestly when entering heritage tombs and religious precincts.",
            "Photography permits may be required for DSLR camera equipment.",
        ],
    }


def test_pdf_generation_basic(sample_itinerary):
    """Test PDF generation produces a valid, well-formed PDF file on disk."""
    pdf_path, pdf_bytes = pdf_service.generate_itinerary_pdf(
        itinerary=sample_itinerary,
        title="Hyderabad 2-Day Executive Itinerary",
    )

    assert os.path.exists(pdf_path)
    assert len(pdf_bytes) > 5000
    # PDF magic signature
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_generation_multi_page(sample_itinerary):
    """Test generating a large multi-day itinerary spanning multiple pages with NumberedCanvas."""
    large_itin = dict(sample_itinerary)
    large_itin["total_days"] = 4
    extra_days = []
    for d in range(1, 5):
        day_copy = dict(sample_itinerary["days"][0])
        day_copy["day_number"] = d
        day_copy["date"] = f"2026-11-{10 + d}"
        extra_days.append(day_copy)
    large_itin["days"] = extra_days

    pdf_path, pdf_bytes = pdf_service.generate_itinerary_pdf(
        itinerary=large_itin,
        title="Hyderabad 4-Day Comprehensive Grand Tour",
    )

    assert os.path.exists(pdf_path)
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_generation_missing_and_none_data():
    """Test PDF generation handles sparse, missing, and None attributes gracefully."""
    sparse_itin = {
        "destination": "Goa",
        "start_date": None,
        "end_date": None,
        "travelers_count": 1,
        "budget_summary": None,
        "days": [
            {
                "day_number": 1,
                "stops": [
                    {
                        "name": "Calangute Beach",
                        "category": None,
                        "arrival_time": None,
                        "departure_time": None,
                        "entrance_fee_per_person": None,
                        "fee_status": None,
                    }
                ],
            }
        ],
    }

    pdf_path, pdf_bytes = pdf_service.generate_itinerary_pdf(
        itinerary=sparse_itin,
        title="Goa Minimal Itinerary",
    )

    assert os.path.exists(pdf_path)
    assert pdf_bytes.startswith(b"%PDF-")


def test_pdf_special_characters_and_xml_escaping():
    """Test special characters (&, <, >, quotes, symbols) do not crash ReportLab XML parser."""
    special_itin = {
        "destination": "Jaipur & Amer <Heritage>",
        "start_date": "2026-12-01",
        "end_date": "2026-12-02",
        "travelers_count": 2,
        "days": [
            {
                "day_number": 1,
                "theme": "Palaces & Forts <Grand> 'Special'",
                "stops": [
                    {
                        "name": "Hawa Mahal & Museum <Royal>",
                        "category": "History & Culture",
                        "arrival_time": "09:00",
                        "departure_time": "10:30",
                        "visit_duration_mins": 90,
                        "travel_distance_km": 5.0,
                        "travel_duration_mins": 15.0,
                        "entrance_fee_per_person": 50.0,
                        "total_entrance_fee": 100.0,
                        "fee_status": "verified",
                    }
                ],
            }
        ],
        "general_notes": ["Special note: 100% verified & safe <recommended>."],
    }

    pdf_path, pdf_bytes = pdf_service.generate_itinerary_pdf(
        itinerary=special_itin,
        title="Jaipur & Environs <Special>",
    )

    assert os.path.exists(pdf_path)
    assert pdf_bytes.startswith(b"%PDF-")


def test_analytics_service_7_visualizations(sample_itinerary):
    """Test that AnalyticsService computes all 7 required visualization datasets accurately."""
    analytics = analytics_service.compute_itinerary_analytics(sample_itinerary)

    # 1. Category Distribution
    assert len(analytics.category_distribution) >= 2
    total_pct = sum(item.percentage for item in analytics.category_distribution)
    assert 99.0 <= total_pct <= 101.0

    # 2. Recommendation Score Distribution
    assert len(analytics.score_distribution) == 4
    for item in analytics.score_distribution:
        assert 0.0 <= item.score <= 1.0
        assert "score_band" in item.model_dump()

    # 3. Daily Expense Distribution
    assert len(analytics.daily_expense_distribution) == 2
    assert analytics.daily_expense_distribution[0].total_cost > 0.0

    # 4. Daily Travel Duration
    assert len(analytics.daily_travel_duration) == 2
    assert analytics.daily_travel_duration[0].travel_time_mins == 42.0
    assert analytics.daily_travel_duration[0].visit_time_mins == 180.0

    # 5. Distance Comparison
    assert len(analytics.distance_comparison) == 2
    assert analytics.distance_comparison[0].distance_km == 16.2
    assert analytics.distance_comparison[1].cumulative_distance_km == round(16.2 + 12.3, 2)

    # 6. Budget Utilization
    b_util = analytics.budget_utilization
    assert b_util.total_budget == 6000.0
    assert b_util.estimated_cost == 4200.0
    assert b_util.remaining_budget == 1800.0
    assert b_util.utilization_percentage == 70.0
    assert b_util.is_over_budget is False

    # 7. Attraction Metrics
    metrics = analytics.attraction_metrics
    assert metrics.scheduled_count == 4
    assert metrics.outdoor_count == 2
    assert metrics.indoor_count == 2
    assert metrics.verified_opening_hours_count == 4


def test_api_generate_report_endpoint(sample_itinerary):
    """Test POST /api/reports/generate with direct itinerary payload."""
    resp = client.post(
        "/api/reports/generate",
        json={
            "itinerary_data": sample_itinerary,
            "title": "Hyderabad Executive Report API Test",
            "planning_notes": "Take comfortable walking shoes.",
        },
    )
    assert resp.status_code == 201
    data = resp.json()

    assert "report_id" in data
    assert data["destination"] == "Hyderabad"
    assert data["total_days"] == 2
    assert data["file_size_bytes"] > 5000
    assert data["download_url"].startswith("/api/reports/")
    assert "analytics" in data
    assert len(data["analytics"]["category_distribution"]) > 0


def test_api_get_report_by_id(sample_itinerary):
    """Test GET /api/reports/{report_id} retrieves generated report metadata."""
    # First generate
    gen_resp = client.post(
        "/api/reports/generate",
        json={"itinerary_data": sample_itinerary},
    )
    assert gen_resp.status_code == 201
    rep_id = gen_resp.json()["report_id"]

    # Then retrieve
    get_resp = client.get(f"/api/reports/{rep_id}")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["report_id"] == rep_id
    assert retrieved["destination"] == "Hyderabad"
    assert retrieved["analytics"]["budget_utilization"]["total_budget"] == 6000.0


def test_api_get_report_not_found():
    """Test GET /api/reports/{report_id} returns 404 for unknown report ID."""
    resp = client.get("/api/reports/rep_non_existent_999")
    assert resp.status_code == 404


def test_api_download_pdf(sample_itinerary):
    """Test GET /api/reports/{report_id}/download streams the ReportLab PDF."""
    gen_resp = client.post(
        "/api/reports/generate",
        json={"itinerary_data": sample_itinerary},
    )
    rep_id = gen_resp.json()["report_id"]

    down_resp = client.get(f"/api/reports/{rep_id}/download")
    assert down_resp.status_code == 200
    assert down_resp.headers["content-type"] == "application/pdf"
    assert "attachment" in down_resp.headers.get("content-disposition", "")
    assert down_resp.content.startswith(b"%PDF-")


def test_api_generate_report_from_cached_itinerary(sample_itinerary):
    """Test POST /api/reports/generate resolving an itinerary by cached ID."""
    cached_id = "itin_cached_test_42"
    ITINERARY_CACHE[cached_id] = sample_itinerary

    resp = client.post(
        "/api/reports/generate",
        json={"itinerary_id": cached_id},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["itinerary_id"] == cached_id
    assert data["destination"] == "Hyderabad"
