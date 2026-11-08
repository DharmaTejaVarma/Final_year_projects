import math
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.algorithms.budget_calculator import calculate_itinerary_budget
    from app.algorithms.itinerary_optimizer import calculate_itinerary_utility
    from app.algorithms.itinerary_validator import (
        parse_opening_hours_window,
        validate_itinerary_plan,
    )
    from app.algorithms.route_optimizer import (
        calculate_leg_road_metrics,
        compute_distance_matrix,
        minutes_to_time_str,
        nearest_neighbor_tour,
        time_str_to_minutes,
        two_opt_local_search,
    )
    from app.algorithms.weather_adjustment import (
        adjust_attraction_weather,
        evaluate_daily_weather_favorability,
        is_outdoor_venue,
    )
    from app.core.logger import logger
    from app.models.destination import Destination, Place
    from app.models.trip import Itinerary, ItineraryDay, ItineraryPlace, Trip
    from app.schemas.external import Coordinate
    from app.schemas.itinerary import (
        BudgetCalculationResult,
        DailyWeatherSummary,
        ItineraryDayPlan,
        ItineraryGenerateRequest,
        ItineraryResponse,
        ItineraryStop,
        ItineraryValidateRequest,
        ItineraryValidationResponse,
        MealBreak,
        POIScheduleInput,
    )
    from app.schemas.recommendation import RecommendationRequest
    from app.services.recommendation_service import recommendation_service
    from app.services.weather_service import weather_service
except ImportError:
    from backend.app.algorithms.budget_calculator import calculate_itinerary_budget
    from backend.app.algorithms.itinerary_optimizer import calculate_itinerary_utility
    from backend.app.algorithms.itinerary_validator import (
        parse_opening_hours_window,
        validate_itinerary_plan,
    )
    from backend.app.algorithms.route_optimizer import (
        calculate_leg_road_metrics,
        compute_distance_matrix,
        minutes_to_time_str,
        nearest_neighbor_tour,
        time_str_to_minutes,
        two_opt_local_search,
    )
    from backend.app.algorithms.weather_adjustment import (
        adjust_attraction_weather,
        evaluate_daily_weather_favorability,
        is_outdoor_venue,
    )
    from backend.app.core.logger import logger
    from backend.app.models.destination import Destination, Place
    from backend.app.models.trip import Itinerary, ItineraryDay, ItineraryPlace, Trip
    from backend.app.schemas.external import Coordinate
    from backend.app.schemas.itinerary import (
        BudgetCalculationResult,
        DailyWeatherSummary,
        ItineraryDayPlan,
        ItineraryGenerateRequest,
        ItineraryResponse,
        ItineraryStop,
        ItineraryValidateRequest,
        ItineraryValidationResponse,
        MealBreak,
        POIScheduleInput,
    )
    from backend.app.schemas.recommendation import RecommendationRequest
    from backend.app.services.recommendation_service import recommendation_service
    from backend.app.services.weather_service import weather_service

# Global in-memory cache for fast retrieval of generated itineraries
ITINERARY_CACHE: Dict[str, ItineraryResponse] = {}


