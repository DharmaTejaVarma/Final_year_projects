import math
from typing import Any, Dict, List, Optional, Tuple

try:
    from app.algorithms.geographic_clustering import run_dbscan_haversine, haversine_distance_km
    from app.algorithms.poi_scoring import (
        ScoringWeights,
        calculate_budget_score,
        calculate_category_score,
        calculate_distance_score,
        calculate_final_score,
        calculate_preference_score,
        calculate_time_score,
        calculate_weather_score,
    )
    from app.algorithms.route_optimizer import (
        compute_distance_matrix,
        nearest_neighbor_tour,
        two_opt_local_search,
    )
except ImportError:
    from backend.app.algorithms.geographic_clustering import run_dbscan_haversine, haversine_distance_km
    from backend.app.algorithms.poi_scoring import (
        ScoringWeights,
        calculate_budget_score,
        calculate_category_score,
        calculate_distance_score,
        calculate_final_score,
        calculate_preference_score,
        calculate_time_score,
        calculate_weather_score,
    )
    from backend.app.algorithms.route_optimizer import (
        compute_distance_matrix,
        nearest_neighbor_tour,
        two_opt_local_search,
    )

haversine_distance = haversine_distance_km


class BaseRecommender:
    """Abstract base recommender interface for experimental evaluation."""

    def __init__(self, name: str):
        self.name = name

    def recommend(
        self,
        candidate_pois: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        weather_scenario: Dict[str, Any],
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError


class PopularityBasedRecommender(BaseRecommender):
    """Baseline 1: Ranks attractions strictly by public popularity and ratings."""

    def __init__(self):
        super().__init__("Baseline 1: Popularity-Based")

    def recommend(
        self,
        candidate_pois: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        weather_scenario: Dict[str, Any],
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        scored = []
        for p in candidate_pois:
            pop = float(p.get("popularity", 0.5))
            rating = float(p.get("rating", 3.0)) / 5.0
            score = round(pop * 0.6 + rating * 0.4, 4)
            item = dict(p)
            item["score"] = score
            scored.append(item)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


class DistanceBasedRecommender(BaseRecommender):
    """Baseline 2: Ranks attractions strictly by proximity to starting location."""

    def __init__(self, max_radius_km: float = 35.0):
        super().__init__("Baseline 2: Distance-Based")
        self.max_radius_km = max_radius_km

    def recommend(
        self,
        candidate_pois: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        weather_scenario: Dict[str, Any],
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        start = user_profile.get("start_location", {"latitude": 17.3616, "longitude": 78.4747})
        start_lat = float(start.get("latitude", 17.3616))
        start_lon = float(start.get("longitude", 78.4747))

        scored = []
        for p in candidate_pois:
            p_lat = float(p["latitude"])
            p_lon = float(p["longitude"])
            dist = haversine_distance(start_lat, start_lon, p_lat, p_lon)
            proximity_score = max(0.0, 1.0 - (dist / self.max_radius_km))
            item = dict(p)
            item["distance_km"] = round(dist, 2)
            item["score"] = round(proximity_score, 4)
            scored.append(item)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


class PreferenceOnlyRecommender(BaseRecommender):
    """Baseline 3: Ranks attractions strictly by semantic & category preference alignment."""

    def __init__(self):
        super().__init__("Baseline 3: Preference-Only")

    def recommend(
        self,
        candidate_pois: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        weather_scenario: Dict[str, Any],
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        interests = user_profile.get("interests", [])
        scored = []
        for p in candidate_pois:
            tags = p.get("tags", [])
            category = p.get("category", "")
            name = p.get("name", "")
            cats = [category] + tags
            pref_score = calculate_preference_score(
                user_interests=interests,
                place_categories=cats,
                place_name=name,
            )
            item = dict(p)
            item["score"] = round(pref_score, 4)
            scored.append(item)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


class PreferenceDistanceRecommender(BaseRecommender):
    """Baseline 4: Hybrid combining preference match and geographic proximity."""

    def __init__(self, pref_weight: float = 0.6, dist_weight: float = 0.4):
        super().__init__("Baseline 4: Preference + Distance")
        self.pref_weight = pref_weight
        self.dist_weight = dist_weight

    def recommend(
        self,
        candidate_pois: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        weather_scenario: Dict[str, Any],
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        interests = user_profile.get("interests", [])
        start = user_profile.get("start_location", {"latitude": 17.3616, "longitude": 78.4747})
        start_lat = float(start.get("latitude", 17.3616))
        start_lon = float(start.get("longitude", 78.4747))

        scored = []
        for p in candidate_pois:
            tags = p.get("tags", [])
            cats = [p.get("category", "")] + tags
            pref_score = calculate_preference_score(
                user_interests=interests,
                place_categories=cats,
                place_name=p.get("name", ""),
            )
            dist = haversine_distance(start_lat, start_lon, float(p["latitude"]), float(p["longitude"]))
            dist_score = max(0.0, 1.0 - (dist / 35.0))
            combined = self.pref_weight * pref_score + self.dist_weight * dist_score

            item = dict(p)
            item["distance_km"] = round(dist, 2)
            item["score"] = round(combined, 4)
            scored.append(item)

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


class TravelSenseAIRecommender(BaseRecommender):
    """Proposed Framework: Full Context-Aware 6-Factor Multi-Criteria Scoring + DBSCAN + 2-Opt TSP."""

    def __init__(self, custom_weights: Optional[ScoringWeights] = None):
        super().__init__("Proposed Method: TravelSenseAI")
        self.weights = (custom_weights or ScoringWeights()).normalized()

    def recommend(
        self,
        candidate_pois: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        weather_scenario: Dict[str, Any],
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        interests = user_profile.get("interests", [])
        budget = float(user_profile.get("budget", 5000.0))
        duration_days = max(int(user_profile.get("duration_days", 2)), 1)
        daily_hours = float(user_profile.get("daily_hours", 8.0))
        start = user_profile.get("start_location", {"latitude": 17.3616, "longitude": 78.4747})
        start_lat = float(start.get("latitude", 17.3616))
        start_lon = float(start.get("longitude", 78.4747))

        w_code = int(weather_scenario.get("weather_code", 1))
        w_rain = float(weather_scenario.get("precipitation_mm", 0.0))
        w_temp = float(weather_scenario.get("temperature_celsius", 25.0))

        scored = []
        for p in candidate_pois:
            tags = p.get("tags", [])
            cats = [p.get("category", "")] + tags
            # If place is outdoor, add outdoor tag so calculate_weather_score detects it
            if p.get("is_outdoor", False):
                cats.append("outdoor")
            else:
                cats.append("indoor")

            # 1. Preference
            p_score = calculate_preference_score(
                user_interests=interests,
                place_categories=cats,
                place_name=p.get("name", ""),
            )
            # 2. Distance
            dist = haversine_distance(start_lat, start_lon, float(p["latitude"]), float(p["longitude"]))
            d_score = calculate_distance_score(dist, max_radius_km=35.0)

            # 3. Time
            t_score = calculate_time_score(
                visit_duration_mins=int(p.get("visit_duration_mins", 90)),
                daily_available_hours=daily_hours,
            )

            # 4. Weather
            w_score = calculate_weather_score(
                weather_code=w_code,
                precipitation_mm=w_rain,
                place_categories=cats,
                max_temp_celsius=w_temp,
            )

            # 5. Budget
            b_score = calculate_budget_score(
                entrance_fee=float(p.get("entrance_fee", 0.0)),
                user_budget=budget,
                total_trip_days=duration_days,
            )

            # 6. Category
            c_score = calculate_category_score(
                place_categories=cats,
                target_categories=interests,
            )

            factors = {
                "preference": p_score,
                "distance": d_score,
                "time": t_score,
                "weather": w_score,
                "category": c_score,
                "budget": b_score,
            }
            final_score = calculate_final_score(factors, weights=self.weights)

            item = dict(p)
            item["score"] = round(final_score, 4)
            item["distance_km"] = round(dist, 2)
            item["factor_scores"] = factors
            scored.append(item)

        scored.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = scored[:top_k]

        # 7. Apply 2-Opt TSP optimization to sequence the selected attractions
        if len(top_candidates) >= 3:
            coords = [(float(p["latitude"]), float(p["longitude"])) for p in top_candidates]
            dist_matrix = compute_distance_matrix(coords)
            init_tour = nearest_neighbor_tour(dist_matrix, start_idx=0)
            opt_tour, _ = two_opt_local_search(init_tour, dist_matrix, max_iterations=50)
            sequenced = [top_candidates[idx] for idx in opt_tour]
            return sequenced

        return top_candidates
