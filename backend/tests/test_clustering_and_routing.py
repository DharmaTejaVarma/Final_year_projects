import pytest
from fastapi.testclient import TestClient

try:
    from app.algorithms.geographic_clustering import (
        haversine_distance_km,
        run_dbscan_haversine,
        run_kmeans_comparison,
        calculate_cluster_envelope,
        get_dbscan_suitability_explanation,
    )
    from app.algorithms.route_optimizer import (
        calculate_leg_road_metrics,
        compute_distance_matrix,
        nearest_neighbor_tour,
        two_opt_local_search,
        partition_daily_routes,
        minutes_to_time_str,
        time_str_to_minutes,
    )
    from app.schemas.clustering_and_routing import POIInput
    from app.main import app
except ImportError:
    from backend.app.algorithms.geographic_clustering import (
        haversine_distance_km,
        run_dbscan_haversine,
        run_kmeans_comparison,
        calculate_cluster_envelope,
        get_dbscan_suitability_explanation,
    )
    from backend.app.algorithms.route_optimizer import (
        calculate_leg_road_metrics,
        compute_distance_matrix,
        nearest_neighbor_tour,
        two_opt_local_search,
        partition_daily_routes,
        minutes_to_time_str,
        time_str_to_minutes,
    )
    from backend.app.schemas.clustering_and_routing import POIInput
    from backend.app.main import app

client = TestClient(app)

# Real coordinates for landmark Hyderabad attractions:
# Cluster A (Golconda Fort precinct):
GOLCONDA = (17.3833, 78.4011)
QUTB_SHAHI = (17.3942, 78.3957)

# Cluster B (Old City precinct):
CHARMINAR = (17.3616, 78.4747)
CHOWMAHALLA = (17.3578, 78.4717)
SALAR_JUNG = (17.3713, 78.4804)

# Isolated Outlier (~30+ km southeast):
RAMOJI = (17.3120, 78.6808)


# ==============================================================================
# 1. GEOGRAPHIC CLUSTERING ALGORITHMS
# ==============================================================================
def test_haversine_distance_accuracy():
    """Verify Haversine formula against known geodetic distances."""
    # Charminar to Chowmahalla Palace is ~0.5 - 0.7 km straight line
    dist_old_city = haversine_distance_km(CHARMINAR[0], CHARMINAR[1], CHOWMAHALLA[0], CHOWMAHALLA[1])
    assert 0.3 < dist_old_city < 1.0

    # Golconda to Qutb Shahi Tombs is ~1.2 - 2.0 km
    dist_fort = haversine_distance_km(GOLCONDA[0], GOLCONDA[1], QUTB_SHAHI[0], QUTB_SHAHI[1])
    assert 1.0 < dist_fort < 2.5

    # Charminar to Ramoji Film City is ~25 - 35 km
    dist_ramoji = haversine_distance_km(CHARMINAR[0], CHARMINAR[1], RAMOJI[0], RAMOJI[1])
    assert 20.0 < dist_ramoji < 35.0


def test_dbscan_clustering_nearby_and_distant():
    """Verify DBSCAN clusters nearby attractions and flags distant ones as noise."""
    coords = [
        GOLCONDA,       # idx 0: Cluster 1 (West)
        QUTB_SHAHI,     # idx 1: Cluster 1 (West)
        CHARMINAR,      # idx 2: Cluster 2 (East Old City)
        CHOWMAHALLA,    # idx 3: Cluster 2 (East Old City)
        SALAR_JUNG,     # idx 4: Cluster 2 (East Old City)
        RAMOJI,         # idx 5: Distant Outlier
    ]

    labels = run_dbscan_haversine(coords, eps_km=3.0, min_samples=2)

    assert len(labels) == 6
    # Golconda & Qutb Shahi Tombs should share the same cluster ID >= 0
    assert labels[0] >= 0
    assert labels[0] == labels[1]

    # Charminar, Chowmahalla, Salar Jung should share the same cluster ID >= 0
    assert labels[2] >= 0
    assert labels[2] == labels[3] == labels[4]

    # Western cluster and Eastern cluster must be distinct
    assert labels[0] != labels[2]

    # Ramoji Film City (over 25km away) must be marked as noise (-1)
    assert labels[5] == -1


def test_dbscan_edge_cases():
    """Verify empty input and single-point inputs behave safely."""
    # Empty
    assert run_dbscan_haversine([], eps_km=3.0, min_samples=2) == []

    # Fewer points than min_samples -> all noise (-1)
    single_label = run_dbscan_haversine([GOLCONDA], eps_km=3.0, min_samples=2)
    assert single_label == [-1]


def test_kmeans_comparison_baseline():
    """Verify K-Means runs as a comparative baseline with inertia and distribution."""
    coords = [GOLCONDA, QUTB_SHAHI, CHARMINAR, CHOWMAHALLA, SALAR_JUNG, RAMOJI]
    km_result = run_kmeans_comparison(coords, k=2)

    assert km_result["k"] == 2
    assert km_result["clusters_count"] == 2
    assert len(km_result["labels"]) == 6
    assert km_result["inertia"] >= 0.0
    assert "cluster_distribution" in km_result
    assert "Cluster 0" in km_result["cluster_distribution"]


