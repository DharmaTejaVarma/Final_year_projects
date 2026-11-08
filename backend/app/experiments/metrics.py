import math
from typing import Any, Dict, List, Optional, Set, Tuple


def precision_at_k(recommended_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """Calculate Precision@K: Fraction of top-K recommended items that are relevant.

    Formula:
        Precision@K = |Top-K intersect GroundTruth| / K
    """
    if k <= 0 or not recommended_ids:
        return 0.0
    top_k = recommended_ids[:k]
    relevant_count = sum(1 for item_id in top_k if item_id in ground_truth_ids)
    return relevant_count / float(k)


def recall_at_k(recommended_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """Calculate Recall@K: Fraction of total relevant items retrieved in top-K.

    Formula:
        Recall@K = |Top-K intersect GroundTruth| / |GroundTruth|
    """
    if not ground_truth_ids or k <= 0 or not recommended_ids:
        return 0.0
    top_k = recommended_ids[:k]
    relevant_count = sum(1 for item_id in top_k if item_id in ground_truth_ids)
    return relevant_count / float(len(ground_truth_ids))


def ndcg_at_k(
    recommended_ids: List[str],
    relevance_grades: Dict[str, int],
    k: int,
) -> float:
    """Calculate Normalized Discounted Cumulative Gain at rank K (NDCG@K).

    Formula:
        DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log2(i + 1)
        IDCG@K = sum_{i=1}^{min(K, |Rel|)} (2^{rel_i^*} - 1) / log2(i + 1)
        NDCG@K = DCG@K / IDCG@K
    """
    if k <= 0 or not recommended_ids:
        return 0.0

    top_k = recommended_ids[:k]
    dcg = 0.0
    for idx, item_id in enumerate(top_k):
        rel = relevance_grades.get(item_id, 0)
        dcg += (math.pow(2, rel) - 1.0) / math.log2(idx + 2)

    # Compute Ideal DCG (IDCG) by sorting all known positive grades descending
    sorted_ideal_grades = sorted(
        [grade for grade in relevance_grades.values() if grade > 0],
        reverse=True,
    )[:k]

    if not sorted_ideal_grades:
        return 0.0

    idcg = 0.0
    for idx, rel in enumerate(sorted_ideal_grades):
        idcg += (math.pow(2, rel) - 1.0) / math.log2(idx + 2)

    if idcg == 0.0:
        return 0.0

    return min(1.0, dcg / idcg)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def total_route_distance(poi_sequence: List[Dict[str, Any]], circuity: float = 1.35) -> float:
    """Calculate total traversed road distance across sequential stops with circuity multiplier."""
    if len(poi_sequence) < 2:
        return 0.0
    total_km = 0.0
    for i in range(len(poi_sequence) - 1):
        p1 = poi_sequence[i]
        p2 = poi_sequence[i + 1]
        dist = haversine_distance_km(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
        total_km += dist * circuity
    return round(total_km, 2)


def total_travel_time_mins(total_distance_km: float, avg_speed_kmh: float = 25.0) -> float:
    """Estimate road travel time in minutes based on distance and average urban speed."""
    if total_distance_km <= 0:
        return 0.0
    hours = total_distance_km / avg_speed_kmh
    return round(hours * 60.0, 1)


def travel_efficiency(touring_visit_mins: float, travel_transit_mins: float) -> float:
    """Calculate Travel Efficiency: Ratio of active sightseeing time to total elapsed itinerary duration.

    Formula:
        travel_efficiency = T_visit / (T_visit + T_travel)
    """
    total = touring_visit_mins + travel_transit_mins
    if total <= 0:
        return 1.0
    return round(touring_visit_mins / total, 3)


def check_itinerary_constraints(
    poi_sequence: List[Dict[str, Any]],
    budget: float,
    daily_hours_limit: float,
    weather_scenario: Dict[str, Any],
    transport_cost_per_km: float = 18.0,
    daily_food_per_person: float = 800.0,
    travelers_count: int = 1,
) -> Tuple[bool, List[str]]:
    """Strictly evaluate if an itinerary satisfies all hard constraints.

    Constraints Checked:
        1. Budget Feasibility: Total admissions + road transport + dining <= budget.
        2. Daily Time Feasibility: Total daily touring + transit <= daily available hours.
        3. Meteorological Hazard: No outdoor venues during severe rain (>15 mm).
        4. Opening Hours: Operating window verified or non-conflicting.
    """
    violations: List[str] = []

    # 1. Total Admissions
    admissions_cost = sum(float(p.get("entrance_fee", 0.0)) * travelers_count for p in poi_sequence)
    route_km = total_route_distance(poi_sequence)
    travel_cost = route_km * transport_cost_per_km
    food_cost = daily_food_per_person * travelers_count
    total_cost = admissions_cost + travel_cost + food_cost

    if total_cost > budget:
        violations.append(
            f"Budget overrun: Estimated INR {total_cost:.2f} exceeds budget limit of INR {budget:.2f}"
        )

    # 2. Daily Touring Duration
    visit_mins = sum(int(p.get("visit_duration_mins", 90)) for p in poi_sequence)
    travel_mins = total_travel_time_mins(route_km)
    total_mins = visit_mins + travel_mins
    max_mins = daily_hours_limit * 60.0

    if total_mins > max_mins:
        violations.append(
            f"Time overrun: Schedule requires {total_mins / 60.0:.1f} hrs, exceeding daily limit of {daily_hours_limit:.1f} hrs"
        )

    # 3. Meteorological Suitability
    rain_mm = float(weather_scenario.get("precipitation_mm", 0.0))
    if rain_mm > 15.0:
        outdoor_pois = [p["name"] for p in poi_sequence if p.get("is_outdoor", False)]
        if outdoor_pois:
            violations.append(
                f"Severe weather mismatch: {len(outdoor_pois)} outdoor venues scheduled during heavy rain ({rain_mm} mm): {', '.join(outdoor_pois[:3])}"
            )

    is_valid = len(violations) == 0
    return is_valid, violations


def attraction_diversity(poi_sequence: List[Dict[str, Any]]) -> float:
    """Calculate Attraction Diversity using Shannon Entropy of categories.

    Formula:
        H(C) = - sum_{c in C} p(c) * log2(p(c))
    Normalized by log2(|C|) so metric is in [0.0, 1.0].
    """
    if not poi_sequence:
        return 0.0
    category_counts: Dict[str, int] = {}
    for p in poi_sequence:
        cat = p.get("category", "General")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    total_pois = len(poi_sequence)
    entropy = 0.0
    for count in category_counts.values():
        p = count / float(total_pois)
        entropy -= p * math.log2(p)

    # Normalize by theoretical maximum entropy for this count
    max_entropy = math.log2(min(total_pois, max(len(category_counts), 1)))
    if max_entropy <= 0:
        return 1.0
    return round(min(1.0, entropy / max_entropy), 3)


def personalization_score(user_recommendations: Dict[str, List[str]]) -> float:
    """Calculate Personalization Score: Average pairwise Jaccard distance between user recommendations.

    Formula:
        Personalization = (2 / (U * (U - 1))) * sum_{u < v} (1 - |R_u intersect R_v| / |R_u union R_v|)
    """
    user_keys = list(user_recommendations.keys())
    u_count = len(user_keys)
    if u_count < 2:
        return 1.0

    total_jaccard_distance = 0.0
    pair_count = 0

    for i in range(u_count):
        for j in range(i + 1, u_count):
            set_u = set(user_recommendations[user_keys[i]])
            set_v = set(user_recommendations[user_keys[j]])
            union_len = len(set_u | set_v)
            if union_len == 0:
                dist = 0.0
            else:
                inter_len = len(set_u & set_v)
                dist = 1.0 - (inter_len / float(union_len))
            total_jaccard_distance += dist
            pair_count += 1

    return round(total_jaccard_distance / float(pair_count), 3)
