from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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
    from app.core.logger import logger
    from app.models.destination import Destination, Place
    from app.schemas.recommendation import (
        BaselineComparison,
        FactorScores,
        RecommendationRequest,
        RecommendationResponse,
        RecommendedPOI,
    )
    from app.services.geoapify_service import geoapify_service
    from app.services.image_service import image_service
    from app.services.ors_service import ors_service
    from app.services.weather_service import weather_service
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
    from backend.app.core.logger import logger
    from backend.app.models.destination import Destination, Place
    from backend.app.schemas.recommendation import (
        BaselineComparison,
        FactorScores,
        RecommendationRequest,
        RecommendationResponse,
        RecommendedPOI,
    )
    from backend.app.services.geoapify_service import geoapify_service
    from backend.app.services.image_service import image_service
    from backend.app.services.ors_service import ors_service
    from backend.app.services.weather_service import weather_service


class RecommendationService:
    """Context-aware recommendation engine orchestrating geospatial retrieval,
    weather forecasts, multi-criteria scoring, and empirical ranking.
    """

    async def get_recommendations(
        self,
        request: RecommendationRequest,
        db: Optional[Session] = None,
    ) -> RecommendationResponse:
        """Generate ranked recommendations for a given trip context."""
        logger.info(
            f"Generating recommendations for '{request.destination}' with interests: {request.interests}"
        )

        # 1. Resolve destination coordinates
        dest_lat, dest_lon = await self._resolve_destination_coordinates(request.destination, db)

        # 2. Retrieve weather conditions for the destination
        weather_context = await self._fetch_weather_context(dest_lat, dest_lon)

        # 3. Retrieve POI candidates (Geoapify + local DB enrichment)
        candidates = await self._retrieve_candidates(
            dest_lat=dest_lat,
            dest_lon=dest_lon,
            max_radius_km=request.max_distance_km or 35.0,
            db=db,
            destination_name=request.destination,
        )

        if not candidates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No points of interest could be discovered for destination '{request.destination}'.",
            )

        # 4. Resolve origin coordinates for distance calculation
        origin_lat = request.origin_latitude if request.origin_latitude is not None else dest_lat
        origin_lon = request.origin_longitude if request.origin_longitude is not None else dest_lon

        # 5. Resolve scoring weights
        scoring_weights = (
            request.weights.to_scoring_weights()
            if request.weights
            else ScoringWeights().normalized()
        )

        # 6. Score and filter candidates
        scored_candidates: List[Dict[str, Any]] = []
        filtered_out_count = 0

        for cand in candidates:
            lat = cand["latitude"]
            lon = cand["longitude"]

            # Distance calculation
            distance_km = ors_service.haversine_distance_km(origin_lat, origin_lon, lat, lon)
            cand["distance_km"] = round(distance_km, 2)

            # Hard constraint: exclude places outside max distance limit
            if request.max_distance_km and distance_km > request.max_distance_km:
                filtered_out_count += 1
                continue

            # Check opening hours constraint if available
            opening_hours = cand.get("opening_hours")
            if opening_hours and any(w in opening_hours.lower() for w in ["permanently closed"]):
                filtered_out_count += 1
                continue

            # Individual factor score calculations
            p_score = calculate_preference_score(
                user_interests=request.interests,
                place_categories=cand.get("categories", []),
                place_name=cand.get("name", ""),
                place_description=cand.get("description", ""),
            )

            d_score = calculate_distance_score(
                distance_km=distance_km,
                max_radius_km=request.max_distance_km or 35.0,
            )

            t_score = calculate_time_score(
                visit_duration_mins=cand.get("estimated_duration_mins"),
                daily_available_hours=request.daily_touring_hours,
                opening_hours=opening_hours,
            )

            w_score = calculate_weather_score(
                weather_code=weather_context.get("weather_code") if weather_context else None,
                precipitation_mm=weather_context.get("precipitation_mm") if weather_context else None,
                place_categories=cand.get("categories", []),
                max_temp_celsius=weather_context.get("temperature_celsius") if weather_context else None,
            )

            b_score = calculate_budget_score(
                entrance_fee=cand.get("entrance_fee"),
                user_budget=request.budget,
                total_trip_days=request.available_duration_days,
            )

            c_score = calculate_category_score(
                place_categories=cand.get("categories", []),
                target_categories=request.interests,
            )

            factor_scores_dict = {
                "preference": p_score,
                "distance": d_score,
                "time": t_score,
                "weather": w_score,
                "category": c_score,
                "budget": b_score,
            }

            final_score = calculate_final_score(factor_scores_dict, scoring_weights)
            baseline_score = calculate_baseline_score(p_score)

            # Flags for constraint warnings (do not silently discard)
            flags: List[str] = []
            entrance_fee = cand.get("entrance_fee")
            if (
                entrance_fee is not None
                and request.budget is not None
                and entrance_fee > (request.budget / max(request.available_duration_days, 1))
            ):
                flags.append("exceeds_daily_budget_guideline")

            visit_mins = cand.get("estimated_duration_mins")
            if visit_mins and visit_mins > (request.daily_touring_hours * 60.0):
                flags.append("exceeds_single_day_available_hours")

            # Explanation generation
            explanation = generate_recommendation_explanation(
                place_name=cand["name"],
                factor_scores=factor_scores_dict,
                user_interests=request.interests,
            )

            cand_result = {
                "place_id": cand["place_id"],
                "name": cand["name"],
                "category": cand.get("category", "tourism"),
                "categories": cand.get("categories", []),
                "latitude": lat,
                "longitude": lon,
                "address": cand.get("address"),
                "distance_km": cand["distance_km"],
                "estimated_duration_mins": cand.get("estimated_duration_mins"),
                "entrance_fee": cand.get("entrance_fee"),
                "factor_scores": factor_scores_dict,
                "final_score": final_score,
                "baseline_preference_score": baseline_score,
                "explanation": explanation,
                "flags": flags,
            }
            scored_candidates.append(cand_result)

        if not scored_candidates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"All discovered places were outside distance/hard constraints ({filtered_out_count} excluded).",
            )

        # 7. Multi-tier ranking
        ranked_list = rank_recommendations(scored_candidates)

        # 8. Baseline comparison analytics
        baseline_comparison = self._calculate_baseline_comparison(ranked_list)

        # 9. Format response POIs with verified location-specific images
        top_recommendations = ranked_list[: request.limit]
        
        # Batch-resolve verified images with duplicate prevention
        batch_inputs = [
            {"name": item["name"], "city": request.destination, "id": item["place_id"]}
            for item in top_recommendations
        ]
        image_metadata_list = await image_service.get_attraction_images_batch(batch_inputs, db=db)
        image_map = {
            item["place_id"]: img_meta
            for item, img_meta in zip(top_recommendations, image_metadata_list)
        }

        formatted_pois: List[RecommendedPOI] = []
        for item in top_recommendations:
            fs = item["factor_scores"]
            img_data = image_map.get(item["place_id"], {})
            formatted_pois.append(
                RecommendedPOI(
                    place_id=item["place_id"],
                    name=item["name"],
                    category=item["category"],
                    categories=item["categories"],
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    address=item["address"],
                    distance_km=item["distance_km"],
                    estimated_duration_mins=item["estimated_duration_mins"],
                    entrance_fee=item["entrance_fee"],
                    factor_scores=FactorScores(
                        preference=fs["preference"],
                        distance=fs["distance"],
                        time=fs["time"],
                        weather=fs["weather"],
                        category=fs["category"],
                        budget=fs["budget"],
                    ),
                    final_score=item["final_score"],
                    baseline_preference_score=item["baseline_preference_score"],
                    rank=item["rank"],
                    explanation=item["explanation"],
                    flags=item["flags"],
                    image_url=img_data.get("image_url"),
                    image_attribution=img_data.get("image_attribution"),
                    image_source=img_data.get("image_source"),
                )
            )

        return RecommendationResponse(
            destination=request.destination,
            destination_coordinates={"latitude": dest_lat, "longitude": dest_lon},
            total_candidates_analyzed=len(candidates),
            total_recommended=len(formatted_pois),
            weights_applied=scoring_weights.to_dict(),
            weather_context=weather_context,
            recommendations=formatted_pois,
            baseline_comparison=baseline_comparison,
        )

    async def _resolve_destination_coordinates(
        self,
        destination_name: str,
        db: Optional[Session] = None,
    ) -> Tuple[float, float]:
        """Geocode destination city name or fallback to database."""
        try:
            results, _ = await geoapify_service.search_destinations(destination_name, limit=1)
            if results:
                return results[0].latitude, results[0].longitude
        except Exception as e:
            logger.warning(f"Geocoding lookup failed for '{destination_name}': {e}")

        # Fallback to local database
        if db:
            dest_record = (
                db.query(Destination)
                .filter(Destination.name.ilike(f"%{destination_name.strip()}%"))
                .first()
            )
            if dest_record and dest_record.latitude and dest_record.longitude:
                return dest_record.latitude, dest_record.longitude

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not resolve geographic coordinates for destination '{destination_name}'.",
        )

    async def _fetch_weather_context(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[Dict[str, Any]]:
        """Fetch current weather summary for scoring."""
        try:
            forecast = await weather_service.get_forecast(latitude, longitude)
            if forecast and forecast.current:
                precip = 0.0
                if forecast.daily:
                    precip = forecast.daily[0].precipitation_mm
                return {
                    "temperature_celsius": forecast.current.temperature_celsius,
                    "condition": forecast.current.condition,
                    "weather_code": forecast.current.weather_code,
                    "wind_speed_kmh": forecast.current.wind_speed_kmh,
                    "precipitation_mm": precip,
                }
        except Exception as e:
            logger.warning(f"Weather context fetch failed: {e}. Scoring will use neutral weather default.")
        return None

    async def _retrieve_candidates(
        self,
        dest_lat: float,
        dest_lon: float,
        max_radius_km: float,
        db: Optional[Session] = None,
        destination_name: str = "",
    ) -> List[Dict[str, Any]]:
        """Discover candidate POIs around the destination using Geoapify and DB."""
        radius_meters = int(min(max(max_radius_km * 1000, 3000), 45000))

        candidates: List[Dict[str, Any]] = []
        seen_names = set()

        # 1. Geoapify Attractions, Sights, and Food
        categories = (
            "tourism.attraction,tourism.sights,entertainment.museum,heritage,"
            "catering.restaurant,catering.cafe,leisure.park"
        )
        try:
            places, _ = await geoapify_service.search_places(
                latitude=dest_lat,
                longitude=dest_lon,
                radius_meters=radius_meters,
                categories=categories,
                limit=30,
            )
            for p in places:
                name_clean = p.name.strip().lower()
                if name_clean not in seen_names:
                    seen_names.add(name_clean)
                    candidates.append({
                        "place_id": p.place_id,
                        "name": p.name,
                        "category": p.category,
                        "categories": p.categories,
                        "latitude": p.latitude,
                        "longitude": p.longitude,
                        "address": p.address,
                        "opening_hours": p.opening_hours,
                        "description": p.description,
                        "estimated_duration_mins": None,  # Not invented
                        "entrance_fee": None,            # Not invented
                    })
        except Exception as e:
            logger.error(f"Geoapify candidate retrieval failed: {e}")

        # 2. Local Database POIs enrichment
        if db:
            db_places = (
                db.query(Place)
                .join(Destination)
                .filter(Destination.name.ilike(f"%{destination_name.strip()}%"))
                .all()
            )
            for dp in db_places:
                name_clean = dp.name.strip().lower()
                if name_clean not in seen_names:
                    seen_names.add(name_clean)
                    candidates.append({
                        "place_id": f"db_{dp.id}",
                        "name": dp.name,
                        "category": dp.category or "tourism",
                        "categories": [dp.category] if dp.category else ["tourism"],
                        "latitude": dp.latitude or dest_lat,
                        "longitude": dp.longitude or dest_lon,
                        "address": dp.address,
                        "opening_hours": dp.opening_hours,
                        "description": dp.description,
                        "estimated_duration_mins": dp.estimated_visit_duration,
                        "entrance_fee": dp.entrance_fee,
                    })

        return candidates

    def _calculate_baseline_comparison(
        self,
        context_ranked_list: List[Dict[str, Any]],
    ) -> BaselineComparison:
        """Measure performance and rank displacement between context-aware and baseline scoring."""
        if not context_ranked_list:
            return BaselineComparison(
                average_context_score=0.0,
                average_baseline_score=0.0,
                rank_displacements=0,
                summary="No candidates available for baseline comparison.",
            )

        # Baseline list sorted purely by preference score
        baseline_sorted = sorted(
            context_ranked_list,
            key=lambda x: x["baseline_preference_score"],
            reverse=True,
        )

        baseline_rank_map = {item["place_id"]: idx + 1 for idx, item in enumerate(baseline_sorted)}

        displacements = 0
        total_context_score = 0.0
        total_baseline_score = 0.0

        for item in context_ranked_list:
            c_rank = item["rank"]
            b_rank = baseline_rank_map.get(item["place_id"], c_rank)
            if c_rank != b_rank:
                displacements += 1
            total_context_score += item["final_score"]
            total_baseline_score += item["baseline_preference_score"]

        n = len(context_ranked_list)
        avg_context = round(total_context_score / n, 4)
        avg_baseline = round(total_baseline_score / n, 4)

        summary = (
            f"Multi-criteria context-aware scoring adjusted {displacements} of {n} place rankings "
            f"relative to the pure preference baseline by incorporating real-time weather, "
            f"distance feasibility, budget, and time availability."
        )

        return BaselineComparison(
            average_context_score=avg_context,
            average_baseline_score=avg_baseline,
            rank_displacements=displacements,
            summary=summary,
        )


recommendation_service = RecommendationService()