def test_cluster_envelope_calculation():
    """Verify geographic centroid, radius, and bounding box calculations."""
    cluster_coords = [CHARMINAR, CHOWMAHALLA, SALAR_JUNG]
    envelope = calculate_cluster_envelope(cluster_coords)

    centroid = envelope["centroid"]
    assert 17.35 <= centroid["latitude"] <= 17.38
    assert 78.46 <= centroid["longitude"] <= 78.49
    assert envelope["radius_km"] > 0.0
    assert envelope["bounding_box"]["min_lat"] <= envelope["bounding_box"]["max_lat"]


def test_dbscan_suitability_explanation():
    """Ensure suitability justification documents the architectural reasons."""
    explanation = get_dbscan_suitability_explanation()
    assert "Arbitrary Cluster Geometries" in explanation
    assert "No Prior Cluster Count (K) Required" in explanation
    assert "Noise & Outlier" in explanation
    assert "Haversine" in explanation


# ==============================================================================
# 2. ROUTE OPTIMIZATION ALGORITHMS
# ==============================================================================
def test_time_conversions():
    """Verify time conversions to/from minutes."""
    assert time_str_to_minutes("09:00") == 540
    assert time_str_to_minutes("14:30") == 870
    assert minutes_to_time_str(540) == "09:00"
    assert minutes_to_time_str(870) == "14:30"


def test_road_metrics_circuity():
    """Verify road metrics apply speed and circuity factors properly."""
    road_km, dur_mins = calculate_leg_road_metrics(
        CHARMINAR[0], CHARMINAR[1], RAMOJI[0], RAMOJI[1], transportation="driving-car"
    )
    straight_km = haversine_distance_km(CHARMINAR[0], CHARMINAR[1], RAMOJI[0], RAMOJI[1])

    # Road km must be greater than straight line by 1.30x factor
    assert road_km > straight_km
    assert 1.25 <= (road_km / straight_km) <= 1.35
    assert dur_mins > 0.0


def test_two_opt_untangles_crossed_tours():
    """Verify 2-Opt local search untangles crossed paths and produces a strictly shorter route."""
    # 4 points forming a square: (0,0), (0,10), (10,10), (10,0)
    # Crossed tour: (0,0) -> (10,10) -> (0,10) -> (10,0) has length ~ 14.14 + 10 + 14.14 = 38.28
    # Uncrossed tour: (0,0) -> (0,10) -> (10,10) -> (10,0) has length 10 + 10 + 10 = 30.0
    sq_coords = [(0.0, 0.0), (0.0, 0.1), (0.1, 0.1), (0.1, 0.0)]
    matrix = compute_distance_matrix(sq_coords, transportation="driving-car")

    # Crossed order: 0 -> 2 -> 1 -> 3
    crossed_tour = [0, 2, 1, 3]
    crossed_dist = matrix[0][2] + matrix[2][1] + matrix[1][3]

    optimized_tour, optimized_dist = two_opt_local_search(
        tour=crossed_tour,
        dist_matrix=matrix,
        fixed_start=True,
        fixed_end=False,
    )

    assert optimized_dist < crossed_dist
    assert optimized_tour[0] == 0


def test_partition_daily_routes():
    """Verify attractions partition into multiple days when exceeding daily hours."""
    poi_1 = POIInput(id=1, name="Stop 1", latitude=17.36, longitude=78.47, visit_duration_mins=180)
    poi_2 = POIInput(id=2, name="Stop 2", latitude=17.37, longitude=78.48, visit_duration_mins=180)
    poi_3 = POIInput(id=3, name="Stop 3", latitude=17.38, longitude=78.49, visit_duration_mins=180)

    # With daily available hours = 4.0 hours (240 mins), each 180 min POI + travel will spill over
    daily_routes = partition_daily_routes(
        ordered_places=[poi_1, poi_2, poi_3],
        start_location=None,
        end_location=None,
        transportation="driving-car",
        daily_available_hours=4.0,
        start_time_str="09:00",
    )

    # 3 POIs of 3 hours each cannot fit in a 4-hour day; must require multiple days
    assert len(daily_routes) >= 2
    assert daily_routes[0].day_number == 1
    assert len(daily_routes[0].stops) >= 1
    assert daily_routes[0].stops[0].arrival_time == "09:00"


