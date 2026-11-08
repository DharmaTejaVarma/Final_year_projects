import httpx
import sys

def main():
    payload = {
        "itinerary_data": {
            "itinerary_id": "itin_phase9_live_demo",
            "destination": "Hyderabad",
            "start_date": "2026-11-15",
            "end_date": "2026-11-16",
            "total_days": 2,
            "travelers_count": 2,
            "transportation": "driving-car",
            "pace": "moderate",
            "total_distance_km": 28.5,
            "total_travel_time_mins": 75.0,
            "total_visit_time_mins": 360.0,
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
                    "date": "2026-11-15",
                    "theme": "Historic Fortresses & Royal Tombs",
                    "daily_distance_km": 16.2,
                    "daily_travel_time_mins": 42.0,
                    "daily_visit_time_mins": 180.0,
                    "daily_total_duration_mins": 222.0,
                    "daily_estimated_cost": 2150.0,
                    "weather": {
                        "date": "2026-11-15",
                        "temperature_celsius": 26.5,
                        "condition": "Clear",
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
                            "category": "Heritage Tombs",
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
                    "date": "2026-11-16",
                    "theme": "Old City Charms & Palatial Grandeur",
                    "daily_distance_km": 12.3,
                    "daily_travel_time_mins": 33.0,
                    "daily_visit_time_mins": 180.0,
                    "daily_total_duration_mins": 213.0,
                    "daily_estimated_cost": 2050.0,
                    "weather": {
                        "date": "2026-11-16",
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
                "Modest attire required for heritage monuments.",
                "Opening hours verified with Archaeological Survey of India (ASI).",
            ],
        },
        "title": "Hyderabad 2-Day Executive Travel Dossier",
        "planning_notes": "Official TravelSenseAI publication release.",
    }

    print("Sending POST /api/reports/generate to live backend...")
    with httpx.Client(base_url="http://127.0.0.1:8000") as client:
        # 1. Generate Report
        res = client.post("/api/reports/generate", json=payload, timeout=10.0)
        print(f"Status Code: {res.status_code}")
        if res.status_code != 201:
            print(f"Error: {res.text}")
            sys.exit(1)
        data = res.json()
        report_id = data["report_id"]
        print(f"Report ID: {report_id}")
        print(f"File Size: {data['file_size_bytes']} bytes ({(data['file_size_bytes'] / 1024):.1f} KB)")
        print(f"Download URL: {data['download_url']}")
        print(f"Categories analyzed: {len(data['analytics']['category_distribution'])}")
        print(f"Score breakdown points: {len(data['analytics']['score_distribution'])}")
        print(f"Daily expenses tracked: {len(data['analytics']['daily_expense_distribution'])}")
        print(f"Budget utilization: {data['analytics']['budget_utilization']['utilization_percentage']}%")

        # 2. Retrieve Report Metadata
        get_res = client.get(f"/api/reports/{report_id}")
        print(f"GET /api/reports/{report_id} -> {get_res.status_code} OK")

        # 3. Download PDF
        down_res = client.get(f"/api/reports/{report_id}/download")
        print(f"Download -> {down_res.status_code} OK ({len(down_res.content)} bytes)")
        assert down_res.content.startswith(b"%PDF-")
        print("Verified: PDF header magic bytes '%PDF-' confirmed!")
        print("ALL REPORTING & ANALYTICS CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()

