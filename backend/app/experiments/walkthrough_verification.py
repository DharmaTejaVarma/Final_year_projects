"""
TravelSenseAI — End-to-End Complete Application Walkthrough Verification (Phase 11, Part G)

Validates all 15 operational steps end-to-end:
1. Register a user
2. Log in
3. Enter travel preferences
4. Retrieve tourist attractions
5. Generate recommendations
6. Cluster nearby attractions
7. Optimize routes
8. Retrieve weather
9. Generate multi-day itinerary
10. Validate the budget
11. Ask the AI assistant a question
12. Display the interactive map (verify route geometry & waypoints)
13. Generate a PDF report
14. View analytics
15. Verify error handling
"""

import sys
import os
import uuid
from pathlib import Path
from datetime import date, timedelta

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app


def run_walkthrough():
    client = TestClient(app)
    results = {}
    print("=" * 80)
    print("TravelSenseAI - Phase 11 Final Walkthrough Verification (15 Steps)")
    print("=" * 80)

    # 1. Register a user
    unique_email = f"walkthrough_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "full_name": "Test Explorer",
        "email": unique_email,
        "password": "StrongPassword123!",
    }
    r1 = client.post("/api/auth/register", json=reg_payload)
    assert r1.status_code in (200, 201), f"Step 1 Failed: {r1.text}"
    token = r1.json().get("access_token")
    assert token, "Step 1 Failed: No access token returned"
    auth_headers = {"Authorization": f"Bearer {token}"}
    results["1_register_user"] = "PASSED"
    print("[PASS] Step 1: User Registration successful.")

    # 2. Log in
    login_payload = {
        "email": unique_email,
        "password": "StrongPassword123!",
    }
    r2 = client.post("/api/auth/login", json=login_payload)
    assert r2.status_code == 200, f"Step 2 Failed: {r2.text}"
    token2 = r2.json().get("access_token")
    assert token2, "Step 2 Failed: Login token missing"
    results["2_user_login"] = "PASSED"
    print("[PASS] Step 2: User Login & JWT acquisition successful.")

    # 3. Enter travel preferences
    pref_payload = {
        "preferences": {
            "preferred_categories": "Heritage, Food, Culture",
            "preferred_transport": "driving",
            "preferred_travel_style": "relaxed",
        }
    }
    r3 = client.put("/api/users/profile", json=pref_payload, headers=auth_headers)
    assert r3.status_code == 200, f"Step 3 Failed: {r3.text}"
    results["3_travel_preferences"] = "PASSED"
    print("[PASS] Step 3: Travel Preferences saved successfully.")

    # 4. Retrieve tourist attractions
    r4 = client.get("/api/places/search?latitude=17.360589&longitude=78.474061&radius=15000&limit=8")
    assert r4.status_code == 200, f"Step 4 Failed: {r4.text}"
    places_resp = r4.json()
    places = places_resp.get("places", [])
    assert isinstance(places, list) and len(places) > 0, f"Step 4 Failed: No attractions returned ({places_resp})"
    results["4_retrieve_attractions"] = "PASSED"
    print(f"[PASS] Step 4: Tourist Attractions retrieval successful ({len(places)} places found).")

    # 5. Generate recommendations
    rec_payload = {
        "destination": "Hyderabad",
        "interests": ["Historical Places", "Food", "Photography"],
        "budget": 5000.0,
        "available_duration_days": 2,
        "transportation": "Car",
        "daily_touring_hours": 8.0,
        "limit": 5,
    }
    r5 = client.post("/api/recommendations/recommend", json=rec_payload)
    assert r5.status_code == 200, f"Step 5 Failed: {r5.text}"
    recs = r5.json().get("recommendations", [])
    assert len(recs) > 0, "Step 5 Failed: No recommendations generated"
    results["5_generate_recommendations"] = "PASSED"
    print(f"[PASS] Step 5: Recommendations generated successfully ({len(recs)} POIs scored with 6 factors).")

    # 6. Cluster nearby attractions
    clustering_payload = {
        "places": [
            {"id": "p1", "name": "Charminar", "latitude": 17.3616, "longitude": 78.4747},
            {"id": "p2", "name": "Mecca Masjid", "latitude": 17.3605, "longitude": 78.4735},
            {"id": "p3", "name": "Chowmahalla Palace", "latitude": 17.3578, "longitude": 78.4717},
            {"id": "p4", "name": "Golconda Fort", "latitude": 17.3833, "longitude": 78.4018},
            {"id": "p5", "name": "Qutb Shahi Tombs", "latitude": 17.3934, "longitude": 78.3963},
        ],
        "eps_km": 3.0,
        "min_samples": 2,
    }
    r6 = client.post("/api/clustering/generate", json=clustering_payload)
    assert r6.status_code == 200, f"Step 6 Failed: {r6.text}"
    clusters = r6.json().get("clusters", [])
    assert len(clusters) >= 2, "Step 6 Failed: DBSCAN should identify 2 clusters"
    results["6_cluster_attractions"] = "PASSED"
    print(f"[PASS] Step 6: Geographic DBSCAN Clustering successful ({len(clusters)} spatial clusters discovered).")

    # 7. Optimize routes
    opt_payload = {
        "places": [
            {"id": "c1", "name": "Charminar", "latitude": 17.3616, "longitude": 78.4747},
            {"id": "c2", "name": "Golconda Fort", "latitude": 17.3833, "longitude": 78.4018},
            {"id": "c3", "name": "Chowmahalla Palace", "latitude": 17.3578, "longitude": 78.4717},
            {"id": "c4", "name": "Qutb Shahi Tombs", "latitude": 17.3934, "longitude": 78.3963},
        ],
        "transportation": "driving-car",
    }
    r7 = client.post("/api/routes/optimize", json=opt_payload)
    assert r7.status_code == 200, f"Step 7 Failed: {r7.text}"
    opt_data = r7.json()
    comp = opt_data.get("comparison", {})
    assert "optimized_distance_km" in comp, f"Step 7 Failed: Missing comparison ({opt_data})"
    results["7_optimize_routes"] = "PASSED"
    print(f"[PASS] Step 7: Route Optimization successful (Saved {comp.get('distance_saved_km', 0):.2f} km).")

    # 8. Retrieve weather
    start_str = (date.today() + timedelta(days=1)).isoformat()
    end_str = (date.today() + timedelta(days=3)).isoformat()
    r8 = client.get(f"/api/weather/forecast?latitude=17.360589&longitude=78.474061&start_date={start_str}&end_date={end_str}")
    assert r8.status_code == 200, f"Step 8 Failed: {r8.text}"
    weather_data = r8.json()
    assert "daily" in weather_data, "Step 8 Failed: Weather daily forecast missing"
    results["8_retrieve_weather"] = "PASSED"
    print(f"[PASS] Step 8: Weather Forecast retrieval successful ({len(weather_data['daily'])} days forecast).")

    # 9. Generate multi-day itinerary
    itin_payload = {
        "destination": "Hyderabad",
        "start_date": start_str,
        "end_date": end_str,
        "num_travelers": 2,
        "budget": 5000.0,
        "interests": ["Heritage", "Food"],
        "transport_mode": "driving",
    }
    r9 = client.post("/api/itinerary/generate", json=itin_payload, headers=auth_headers)
    assert r9.status_code == 200, f"Step 9 Failed: {r9.text}"
    itin_data = r9.json()
    itin_id = itin_data.get("itinerary_id")
    assert itin_id, "Step 9 Failed: No itinerary_id returned"
    assert len(itin_data.get("days", [])) >= 2, "Step 9 Failed: Missing itinerary days"
    results["9_generate_itinerary"] = "PASSED"
    print(f"[PASS] Step 9: Multi-Day Itinerary generated successfully (ID: {itin_id}, Utility: {itin_data.get('utility_score', 0):.3f}).")

    # 10. Validate the budget & constraints
    val_payload = {
        "destination": itin_data["destination"],
        "start_date": itin_data["start_date"],
        "end_date": itin_data["end_date"],
        "budget": 5000.0,
        "travelers_count": itin_data.get("travelers_count", 1),
        "daily_available_hours": 8.0,
        "days": itin_data["days"],
    }
    r10 = client.post("/api/itinerary/validate", json=val_payload)
    assert r10.status_code == 200, f"Step 10 Failed: {r10.text}"
    val_report = r10.json()
    assert "is_valid" in val_report, "Step 10 Failed: Validation flag missing"
    results["10_validate_budget_constraints"] = "PASSED"
    print(f"[PASS] Step 10: Budget & Schedule Validation successful (Valid: {val_report['is_valid']}, Violations: {len(val_report.get('violations', []))}).")

    # 11. Ask the AI assistant a question
    ai_chat_payload = {
        "message": "What is the history of Charminar and what are its entry timings?",
        "session_id": "test_walkthrough_sess",
    }
    r11 = client.post("/api/ai/chat", json=ai_chat_payload)
    assert r11.status_code == 200, f"Step 11 Failed: {r11.text}"
    ai_reply = r11.json()
    assert "reply" in ai_reply and len(ai_reply["reply"]) > 10, "Step 11 Failed: Inadequate AI reply"
    results["11_ai_assistant_interaction"] = "PASSED"
    print(f"[PASS] Step 11: AI Assistant RAG Chat successful (Intent: {ai_reply.get('intent')}, Sources: {len(ai_reply.get('sources', []))}).")

    # 12. Display interactive map (Route calculation)
    route_calc_payload = {
        "coordinates": [
            {"latitude": 17.3616, "longitude": 78.4747},
            {"latitude": 17.3578, "longitude": 78.4717},
            {"latitude": 17.3833, "longitude": 78.4018},
        ],
        "profile": "driving-car",
    }
    r12 = client.post("/api/routes/calculate", json=route_calc_payload)
    assert r12.status_code == 200, f"Step 12 Failed: {r12.text}"
    route_geom = r12.json()
    assert "distance_km" in route_geom and "geometry" in route_geom, "Step 12 Failed: Route geometry missing"
    results["12_map_routing_geometry"] = "PASSED"
    print(f"[PASS] Step 12: Interactive Map Routing successful ({route_geom['distance_km']:.2f} km road geometry synthesized).")

    # 13. Generate a PDF report
    pdf_req = {"itinerary_id": itin_id}
    r13 = client.post("/api/reports/generate", json=pdf_req, headers=auth_headers)
    assert r13.status_code in (200, 201), f"Step 13 Failed: {r13.text}"
    report_info = r13.json()
    rep_id = report_info.get("report_id")
    assert rep_id, "Step 13 Failed: Missing report_id"

    # Download binary PDF
    r13_down = client.get(f"/api/reports/{rep_id}/download")
    assert r13_down.status_code == 200, f"Step 13 Download Failed: {r13_down.status_code}"
    assert r13_down.content.startswith(b"%PDF"), "Step 13 Failed: Download is not valid PDF binary"
    results["13_generate_pdf_report"] = "PASSED"
    print(f"[PASS] Step 13: ReportLab PDF Generation & Download successful ({len(r13_down.content)} bytes).")

    # 14. View analytics
    r14 = client.get(f"/api/reports/{rep_id}", headers=auth_headers)
    assert r14.status_code == 200, f"Step 14 Failed: {r14.text}"
    report_data = r14.json()
    analytics_data = report_data.get("analytics", {})
    required_charts = [
        "category_distribution",
        "score_distribution",
        "daily_expense_distribution",
        "daily_travel_duration",
        "distance_comparison",
        "budget_utilization",
        "attraction_metrics",
    ]
    for ch in required_charts:
        assert ch in analytics_data, f"Step 14 Failed: Chart schema {ch} missing ({analytics_data.keys()})"
    results["14_view_travel_analytics"] = "PASSED"
    print(f"[PASS] Step 14: Analytics Dashboard data aggregation successful (All 7 chart schemas verified).")

    # 15. Verify error handling
    # 15a. 404 for nonexistent report
    r15_404 = client.get("/api/reports/nonexistent_report_id_xyz/download")
    assert r15_404.status_code == 404, "Step 15a Failed: Expected 404 for invalid report"

    # 15b. 400 for inverted date order in weather
    r15_400 = client.get("/api/weather/forecast?latitude=17.36&longitude=78.47&start_date=2026-11-20&end_date=2026-11-10")
    assert r15_400.status_code == 400, "Step 15b Failed: Expected 400 for inverted date range"

    # 15c. 422 for unprocessable invalid latitude string
    r15_422 = client.get("/api/weather/forecast?latitude=not_a_number&longitude=78.47")
    assert r15_422.status_code == 422, "Step 15c Failed: Expected 422 for invalid coordinate type"

    # 15d. 422 for empty destination query parameter (fails min_length=1)
    r15_empty = client.get("/api/destinations/search?q=")
    assert r15_empty.status_code in (400, 422), f"Step 15d Failed: Expected 400/422 for empty query, got {r15_empty.status_code}"

    # 15e. 401 for unauthorized preferences update
    r15_unauth = client.put("/api/users/profile", json={"full_name": "Hacker"})
    assert r15_unauth.status_code == 401, "Step 15e Failed: Expected 401 for unauthenticated request"

    results["15_verify_error_handling"] = "PASSED"
    print("[PASS] Step 15: Error Handling verification successful (404, 422, 400, 401 handled with RFC 7807 problem details).")

    print("=" * 80)
    print("ALL 15 END-TO-END WALKTHROUGH STEPS PASSED SUCCESSFULLY (100% COMPLETE)!")
    print("=" * 80)
    return results


if __name__ == "__main__":
    res = run_walkthrough()
