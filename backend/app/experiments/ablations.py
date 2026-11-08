from typing import Any, Dict, List, Optional
try:
    from app.algorithms.poi_scoring import ScoringWeights
    from app.experiments.baselines import TravelSenseAIRecommender
except ImportError:
    from backend.app.algorithms.poi_scoring import ScoringWeights
    from backend.app.experiments.baselines import TravelSenseAIRecommender


class AblationTravelSenseAI:
    """Configurable ablation models to measure individual component contributions."""

    @staticmethod
    def get_full_model() -> TravelSenseAIRecommender:
        """1. Full TravelSenseAI framework with all 6 factors and 2-Opt route optimization."""
        return TravelSenseAIRecommender()

    @staticmethod
    def get_no_weather_model() -> TravelSenseAIRecommender:
        """2. Ablation: Without Weather Context (w_W = 0.0)."""
        w = ScoringWeights(
            preference=0.35,
            distance=0.20,
            time=0.20,
            weather=0.00,
            category=0.15,
            budget=0.10,
        )
        model = TravelSenseAIRecommender(custom_weights=w)
        model.name = "Ablation: Without Weather"
        return model

    @staticmethod
    def get_no_preferences_model() -> TravelSenseAIRecommender:
        """3. Ablation: Without User Preference Modeling (w_P = 0.0)."""
        w = ScoringWeights(
            preference=0.00,
            distance=0.25,
            time=0.25,
            weather=0.20,
            category=0.15,
            budget=0.15,
        )
        model = TravelSenseAIRecommender(custom_weights=w)
        model.name = "Ablation: Without Preferences"
        return model

    @staticmethod
    def get_no_budget_model() -> TravelSenseAIRecommender:
        """4. Ablation: Without Budget Constraints (w_B = 0.0)."""
        w = ScoringWeights(
            preference=0.35,
            distance=0.20,
            time=0.20,
            weather=0.15,
            category=0.10,
            budget=0.00,
        )
        model = TravelSenseAIRecommender(custom_weights=w)
        model.name = "Ablation: Without Budget"
        return model


class NoRouteOptimizationRecommender(TravelSenseAIRecommender):
    """5. Ablation: TravelSenseAI without 2-Opt route optimization (naive order)."""

    def __init__(self):
        super().__init__()
        self.name = "Ablation: Without Route Optimization"

    def recommend(
        self,
        candidate_pois: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        weather_scenario: Dict[str, Any],
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:
        # Call base scoring but DO NOT apply 2-Opt TSP
        interests = user_profile.get("interests", [])
        budget = float(user_profile.get("budget", 5000.0))
        duration_days = max(int(user_profile.get("duration_days", 2)), 1)
        daily_hours = float(user_profile.get("daily_hours", 8.0))
        start = user_profile.get("start_location", {"latitude": 17.3616, "longitude": 78.4747})
        start_lat = float(start.get("latitude", 17.3616))
        start_lon = float(start.get("longitude", 78.4747))

        w_rain = float(weather_scenario.get("precipitation_mm", 0.0))
        w_temp = float(weather_scenario.get("temperature_celsius", 25.0))

        try:
            from app.algorithms.geographic_clustering import haversine_distance_km as haversine_distance
            from app.algorithms.poi_scoring import (
                calculate_budget_score,
                calculate_category_score,
                calculate_distance_score,
                calculate_final_score,
                calculate_preference_score,
                calculate_time_score,
                calculate_weather_score,
            )
        except ImportError:
            from backend.app.algorithms.geographic_clustering import haversine_distance_km as haversine_distance
            from backend.app.algorithms.poi_scoring import (
                calculate_budget_score,
                calculate_category_score,
                calculate_distance_score,
                calculate_final_score,
                calculate_preference_score,
                calculate_time_score,
                calculate_weather_score,
            )

        scored = []
        w_code = int(weather_scenario.get("weather_code", 1))
        for p in candidate_pois:
            tags = p.get("tags", [])
            cats = [p.get("category", "")] + tags
            if p.get("is_outdoor", False):
                cats.append("outdoor")
            else:
                cats.append("indoor")

            p_score = calculate_preference_score(
                user_interests=interests,
                place_categories=cats,
                place_name=p.get("name", ""),
            )
            dist = haversine_distance(start_lat, start_lon, float(p["latitude"]), float(p["longitude"]))
            d_score = calculate_distance_score(dist, max_radius_km=35.0)
            t_score = calculate_time_score(int(p.get("visit_duration_mins", 90)), daily_hours)
            w_score = calculate_weather_score(
                weather_code=w_code,
                precipitation_mm=w_rain,
                place_categories=cats,
                max_temp_celsius=w_temp,
            )
            b_score = calculate_budget_score(
                entrance_fee=float(p.get("entrance_fee", 0.0)),
                user_budget=budget,
                total_trip_days=duration_days,
            )
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
            scored.append(item)

        # Naive score order without 2-Opt road sequencing
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
