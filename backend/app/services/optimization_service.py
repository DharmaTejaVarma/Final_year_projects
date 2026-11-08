from typing import List, Optional, Tuple
from copy import deepcopy

try:
    from app.algorithms.route_optimizer import (
        compute_distance_matrix,
        nearest_neighbor_tour,
        two_opt_local_search,
        calculate_tour_distance,
        partition_daily_routes,
        calculate_leg_road_metrics,
        PROFILE_SPECS,
    )
    from app.core.config import settings
    from app.core.logger import logger
    from app.schemas.clustering_and_routing import (
        RouteOptimizationRequest,
        RouteOptimizationResponse,
        RouteComparison,
        POIInput,
        DailyRoute,
    )
    from app.services.ors_service import ors_service
except ImportError:
    from backend.app.algorithms.route_optimizer import (
        compute_distance_matrix,
        nearest_neighbor_tour,
        two_opt_local_search,
        calculate_tour_distance,
        partition_daily_routes,
        calculate_leg_road_metrics,
        PROFILE_SPECS,
    )
    from backend.app.core.config import settings
    from backend.app.core.logger import logger
    from backend.app.schemas.clustering_and_routing import (
        RouteOptimizationRequest,
        RouteOptimizationResponse,
        RouteComparison,
        POIInput,
        DailyRoute,
    )
    from backend.app.services.ors_service import ors_service


class OptimizationService:
    """Service orchestrating visiting sequence optimization and daily itinerary generation."""

    @staticmethod
    async def optimize_routes(request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        """Optimize route sequence using Nearest-Neighbor initialization and 2-Opt local search."""
        places: List[POIInput] = request.places
        n_places = len(places)
        transportation = request.transportation

        logger.info(
            f"Optimizing route for {n_places} attractions via '{transportation}' mode. "
            f"Daily hours: {request.daily_available_hours}h, start time: {request.start_time}"
        )

        # Assemble full list of waypoints for TSP
        # If start_location is provided, it occupies index 0
        waypoints: List[POIInput] = []
        has_start = request.start_location is not None
        has_end = request.end_location is not None

        if has_start:
            waypoints.append(request.start_location)

        # Attractions
        waypoints.extend(places)

        if has_end:
            waypoints.append(request.end_location)

        total_pts = len(waypoints)
        coords = [(wp.latitude, wp.longitude) for wp in waypoints]

        # Compute road distance matrix
        dist_matrix = compute_distance_matrix(coords, transportation=transportation)

        # Determine initial naive sequence
        naive_tour = list(range(total_pts))
        initial_distance = calculate_tour_distance(naive_tour, dist_matrix)

        # Optimization: Nearest-Neighbor + 2-Opt
        start_idx = 0 if has_start else 0
        fixed_end_idx = (total_pts - 1) if has_end else None

        nn_tour = nearest_neighbor_tour(
            dist_matrix=dist_matrix,
            start_idx=start_idx,
            fixed_end_idx=fixed_end_idx,
        )

        optimized_tour_indices, optimized_distance = two_opt_local_search(
            tour=nn_tour,
            dist_matrix=dist_matrix,
            fixed_start=has_start,
            fixed_end=has_end,
        )

        # If 2-opt didn't beat naive (e.g. user input was already optimal), guard bounds
        if optimized_distance > initial_distance and not has_start and not has_end:
            optimized_tour_indices = naive_tour
            optimized_distance = initial_distance

        # Calculate time metrics for naive vs optimized
        spec = PROFILE_SPECS.get(transportation, PROFILE_SPECS["driving-car"])
        speed_kmh = spec["speed_kmh"]
        initial_travel_time = round((initial_distance / speed_kmh) * 60.0, 1)
        optimized_travel_time = round((optimized_distance / speed_kmh) * 60.0, 1)

        dist_saved = round(max(0.0, initial_distance - optimized_distance), 2)
        time_saved = round(max(0.0, initial_travel_time - optimized_travel_time), 1)

        improvement_pct = (
            round((dist_saved / initial_distance) * 100.0, 2)
            if initial_distance > 0.0
            else 0.0
        )

        comparison = RouteComparison(
            initial_distance_km=initial_distance,
            optimized_distance_km=optimized_distance,
            distance_saved_km=dist_saved,
            improvement_percentage=improvement_pct,
            initial_travel_time_mins=initial_travel_time,
            optimized_travel_time_mins=optimized_travel_time,
            time_saved_mins=time_saved,
            method_used="Nearest-Neighbor Construction + 2-Opt Local Search",
            details=(
                f"Initial sequence traversed {initial_distance} km ({initial_travel_time} mins). "
                f"2-Opt optimization reorganized visiting sequence to {optimized_distance} km "
                f"({optimized_travel_time} mins), reducing road travel by {dist_saved} km ({improvement_pct}% improvement)."
            ),
        )

        # Extract ordered POIs (excluding start_location and end_location wrappers)
        ordered_places: List[POIInput] = []
        for idx in optimized_tour_indices:
            if has_start and idx == 0:
                continue
            if has_end and idx == (total_pts - 1):
                continue
            ordered_places.append(waypoints[idx])

        # Partition into daily routes
        daily_routes = partition_daily_routes(
            ordered_places=ordered_places,
            start_location=request.start_location,
            end_location=request.end_location,
            transportation=transportation,
            daily_available_hours=request.daily_available_hours,
            start_time_str=request.start_time,
            max_days=request.total_days,
        )

        # Aggregate overall itinerary metrics
        total_dist_km = round(sum(d.total_distance_km for d in daily_routes), 2)
        total_travel_mins = round(sum(d.total_travel_time_mins for d in daily_routes), 1)
        total_visit_mins = round(sum(d.total_visit_time_mins for d in daily_routes), 1)

        is_ors_configured = bool(settings.ORS_API_KEY and settings.ORS_API_KEY.strip())
        source = "live" if is_ors_configured else "simulated"
        is_mocked = not is_ors_configured

        summary_note = (
            f"Successfully optimized {n_places} attractions into {len(daily_routes)} day(s) "
            f"via {transportation} mode using 2-Opt TSP optimization. "
            f"Total travel distance: {total_dist_km} km. Total travel time: {total_travel_mins} mins. "
            f"Road circuity factor: {spec['circuity']}x at average {speed_kmh} km/h velocity."
        )

        return RouteOptimizationResponse(
            transportation=transportation,
            total_days=len(daily_routes),
            total_places_visited=n_places,
            total_distance_km=total_dist_km,
            total_travel_time_mins=total_travel_mins,
            total_visit_time_mins=total_visit_mins,
            comparison=comparison,
            daily_routes=daily_routes,
            is_mocked=is_mocked,
            source=source,
            summary_note=summary_note,
        )


optimization_service = OptimizationService()

