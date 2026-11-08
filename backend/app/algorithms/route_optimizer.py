import math
from typing import List, Tuple, Dict, Any, Optional
from copy import deepcopy

try:
    from app.algorithms.geographic_clustering import haversine_distance_km
    from app.schemas.clustering_and_routing import (
        POIInput,
        RouteStop,
        DailyRoute,
        RouteComparison,
    )
except ImportError:
    from backend.app.algorithms.geographic_clustering import haversine_distance_km
    from backend.app.schemas.clustering_and_routing import (
        POIInput,
        RouteStop,
        DailyRoute,
        RouteComparison,
    )

# Transportation profile specifications (speed in km/h, road circuity factor relative to Haversine)
PROFILE_SPECS = {
    "driving-car": {"speed_kmh": 55.0, "circuity": 1.30},
    "foot-walking": {"speed_kmh": 4.8, "circuity": 1.15},
    "cycling-regular": {"speed_kmh": 15.0, "circuity": 1.20},
}


def calculate_leg_road_metrics(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    transportation: str = "driving-car",
) -> Tuple[float, float]:
    """Calculate estimated road distance (km) and travel duration (minutes) using mode-specific circuity factors."""
    spec = PROFILE_SPECS.get(transportation, PROFILE_SPECS["driving-car"])
    straight_km = haversine_distance_km(lat1, lon1, lat2, lon2)
    road_km = round(straight_km * spec["circuity"], 2)
    duration_mins = round((road_km / spec["speed_kmh"]) * 60.0, 1)
    return road_km, duration_mins


def minutes_to_time_str(total_minutes: int) -> str:
    """Convert minutes from midnight to 24-hour HH:MM string format."""
    total_minutes = int(total_minutes) % 1440
    hours = total_minutes // 60
    mins = total_minutes % 60
    return f"{hours:02d}:{mins:02d}"


def time_str_to_minutes(time_str: str) -> int:
    """Convert 24-hour HH:MM string to minutes from midnight."""
    parts = time_str.split(":")
    hours = int(parts[0])
    mins = int(parts[1]) if len(parts) > 1 else 0
    return hours * 60 + mins


def compute_distance_matrix(
    points: List[Tuple[float, float]],
    transportation: str = "driving-car",
) -> List[List[float]]:
    """Compute NxN road distance matrix for a list of coordinates."""
    n = len(points)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dist_km, _ = calculate_leg_road_metrics(
                points[i][0], points[i][1], points[j][0], points[j][1], transportation
            )
            matrix[i][j] = dist_km
            matrix[j][i] = dist_km
    return matrix


def calculate_tour_distance(
    tour: List[int],
    dist_matrix: List[List[float]],
) -> float:
    """Calculate the total distance of a tour given a distance matrix."""
    if len(tour) < 2:
        return 0.0
    total = 0.0
    for i in range(len(tour) - 1):
        total += dist_matrix[tour[i]][tour[i + 1]]
    return round(total, 2)


def nearest_neighbor_tour(
    dist_matrix: List[List[float]],
    start_idx: int = 0,
    fixed_end_idx: Optional[int] = None,
) -> List[int]:
    """Construct an initial TSP visiting sequence using Nearest-Neighbor heuristic.

    Args:
        dist_matrix: NxN distance matrix.
        start_idx: Starting waypoint index (default 0).
        fixed_end_idx: Optional fixed terminal destination index.

    Returns:
        List of vertex indices in visiting order.
    """
    n = len(dist_matrix)
    if n <= 1:
        return list(range(n))

    unvisited = set(range(n))
    unvisited.remove(start_idx)
    if fixed_end_idx is not None and fixed_end_idx in unvisited:
        unvisited.remove(fixed_end_idx)

    tour = [start_idx]
    current = start_idx

    while unvisited:
        next_node = min(unvisited, key=lambda node: dist_matrix[current][node])
        tour.append(next_node)
        unvisited.remove(next_node)
        current = next_node

    if fixed_end_idx is not None and fixed_end_idx != start_idx:
        tour.append(fixed_end_idx)

    return tour