# ==============================================================================
# 3. ENDPOINT INTEGRATION TESTS
# ==============================================================================
def test_clustering_generate_endpoint_success():
    """Test POST /api/clustering/generate returns valid clusters, centroids, and noise identification."""
    payload = {
        "places": [
            {"id": "golconda", "name": "Golconda Fort", "latitude": 17.3833, "longitude": 78.4011, "category": "heritage.fort"},
            {"id": "qutb", "name": "Qutb Shahi Tombs", "latitude": 17.3942, "longitude": 78.3957, "category": "heritage.monument"},
            {"id": "charminar", "name": "Charminar", "latitude": 17.3616, "longitude": 78.4747, "category": "heritage.monument"},
            {"id": "chowmahalla", "name": "Chowmahalla Palace", "latitude": 17.3578, "longitude": 78.4717, "category": "heritage.palace"},
            {"id": "ramoji", "name": "Ramoji Film City", "latitude": 17.3120, "longitude": 78.6808, "category": "entertainment"},
        ],
        "eps_km": 3.5,
        "min_samples": 2,
        "compare_kmeans": True,
        "k": 2,
    }

    res = client.post("/api/clustering/generate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["total_places"] == 5
    assert data["clusters_count"] >= 1
    assert data["noise_count"] >= 1  # Ramoji Film City should be noise
    assert len(data["clusters"]) >= 2

    # Check that noise cluster has Ramoji Film City
    noise_cluster = next((c for c in data["clusters"] if c["is_noise"]), None)
    assert noise_cluster is not None
    noise_place_ids = [p["id"] for p in noise_cluster["places"]]
    assert "ramoji" in noise_place_ids

    # Check non-noise cluster has centroid and radius
    valid_clusters = [c for c in data["clusters"] if not c["is_noise"]]
    assert len(valid_clusters) >= 1
    for c in valid_clusters:
        assert c["centroid"] is not None
        assert c["radius_km"] >= 0.0

    # Check K-Means comparison
    assert data["kmeans_comparison"] is not None
    assert data["kmeans_comparison"]["k"] == 2

    # Check suitability explanation
    assert len(data["dbscan_suitability_explanation"]) > 50


def test_clustering_endpoint_empty_and_invalid():
    """Test validation errors for empty places list and invalid coordinates."""
    # Empty list
    res_empty = client.post("/api/clustering/generate", json={"places": []})
    assert res_empty.status_code == 422

    # Invalid latitude (> 90)
    res_invalid_lat = client.post(
        "/api/clustering/generate",
        json={"places": [{"name": "Invalid", "latitude": 95.0, "longitude": 78.0}]},
    )
    assert res_invalid_lat.status_code == 422


def test_route_optimize_endpoint_success():
    """Test POST /api/routes/optimize returns optimized visiting sequence and comparison metrics."""
    payload = {
        "places": [
            {"id": "p1", "name": "Golconda Fort", "latitude": 17.3833, "longitude": 78.4011, "visit_duration_mins": 90},
            {"id": "p2", "name": "Charminar", "latitude": 17.3616, "longitude": 78.4747, "visit_duration_mins": 60},
            {"id": "p3", "name": "Qutb Shahi Tombs", "latitude": 17.3942, "longitude": 78.3957, "visit_duration_mins": 60},
            {"id": "p4", "name": "Chowmahalla Palace", "latitude": 17.3578, "longitude": 78.4717, "visit_duration_mins": 75},
        ],
        "start_location": {
            "name": "Taj Falaknuma Hotel",
            "latitude": 17.3314,
            "longitude": 78.4674,
            "visit_duration_mins": 0,
        },
        "end_location": {
            "name": "Taj Falaknuma Hotel",
            "latitude": 17.3314,
            "longitude": 78.4674,
            "visit_duration_mins": 0,
        },
        "transportation": "driving-car",
        "daily_available_hours": 8.0,
        "start_time": "09:00",
    }

    res = client.post("/api/routes/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["transportation"] == "driving-car"
    assert data["total_places_visited"] == 4
    assert data["total_days"] >= 1
    assert data["total_distance_km"] > 0.0

    # Comparison metrics
    comp = data["comparison"]
    assert comp["initial_distance_km"] > 0.0
    assert comp["optimized_distance_km"] > 0.0
    assert comp["improvement_percentage"] >= 0.0
    assert "2-Opt" in comp["method_used"]

    # Daily itinerary
    daily_routes = data["daily_routes"]
    assert len(daily_routes) >= 1
    day1 = daily_routes[0]
    assert len(day1["stops"]) >= 4
    assert day1["geometry"] is not None
    assert len(day1["geometry"]) > 0

    # First stop should be start_location
    assert day1["stops"][0]["is_start_location"] is True
    assert day1["stops"][0]["arrival_time"] == "09:00"


def test_route_optimize_walking_mode():
    """Test route optimization with walking transportation profile."""
    payload = {
        "places": [
            {"id": "charminar", "name": "Charminar", "latitude": 17.3616, "longitude": 78.4747, "visit_duration_mins": 45},
            {"id": "chowmahalla", "name": "Chowmahalla Palace", "latitude": 17.3578, "longitude": 78.4717, "visit_duration_mins": 45},
        ],
        "transportation": "foot-walking",
        "daily_available_hours": 6.0,
    }

    res = client.post("/api/routes/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["transportation"] == "foot-walking"
    assert data["total_places_visited"] == 2


def test_route_optimize_validation():
    """Verify rejection of empty list and invalid transportation mode."""
    # Empty
    res_empty = client.post("/api/routes/optimize", json={"places": []})
    assert res_empty.status_code == 422

    # Invalid transportation mode
    res_mode = client.post(
        "/api/routes/optimize",
        json={
            "places": [{"name": "P1", "latitude": 17.36, "longitude": 78.47}],
            "transportation": "airplane",
        },
    )
    assert res_mode.status_code == 422