class ItineraryService:
    """Service orchestrating multi-day itinerary generation, weather adjustments, constraint checking, and budget calculations."""

    @staticmethod
    def _parse_dates(start_date_str: str, end_date_str: str) -> Tuple[datetime.date, datetime.date, int]:
        """Validate and parse date strings into dates and total days."""
        try:
            s_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            e_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid date format: {e}. Expected YYYY-MM-DD.",
            )

        if e_date < s_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid date range: start_date ({start_date_str}) is after end_date ({end_date_str}).",
            )

        total_days = (e_date - s_date).days + 1
        if total_days > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum itinerary generation limit is 30 days.",
            )

        return s_date, e_date, total_days

    async def _resolve_candidate_attractions(
        self,
        request: ItineraryGenerateRequest,
        total_days: int,
        db: Optional[Session] = None,
    ) -> List[POIScheduleInput]:
        """Obtain attraction candidates either from request or by invoking the Phase 4 recommendation engine."""
        if request.attractions and len(request.attractions) > 0:
            return request.attractions

        # Determine target count based on pace and days
        pace_multiplier = {"relaxed": 2, "moderate": 3, "packed": 5}.get(request.pace, 3)
        target_limit = min(25, max(4, total_days * pace_multiplier))

        # Query recommendation engine
        rec_req = RecommendationRequest(
            destination=request.destination,
            interests=request.interests or ["Historical Places", "Sightseeing", "Culture"],
            budget=request.budget,
            available_duration_days=total_days,
            transportation=request.transportation,
            daily_touring_hours=request.daily_available_hours,
            limit=target_limit,
        )

        try:
            rec_res = await recommendation_service.get_recommendations(rec_req, db=db)
            pois: List[POIScheduleInput] = []
            for rec in rec_res.recommendations:
                lat = getattr(rec, "latitude", None)
                if lat is None and hasattr(rec, "coordinates"):
                    lat = getattr(rec.coordinates, "latitude", 0.0)
                lon = getattr(rec, "longitude", None)
                if lon is None and hasattr(rec, "coordinates"):
                    lon = getattr(rec.coordinates, "longitude", 0.0)
                dur = getattr(rec, "estimated_duration_mins", None) or getattr(rec, "estimated_visit_duration", 60)
                hours = getattr(rec, "opening_hours", None)

                pois.append(
                    POIScheduleInput(
                        id=rec.place_id,
                        name=rec.name,
                        latitude=lat or 0.0,
                        longitude=lon or 0.0,
                        category=rec.category,
                        address=rec.address,
                        visit_duration_mins=dur,
                        opening_hours=hours,
                        is_opening_hours_verified=bool(hours and hours != "Unknown"),
                        entrance_fee=rec.entrance_fee,
                        is_fee_verified=rec.entrance_fee is not None,
                        recommendation_score=rec.final_score,
                        is_outdoor=is_outdoor_venue(rec.category, rec.name),
                        image_url=getattr(rec, "image_url", None),
                        image_attribution=getattr(rec, "image_attribution", None),
                    )
                )
            return pois
        except Exception as e:
            logger.warning(f"Automatic recommendation retrieval fallback: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not discover attractions for '{request.destination}'. Please provide specific attractions.",
            )

    async def _fetch_itinerary_weather(
        self,
        lat: float,
        lon: float,
        start_date: datetime.date,
        total_days: int,
    ) -> Dict[str, DailyWeatherSummary]:
        """Fetch forecast and map DailyWeatherSummary by date string."""
        weather_map: Dict[str, DailyWeatherSummary] = {}
        end_date = start_date + timedelta(days=total_days - 1)

        try:
            forecast_res = await weather_service.get_forecast(
                latitude=lat,
                longitude=lon,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )
            for daily in forecast_res.daily_forecasts:
                f_date = daily.date
                precip = daily.precipitation_sum_mm or 0.0
                is_favorable, _, summary = evaluate_daily_weather_favorability(
                    {
                        "precipitation_mm": precip,
                        "weather_code": daily.weather_code,
                        "wind_speed_kmh": daily.wind_speed_max_kmh,
                        "temperature_celsius": daily.temperature_max_celsius,
                    }
                )
                weather_map[f_date] = DailyWeatherSummary(
                    date=f_date,
                    temperature_celsius=daily.temperature_max_celsius,
                    condition=daily.condition,
                    weather_code=daily.weather_code,
                    precipitation_mm=precip,
                    wind_speed_kmh=daily.wind_speed_max_kmh,
                    is_outdoor_favorable=is_favorable,
                    suitability_summary=summary,
                )
        except Exception as e:
            logger.warning(f"Weather retrieval fallback for itinerary: {e}")

        # Fill in any missing dates with benign default
        for i in range(total_days):
            d_str = (start_date + timedelta(days=i)).isoformat()
            if d_str not in weather_map:
                weather_map[d_str] = DailyWeatherSummary(
                    date=d_str,
                    temperature_celsius=25.0,
                    condition="Mainly clear",
                    weather_code=1,
                    precipitation_mm=0.0,
                    wind_speed_kmh=10.0,
                    is_outdoor_favorable=True,
                    suitability_summary="Favorable weather conditions expected.",
                )

        return weather_map

    async def generate_itinerary(
        self,
        request: ItineraryGenerateRequest,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
    ) -> ItineraryResponse:
        """Generate a personalized, constraint-checked multi-day travel itinerary."""
        start_date, end_date, total_days = self._parse_dates(request.start_date, request.end_date)

        # 1. Resolve candidates
        attractions = await self._resolve_candidate_attractions(request, total_days, db=db)
        if not attractions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one point of interest is required to generate an itinerary.",
            )

        ref_lat = attractions[0].latitude
        ref_lon = attractions[0].longitude

        # 2. Retrieve weather forecast
        weather_by_date = await self._fetch_itinerary_weather(ref_lat, ref_lon, start_date, total_days)

        # 3. Identify indoor venues for alternatives
        indoor_alternatives = [
            a.name for a in attractions if not is_outdoor_venue(a.category, a.name, a.is_outdoor)
        ]

        # 4. Partition attractions across days
        # Sort or group attractions into days
        max_daily_pois = {"relaxed": 3, "moderate": 4, "packed": 6}.get(request.pace, 4)
        daily_buckets: List[List[POIScheduleInput]] = [[] for _ in range(total_days)]

        # Distribute attractions sequentially or geographically
        for i, poi in enumerate(attractions):
            day_idx = min(i // max_daily_pois, total_days - 1)
            daily_buckets[day_idx].append(poi)

        # Ensure no day is left completely empty if attractions exist
        non_empty_buckets = [b for b in daily_buckets if len(b) > 0]
        if len(non_empty_buckets) < total_days and len(attractions) >= total_days:
            # Rebalance evenly
            daily_buckets = [[] for _ in range(total_days)]
            for i, poi in enumerate(attractions):
                daily_buckets[i % total_days].append(poi)

        # 5. Build detailed schedule for each day
        day_plans: List[ItineraryDayPlan] = []
        all_stops_flat: List[Dict[str, Any]] = []

        total_trip_dist_km = 0.0
        total_trip_travel_mins = 0.0
        total_trip_visit_mins = 0.0

        for day_num in range(1, total_days + 1):
            curr_date = start_date + timedelta(days=day_num - 1)
            curr_date_str = curr_date.isoformat()
            day_weather = weather_by_date[curr_date_str]
            day_pois = daily_buckets[day_num - 1]

            # If no attractions allocated to this day (e.g. relaxed rest day)
            if not day_pois:
                day_plans.append(
                    ItineraryDayPlan(
                        day_number=day_num,
                        date=curr_date_str,
                        theme="Leisure & Exploration Day",
                        weather=day_weather,
                        stops=[],
                        meal_breaks=[],
                        daily_distance_km=0.0,
                        daily_travel_time_mins=0.0,
                        daily_visit_time_mins=0.0,
                        daily_total_duration_mins=0.0,
                        daily_estimated_cost=0.0,
                        stops_count=0,
                        warnings=["No fixed attractions scheduled; leisure and personal exploration."],
                        geometry=[],
                    )
                )
                continue

            # Intra-day Route Optimization (2-Opt)
            day_coords = [(p.latitude, p.longitude) for p in day_pois]
            matrix = compute_distance_matrix(day_coords, transportation=request.transportation)
            nn_tour = nearest_neighbor_tour(matrix, start_idx=0)
            opt_tour, _ = two_opt_local_search(nn_tour, matrix, fixed_start=False, fixed_end=False)
            ordered_day_pois = [day_pois[idx] for idx in opt_tour]

            # Assemble chronological stops with time tracking
            clock_mins = time_str_to_minutes(request.start_time)
            curr_lat: Optional[float] = None
            curr_lon: Optional[float] = None

            day_stops: List[ItineraryStop] = []
            day_meals: List[MealBreak] = []
            day_warnings: List[str] = []

            # Optional start location
            if request.start_location:
                sl = request.start_location
                curr_lat = sl.latitude
                curr_lon = sl.longitude
                day_stops.append(
                    ItineraryStop(
                        stop_order=1,
                        place_id=sl.id,
                        name=sl.name,
                        latitude=sl.latitude,
                        longitude=sl.longitude,
                        category=sl.category or "Hotel / Starting Point",
                        arrival_time=minutes_to_time_str(clock_mins),
                        departure_time=minutes_to_time_str(clock_mins),
                        visit_duration_mins=0,
                        travel_duration_mins=0.0,
                        travel_distance_km=0.0,
                        entrance_fee_per_person=0.0,
                        total_entrance_fee=0.0,
                        fee_status="free",
                        is_start_location=True,
                    )
                )

            lunch_scheduled = False

            for poi in ordered_day_pois:
                # Travel from current location
                if curr_lat is not None and curr_lon is not None:
                    leg_dist, leg_dur = calculate_leg_road_metrics(
                        curr_lat, curr_lon, poi.latitude, poi.longitude, request.transportation
                    )
                else:
                    leg_dist, leg_dur = 0.0, 0.0

                clock_mins += int(round(leg_dur))

                # Midday Lunch Break: Schedule if clock reaches >= 12:30 and no lunch yet
                if clock_mins >= 750 and not lunch_scheduled:
                    lunch_start = minutes_to_time_str(clock_mins)
                    clock_mins += 60  # 60 min lunch
                    lunch_end = minutes_to_time_str(clock_mins)
                    day_meals.append(
                        MealBreak(
                            meal_type="lunch",
                            name=f"Lunch Break near {poi.name}",
                            scheduled_start=lunch_start,
                            scheduled_end=lunch_end,
                            duration_mins=60,
                            estimated_cost_per_person=350.0,
                        )
                    )
                    lunch_scheduled = True

                arrival_time_str = minutes_to_time_str(clock_mins)
                visit_duration = poi.visit_duration_mins
                clock_mins += visit_duration
                departure_time_str = minutes_to_time_str(clock_mins)

                curr_lat = poi.latitude
                curr_lon = poi.longitude

                # Weather adjustment
                is_outdoor = is_outdoor_venue(poi.category, poi.name, poi.is_outdoor)
                w_score, w_warn, indoor_alt = adjust_attraction_weather(
                    poi_name=poi.name,
                    category=poi.category,
                    is_outdoor=is_outdoor,
                    weather_data={
                        "precipitation_mm": day_weather.precipitation_mm,
                        "weather_code": day_weather.weather_code,
                        "wind_speed_kmh": day_weather.wind_speed_kmh,
                        "temperature_celsius": day_weather.temperature_celsius,
                    },
                    available_indoor_alternatives=[alt for alt in indoor_alternatives if alt != poi.name],
                )
                if w_warn:
                    day_warnings.append(w_warn)

                # Opening hours verification
                oh_status = "unknown"
                oh_warning: Optional[str] = None
                if poi.opening_hours:
                    w_interval = parse_opening_hours_window(poi.opening_hours)
                    if w_interval:
                        op_m, cl_m = w_interval
                        arr_m = time_str_to_minutes(arrival_time_str)
                        dep_m = time_str_to_minutes(departure_time_str)
                        if arr_m < op_m or dep_m > cl_m:
                            oh_status = "conflict"
                            oh_warning = f"Visit ({arrival_time_str}-{departure_time_str}) falls outside verified hours ({poi.opening_hours})."
                            day_warnings.append(f"Opening hours conflict at '{poi.name}': {oh_warning}")
                        else:
                            oh_status = "verified"
                else:
                    oh_warning = f"Opening hours unverified for '{poi.name}'. Please confirm locally."
                    day_warnings.append(oh_warning)

                # Pricing provenance
                if poi.entrance_fee is not None:
                    fee_per_person = float(poi.entrance_fee)
                    fee_status = "verified" if poi.is_fee_verified else "user_provided"
                else:
                    fee_per_person = 150.0
                    fee_status = "unknown_estimated"

                stop_obj = ItineraryStop(
                    stop_order=len(day_stops) + 1,
                    place_id=poi.id,
                    name=poi.name,
                    latitude=poi.latitude,
                    longitude=poi.longitude,
                    category=poi.category,
                    arrival_time=arrival_time_str,
                    departure_time=departure_time_str,
                    visit_duration_mins=visit_duration,
                    travel_duration_mins=leg_dur,
                    travel_distance_km=leg_dist,
                    opening_hours=poi.opening_hours,
                    opening_hours_status=oh_status,
                    opening_hours_warning=oh_warning,
                    entrance_fee_per_person=fee_per_person,
                    total_entrance_fee=fee_per_person * request.travelers_count,
                    fee_status=fee_status,
                    weather_suitability_score=w_score,
                    weather_warning=w_warn,
                    indoor_alternative_suggested=indoor_alt,
                    is_outdoor=is_outdoor,
                    image_url=getattr(poi, "image_url", None),
                    image_attribution=getattr(poi, "image_attribution", None),
                )
                day_stops.append(stop_obj)

                all_stops_flat.append(
                    {
                        "name": poi.name,
                        "entrance_fee": poi.entrance_fee,
                        "is_fee_verified": poi.is_fee_verified,
                        "is_user_provided": bool(poi.entrance_fee is not None and not poi.is_fee_verified),
                    }
                )

            # Optional end location
            if request.end_location and curr_lat is not None and curr_lon is not None:
                el = request.end_location
                end_dist, end_dur = calculate_leg_road_metrics(
                    curr_lat, curr_lon, el.latitude, el.longitude, request.transportation
                )
                clock_mins += int(round(end_dur))
                day_stops.append(
                    ItineraryStop(
                        stop_order=len(day_stops) + 1,
                        place_id=el.id,
                        name=el.name,
                        latitude=el.latitude,
                        longitude=el.longitude,
                        category=el.category or "Hotel / Ending Destination",
                        arrival_time=minutes_to_time_str(clock_mins),
                        departure_time=minutes_to_time_str(clock_mins),
                        visit_duration_mins=0,
                        travel_duration_mins=end_dur,
                        travel_distance_km=end_dist,
                        entrance_fee_per_person=0.0,
                        total_entrance_fee=0.0,
                        fee_status="free",
                        is_end_location=True,
                    )
                )

            # Daily totals
            day_dist = round(sum(s.travel_distance_km for s in day_stops), 2)
            day_travel = round(sum(s.travel_duration_mins for s in day_stops), 1)
            day_visit = round(sum(s.visit_duration_mins for s in day_stops), 1)
            day_meals_mins = sum(m.duration_mins for m in day_meals)
            day_duration = round(day_travel + day_visit + day_meals_mins, 1)

            total_trip_dist_km += day_dist
            total_trip_travel_mins += day_travel
            total_trip_visit_mins += day_visit

            # Check daily duration constraint
            max_daily_mins = int(request.daily_available_hours * 60.0)
            if day_duration > max_daily_mins:
                day_warnings.append(
                    f"Day schedule ({day_duration:.0f} mins) exceeds daily limit of {max_daily_mins} mins ({request.daily_available_hours}h)."
                )

            # Daily geometry
            geom = [[s.latitude, s.longitude] for s in day_stops]

            day_plan = ItineraryDayPlan(
                day_number=day_num,
                date=curr_date_str,
                theme=f"Day {day_num}: {ordered_day_pois[0].name} & Cultural Highlights",
                weather=day_weather,
                stops=day_stops,
                meal_breaks=day_meals,
                daily_distance_km=day_dist,
                daily_travel_time_mins=day_travel,
                daily_visit_time_mins=day_visit,
                daily_total_duration_mins=day_duration,
                daily_estimated_cost=round(sum(s.total_entrance_fee for s in day_stops), 2),
                stops_count=len([s for s in day_stops if not s.is_start_location and not s.is_end_location]),
                warnings=day_warnings,
                geometry=geom,
            )
            day_plans.append(day_plan)

        # 6. Budget Calculation
        budget_result = calculate_itinerary_budget(
            total_budget=request.budget,
            travelers_count=request.travelers_count,
            total_days=total_days,
            total_distance_km=total_trip_dist_km,
            transportation=request.transportation,
            stops_data=all_stops_flat,
            include_accommodation=request.include_accommodation,
            accommodation_type=request.accommodation_type or "standard",
            dietary_budget_tier=request.dietary_budget_tier or "moderate",
        )

        # 7. Constraint Validation
        validation = validate_itinerary_plan(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            budget=request.budget,
            daily_available_hours=request.daily_available_hours,
            days=day_plans,
            total_cost=budget_result.estimated_total_cost,
        )

        # 8. Multi-Criteria Utility Optimization Evaluation U(I)
        utility = calculate_itinerary_utility(
            days=day_plans,
            budget_result=budget_result,
            daily_available_hours=request.daily_available_hours,
        )

        # 9. Assembly & Persistence
        itinerary_id = f"itin_{uuid.uuid4().hex[:12]}"
        feasibility_status = "feasible" if validation.is_valid and not validation.warnings else "feasible_with_warnings"

        response = ItineraryResponse(
            itinerary_id=itinerary_id,
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            total_days=total_days,
            travelers_count=request.travelers_count,
            transportation=request.transportation,
            pace=request.pace,
            total_attractions_scheduled=len(all_stops_flat),
            total_distance_km=round(total_trip_dist_km, 2),
            total_travel_time_mins=round(total_trip_travel_mins, 1),
            total_visit_time_mins=round(total_trip_visit_mins, 1),
            budget_summary=budget_result,
            utility=utility,
            days=day_plans,
            feasibility_status=feasibility_status,
            unresolved_constraints=validation.errors,
            general_notes=budget_result.budget_notes + validation.warnings,
        )

        # Store in cache
        ITINERARY_CACHE[itinerary_id] = response

        # Store in SQLite database if user is authenticated
        if db is not None:
            try:
                dest_rec = db.query(Destination).filter(Destination.name.ilike(f"%{request.destination}%")).first()
                if not dest_rec:
                    dest_rec = Destination(
                        name=request.destination,
                        country="India",
                        latitude=ref_lat,
                        longitude=ref_lon,
                    )
                    db.add(dest_rec)
                    db.flush()

                # If user_id provided or guest
                actual_user_id = user_id if user_id else 1
                trip = Trip(
                    user_id=actual_user_id,
                    destination_id=dest_rec.id,
                    start_date=start_date,
                    end_date=end_date,
                    budget=request.budget,
                    travelers_count=request.travelers_count,
                    transportation=request.transportation,
                    status="planned",
                )
                db.add(trip)
                db.flush()

                itin_rec = Itinerary(
                    trip_id=trip.id,
                    title=f"{total_days}-Day Trip to {request.destination}",
                    total_estimated_cost=budget_result.estimated_total_cost,
                    total_distance=total_trip_dist_km,
                    total_duration=round(total_trip_travel_mins + total_trip_visit_mins, 1) / 60.0,
                )
                db.add(itin_rec)
                db.flush()

                response.trip_id = trip.id
                db.commit()
            except Exception as dbe:
                db.rollback()
                logger.warning(f"Database persistence skipped for itinerary {itinerary_id}: {dbe}")

        return response

    @staticmethod
    def get_itinerary(itinerary_id: str) -> Optional[ItineraryResponse]:
        """Retrieve previously generated itinerary by its identifier."""
        return ITINERARY_CACHE.get(itinerary_id)

    @staticmethod
    def validate_existing_itinerary(
        request: ItineraryValidateRequest,
    ) -> ItineraryValidationResponse:
        """Validate feasibility of an existing or proposed itinerary."""
        total_cost = sum(d.daily_estimated_cost for d in request.days)
        return validate_itinerary_plan(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            budget=request.budget,
            daily_available_hours=request.daily_available_hours,
            days=request.days,
            total_cost=total_cost,
        )


itinerary_service = ItineraryService()