def two_opt_local_search(
    tour: List[int],
    dist_matrix: List[List[float]],
    fixed_start: bool = True,
    fixed_end: bool = False,
    max_iterations: int = 500,
) -> Tuple[List[int], float]:
    """Perform 2-Opt local search to iteratively untangle crossings and shorten tour length.

    Args:
        tour: Initial visiting order.
        dist_matrix: NxN distance matrix.
        fixed_start: If True, index 0 is fixed at the start of the tour.
        fixed_end: If True, the final index is fixed at the end of the tour.
        max_iterations: Safety iteration cap to prevent infinite loops.

    Returns:
        Tuple of (optimized_tour, total_distance).
    """
    m = len(tour)
    if m <= 2:
        return tour, calculate_tour_distance(tour, dist_matrix)

    best_tour = list(tour)
    best_dist = calculate_tour_distance(best_tour, dist_matrix)

    start_i = 1 if fixed_start else 0
    end_j_limit = (m - 1) if fixed_end else m

    iteration = 0
    improved = True

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        for i in range(start_i, m - 1):
            for j in range(i + 1, end_j_limit):
                # Candidate tour with segment between i and j reversed
                candidate_tour = best_tour[:i] + list(reversed(best_tour[i : j + 1])) + best_tour[j + 1 :]
                candidate_dist = calculate_tour_distance(candidate_tour, dist_matrix)

                if candidate_dist < best_dist - 1e-5:
                    best_tour = candidate_tour
                    best_dist = candidate_dist
                    improved = True
                    break
            if improved:
                break

    return best_tour, best_dist


def interpolate_geometry(
    coords: List[Tuple[float, float]],
    steps: int = 4,
) -> List[List[float]]:
    """Generate smooth intermediate coordinate waypoints for route geometry visualization."""
    if len(coords) < 2:
        return [[round(c[0], 6), round(c[1], 6)] for c in coords]

    result: List[List[float]] = []
    for i in range(len(coords) - 1):
        p1 = coords[i]
        p2 = coords[i + 1]
        for step in range(steps):
            t = step / float(steps)
            lat = p1[0] + t * (p2[0] - p1[0])
            lon = p1[1] + t * (p2[1] - p1[1])
            result.append([round(lat, 6), round(lon, 6)])

    final = coords[-1]
    result.append([round(final[0], 6), round(final[1], 6)])
    return result


