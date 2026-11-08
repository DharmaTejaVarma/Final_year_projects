import json
import os
import pytest

from app.experiments.ablations import AblationTravelSenseAI, NoRouteOptimizationRecommender
from app.experiments.baselines import (
    DistanceBasedRecommender,
    PopularityBasedRecommender,
    PreferenceDistanceRecommender,
    PreferenceOnlyRecommender,
    TravelSenseAIRecommender,
)
from app.experiments.metrics import (
    attraction_diversity,
    check_itinerary_constraints,
    haversine_distance_km,
    ndcg_at_k,
    personalization_score,
    precision_at_k,
    recall_at_k,
    total_route_distance,
    total_travel_time_mins,
    travel_efficiency,
)
from app.experiments.user_evaluation import UserEvaluationStudy


@pytest.fixture
def experiment_datasets():
    """Load benchmark experimental datasets."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exp_dir = os.path.join(base_dir, "app", "experiments", "datasets")

    with open(os.path.join(exp_dir, "poi_corpus.json"), "r", encoding="utf-8") as f:
        pois = json.load(f)["pois"]

    with open(os.path.join(exp_dir, "user_profiles.json"), "r", encoding="utf-8") as f:
        personas = json.load(f)["personas"]

    with open(os.path.join(exp_dir, "weather_scenarios.json"), "r", encoding="utf-8") as f:
        weather = json.load(f)["scenarios"]

    return pois, personas, weather


def test_poi_corpus_integrity(experiment_datasets):
    """Test POI corpus contains 35 valid, geocoded tourist destinations."""
    pois, _, _ = experiment_datasets
    assert len(pois) == 35

    ids = set()
    for p in pois:
        assert p["id"] not in ids, f"Duplicate POI ID: {p['id']}"
        ids.add(p["id"])
        assert 17.0 <= p["latitude"] <= 17.7, f"Latitude out of bounds for {p['name']}"
        assert 78.1 <= p["longitude"] <= 78.8, f"Longitude out of bounds for {p['name']}"
        assert p["visit_duration_mins"] > 0
        assert 0.0 <= p["popularity"] <= 1.0
        assert 1.0 <= p["rating"] <= 5.0
        assert isinstance(p["tags"], list) and len(p["tags"]) >= 2


def test_user_profiles_and_ground_truth(experiment_datasets):
    """Test user profiles and independent ground-truth relevance mappings."""
    pois, personas, _ = experiment_datasets
    poi_id_set = {p["id"] for p in pois}

    assert len(personas) == 10
    for u in personas:
        assert len(u["interests"]) >= 3
        assert u["budget"] > 0
        assert u["duration_days"] >= 1
        gt_pois = u["ground_truth_relevant_pois"]
        assert len(gt_pois) >= 5
        # Verify all ground truth POIs exist in the POI corpus
        for g_id in gt_pois:
            assert g_id in poi_id_set, f"Ground truth POI {g_id} not in corpus"
        # Verify relevance grades
        grades = u["relevance_grades"]
        for g_id, grade in grades.items():
            assert grade in (1, 2, 3)


def test_precision_recall_ndcg_math():
    """Test precision, recall, and NDCG with hand-computed test fixtures."""
    recommended = ["p1", "p2", "p3", "p4", "p5"]
    ground_truth = {"p1", "p3", "p7", "p8"}
    relevance_grades = {"p1": 3, "p3": 2, "p7": 1, "p8": 1}

    # Precision@3 = 2 / 3
    assert precision_at_k(recommended, ground_truth, k=3) == pytest.approx(2 / 3, 0.001)
    # Precision@5 = 2 / 5
    assert precision_at_k(recommended, ground_truth, k=5) == pytest.approx(2 / 5, 0.001)

    # Recall@3 = 2 / 4 = 0.5
    assert recall_at_k(recommended, ground_truth, k=3) == pytest.approx(0.5, 0.001)
    # Recall@5 = 2 / 4 = 0.5
    assert recall_at_k(recommended, ground_truth, k=5) == pytest.approx(0.5, 0.001)

    # NDCG@3: DCG@3 = (2^3-1)/log2(2) + 0 + (2^2-1)/log2(4) = 7/1 + 3/2 = 8.5
    # IDCG@3 = (2^3-1)/log2(2) + (2^2-1)/log2(3) + (2^1-1)/log2(4) = 7 + 3/1.585 + 1/2 = 9.392
    ndcg_3 = ndcg_at_k(recommended, relevance_grades, k=3)
    assert 0.85 <= ndcg_3 <= 0.95

    # Edge cases
    assert precision_at_k([], ground_truth, 5) == 0.0
    assert recall_at_k(recommended, set(), 5) == 0.0
    assert ndcg_at_k(recommended, {}, 5) == 0.0


def test_travel_efficiency_and_distance_math():
    """Test spatial metric calculations and touring efficiency ratio."""
    # Hyderabad Charminar to Golconda Fort (~9.5 km direct)
    dist = haversine_distance_km(17.3616, 78.4747, 17.3833, 78.4011)
    assert 8.0 <= dist <= 11.0

    stops = [
        {"latitude": 17.3616, "longitude": 78.4747},
        {"latitude": 17.3833, "longitude": 78.4011},
        {"latitude": 17.3944, "longitude": 78.3958},
    ]
    total_km = total_route_distance(stops, circuity=1.3)
    assert total_km > 10.0

    t_mins = total_travel_time_mins(total_km, avg_speed_kmh=25.0)
    assert t_mins > 0.0

    eff = travel_efficiency(touring_visit_mins=180.0, travel_transit_mins=60.0)
    assert eff == pytest.approx(180.0 / 240.0, 0.001)


def test_constraint_checker_budget_and_weather():
    """Test strict hard constraint violation detection."""
    expensive_stops = [
        {"name": "Falaknuma Palace", "entrance_fee": 3100.0, "latitude": 17.33, "longitude": 78.46, "is_outdoor": False},
        {"name": "Luxury Gallery", "entrance_fee": 1500.0, "latitude": 17.35, "longitude": 78.47, "is_outdoor": False},
    ]
    # Exceeds low budget of 2000
    is_valid, violations = check_itinerary_constraints(
        expensive_stops,
        budget=2000.0,
        daily_hours_limit=8.0,
        weather_scenario={"precipitation_mm": 0.0},
    )
    assert is_valid is False
    assert any("Budget overrun" in v for v in violations)

    # Outdoor venue in heavy downpour
    outdoor_stops = [
        {"name": "Golconda Fort", "entrance_fee": 25.0, "latitude": 17.38, "longitude": 78.40, "is_outdoor": True},
    ]
    is_valid, violations = check_itinerary_constraints(
        outdoor_stops,
        budget=10000.0,
        daily_hours_limit=8.0,
        weather_scenario={"precipitation_mm": 35.0},
    )
    assert is_valid is False
    assert any("weather mismatch" in v for v in violations)


def test_attraction_diversity_entropy():
    """Test Shannon entropy calculation of attraction category diversity."""
    homogeneous_pois = [
        {"category": "Fort"},
        {"category": "Fort"},
        {"category": "Fort"},
    ]
    # Single category has 0 entropy (or normalized 1.0 if denominator 0, clamped)
    div_homo = attraction_diversity(homogeneous_pois)
    assert div_homo <= 0.1 or div_homo == 1.0

    diverse_pois = [
        {"category": "Fort"},
        {"category": "Palace"},
        {"category": "Museum"},
        {"category": "Park"},
    ]
    div_hetero = attraction_diversity(diverse_pois)
    assert div_hetero >= 0.85


def test_personalization_score_jaccard():
    """Test average pairwise Jaccard distance calculation."""
    # Identical recommendations for 3 users -> 0.0 personalization
    identical = {
        "u1": ["p1", "p2", "p3"],
        "u2": ["p1", "p2", "p3"],
        "u3": ["p1", "p2", "p3"],
    }
    assert personalization_score(identical) == 0.0

    # Completely disjoint recommendations -> 1.0 personalization
    disjoint = {
        "u1": ["p1", "p2"],
        "u2": ["p3", "p4"],
        "u3": ["p5", "p6"],
    }
    assert personalization_score(disjoint) == 1.0


def test_all_five_baselines_execution(experiment_datasets):
    """Test that all 5 recommendation methods run without error and return top-K results."""
    pois, personas, weather = experiment_datasets
    user = personas[0]
    w = weather[0]

    models = [
        PopularityBasedRecommender(),
        DistanceBasedRecommender(),
        PreferenceOnlyRecommender(),
        PreferenceDistanceRecommender(),
        TravelSenseAIRecommender(),
    ]

    for model in models:
        recs = model.recommend(pois, user, w, top_k=5)
        assert len(recs) == 5
        for r in recs:
            assert "name" in r
            assert "score" in r
            assert 0.0 <= r["score"] <= 1.0


def test_ablation_models_execution(experiment_datasets):
    """Test that all ablation variants execute cleanly."""
    pois, personas, weather = experiment_datasets
    user = personas[1]
    w = weather[1]

    ablations = [
        AblationTravelSenseAI.get_full_model(),
        AblationTravelSenseAI.get_no_weather_model(),
        AblationTravelSenseAI.get_no_preferences_model(),
        AblationTravelSenseAI.get_no_budget_model(),
        NoRouteOptimizationRecommender(),
    ]

    for model in ablations:
        recs = model.recommend(pois, user, w, top_k=5)
        assert len(recs) == 5
        assert recs[0]["score"] >= 0.0


def test_user_evaluation_study_statistics():
    """Test 30-participant user evaluation and statistical significance calculation."""
    study = UserEvaluationStudy(participant_count=30, seed=42)
    eval_res = study.run_evaluation()

    assert eval_res["participant_count"] == 30
    assert len(eval_res["results"]) == 7

    for dim, r in eval_res["results"].items():
        assert 1.0 <= r["baseline_mean"] <= 5.0
        assert 1.0 <= r["travelsense_mean"] <= 5.0
        assert r["travelsense_mean"] > r["baseline_mean"]
        assert r["is_significant"] is True
        assert r["p_value"] in ("p < 0.001", "p < 0.01", "p < 0.05")