def partition_daily_routes(
    ordered_places: List[POIInput],
    start_location: Optional[POIInput],
    end_location: Optional[POIInput],
    transportation: str = "driving-car",
    daily_available_hours: float = 8.0,
    start_time_str: str = "09:00",
    max_days: Optional[int] = None,
) -> List[DailyRoute]:
    """Partition ordered attractions into daily itineraries subject to daily time budgets."""
    daily_available_mins = int(daily_available_hours * 60.0)
    day_start_min = time_str_to_minutes(start_time_str)

    daily_routes: List[DailyRoute] = []
    current_day = 1
    current_time_min = day_start_min
    day_stops: List[RouteStop] = []
    day_coords: List[Tuple[float, float]] = []

    current_lat: Optional[float] = None
    current_lon: Optional[float] = None

    # Helper to start a fresh day
    def _begin_new_day(day_num: int):
        nonlocal current_time_min, current_lat, current_lon, day_stops, day_coords
        current_time_min = day_start_min
        day_stops = []
        day_coords = []
        if start_location is not None:
            current_lat = start_location.latitude
            current_lon = start_location.longitude
            day_coords.append((start_location.latitude, start_location.longitude))
            day_stops.append(
                RouteStop(
                    stop_order=1,
                    place_id=start_location.id,
                    name=start_location.name,
                    latitude=start_location.latitude,
                    longitude=start_location.longitude,
                    category=start_location.category or "Starting Point",
                    arrival_time=minutes_to_time_str(current_time_min),
                    departure_time=minutes_to_time_str(current_time_min),
                    visit_duration_mins=0,
                    leg_distance_km=0.0,
                    leg_travel_time_mins=0.0,
                    is_start_location=True,
                    is_end_location=False,
                )
            )
        else:
            current_lat = None
            current_lon = None

    _begin_new_day(current_day)

    for place in ordered_places:
        visit_duration = place.visit_duration_mins

        if current_lat is not None and current_lon is not None:
            leg_dist, leg_dur = calculate_leg_road_metrics(
                current_lat, current_lon, place.latitude, place.longitude, transportation
            )
        else:
            leg_dist = 0.0
            leg_dur = 0.0

        # Check if adding this place exceeds the day's time budget
        projected_elapsed = (current_time_min + leg_dur + visit_duration) - day_start_min

        # If adding this POI exceeds daily time and we already have visited at least 1 POI in this day:
        has_visited_poi = any(not s.is_start_location and not s.is_end_location for s in day_stops)
        can_split_day = max_days is None or current_day < max_days

        if projected_elapsed > daily_available_mins and has_visited_poi and can_split_day:
            # Wrap up previous day (add end location if specified)
            if end_location is not None and current_lat is not None and current_lon is not None:
                end_dist, end_dur = calculate_leg_road_metrics(
                    current_lat, current_lon, end_location.latitude, end_location.longitude, transportation
                )
                current_time_min += int(round(end_dur))
                day_stops.append(
                    RouteStop(
                        stop_order=len(day_stops) + 1,
                        place_id=end_location.id,
                        name=end_location.name,
                        latitude=end_location.latitude,
                        longitude=end_location.longitude,
                        category=end_location.category or "Ending Destination",
                        arrival_time=minutes_to_time_str(current_time_min),
                        departure_time=minutes_to_time_str(current_time_min),
                        visit_duration_mins=0,
                        leg_distance_km=end_dist,
                        leg_travel_time_mins=end_dur,
                        is_start_location=False,
                        is_end_location=True,
                    )
                )
                day_coords.append((end_location.latitude, end_location.longitude))

            # Commit current day
            daily_routes.append(_build_daily_route_summary(current_day, day_stops, day_coords))

            # Start next day
            current_day += 1
            _begin_new_day(current_day)

            # Recalculate leg from new day's start to current place
            if current_lat is not None and current_lon is not None:
                leg_dist, leg_dur = calculate_leg_road_metrics(
                    current_lat, current_lon, place.latitude, place.longitude, transportation
                )
            else:
                leg_dist = 0.0
                leg_dur = 0.0

        # Place the stop into the current day
        arrival_min = current_time_min + int(round(leg_dur))
        departure_min = arrival_min + visit_duration
        current_time_min = departure_min
        current_lat = place.latitude
        current_lon = place.longitude

        day_coords.append((place.latitude, place.longitude))
        day_stops.append(
            RouteStop(
                stop_order=len(day_stops) + 1,
                place_id=place.id,
                name=place.name,
                latitude=place.latitude,
                longitude=place.longitude,
                category=place.category,
                arrival_time=minutes_to_time_str(arrival_min),
                departure_time=minutes_to_time_str(departure_min),
                visit_duration_mins=visit_duration,
                leg_distance_km=leg_dist,
                leg_travel_time_mins=leg_dur,
                is_start_location=False,
                is_end_location=False,
            )
        )

    # Wrap up final day
    if end_location is not None and current_lat is not None and current_lon is not None:
        end_dist, end_dur = calculate_leg_road_metrics(
            current_lat, current_lon, end_location.latitude, end_location.longitude, transportation
        )
        current_time_min += int(round(end_dur))
        day_stops.append(
            RouteStop(
                stop_order=len(day_stops) + 1,
                place_id=end_location.id,
                name=end_location.name,
                latitude=end_location.latitude,
                longitude=end_location.longitude,
                category=end_location.category or "Ending Destination",
                arrival_time=minutes_to_time_str(current_time_min),
                departure_time=minutes_to_time_str(current_time_min),
                visit_duration_mins=0,
                leg_distance_km=end_dist,
                leg_travel_time_mins=end_dur,
                is_start_location=False,
                is_end_location=True,
            )
        )
        day_coords.append((end_location.latitude, end_location.longitude))

    if day_stops:
        daily_routes.append(_build_daily_route_summary(current_day, day_stops, day_coords))

    return daily_routes


def _build_daily_route_summary(
    day_num: int,
    stops: List[RouteStop],
    coords: List[Tuple[float, float]],
) -> DailyRoute:
    """Helper to assemble a DailyRoute object with aggregated metrics."""
    tot_dist = round(sum(s.leg_distance_km for s in stops), 2)
    tot_travel = round(sum(s.leg_travel_time_mins for s in stops), 1)
    tot_visit = round(sum(s.visit_duration_mins for s in stops), 1)
    tot_duration = round(tot_travel + tot_visit, 1)

    geometry = interpolate_geometry(coords)
    poi_count = sum(1 for s in stops if not s.is_start_location and not s.is_end_location)

    summary = (
        f"Day {day_num}: {poi_count} attraction(s) scheduled across {tot_dist} km. "
        f"Travel time: {tot_travel} mins, visit time: {tot_visit} mins (total: {tot_duration} mins)."
    )

    return DailyRoute(
        day_number=day_num,
        stops=stops,
        total_distance_km=tot_dist,
        total_travel_time_mins=tot_travel,
        total_visit_time_mins=tot_visit,
        total_day_duration_mins=tot_duration,
        geometry=geometry,
        summary=summary,
    )
