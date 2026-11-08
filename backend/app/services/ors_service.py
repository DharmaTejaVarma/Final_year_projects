import math
from typing import List, Tuple
import httpx
from fastapi import HTTPException, status

try:
    from app.core.config import settings
    from app.core.logger import logger
    from app.schemas.external import Coordinate, RouteCalculationResponse
    from app.utils.cache import api_cache, execute_with_retry
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.logger import logger
    from backend.app.schemas.external import Coordinate, RouteCalculationResponse
    from backend.app.utils.cache import api_cache, execute_with_retry


class OpenRouteService:
    """Service wrapping OpenRouteService for routing, distance, travel duration, and geometry."""

    BASE_URL = "https://api.openrouteservice.org/v2/directions"

    # Profile mapping to ORS profile path
    PROFILE_MAPPING = {
        "driving-car": "driving-car",
        "foot-walking": "foot-walking",
        "cycling-regular": "cycling-regular",
    }

    # Speed & circuity constants for fallback simulated routing
    PROFILE_SPECS = {
        "driving-car": {"speed_kmh": 55.0, "circuity": 1.30},
        "foot-walking": {"speed_kmh": 4.8, "circuity": 1.15},
        "cycling-regular": {"speed_kmh": 15.0, "circuity": 1.20},
    }

    def __init__(self):
        self.api_key = settings.ORS_API_KEY
        self.timeout = settings.EXTERNAL_API_TIMEOUT_SECONDS

    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate Great-Circle distance between two points on Earth in kilometers."""
        radius_earth_km = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return radius_earth_km * c

    def _generate_simulated_geometry(
        self,
        coords: List[Coordinate],
        steps_per_segment: int = 5,
    ) -> List[List[float]]:
        """Generate smooth intermediate coordinate waypoints for fallback simulated routes."""
        geometry: List[List[float]] = []
        for i in range(len(coords) - 1):
            p1 = coords[i]
            p2 = coords[i + 1]
            for step in range(steps_per_segment):
                t = step / float(steps_per_segment)
                lat = p1.latitude + t * (p2.latitude - p1.latitude)
                lon = p1.longitude + t * (p2.longitude - p1.longitude)
                geometry.append([round(lat, 6), round(lon, 6)])

        # Append final destination point
        final_pt = coords[-1]
        geometry.append([round(final_pt.latitude, 6), round(final_pt.longitude, 6)])
        return geometry

    def _calculate_simulated_route(
        self,
        coordinates: List[Coordinate],
        profile: str,
        reason: str,
    ) -> RouteCalculationResponse:
        """Generate a mathematically estimated route when live ORS API key is unavailable."""
        spec = self.PROFILE_SPECS.get(profile, self.PROFILE_SPECS["driving-car"])
        circuity = spec["circuity"]
        speed_kmh = spec["speed_kmh"]

        total_straight_km = 0.0
        for i in range(len(coordinates) - 1):
            c1 = coordinates[i]
            c2 = coordinates[i + 1]
            total_straight_km += self.haversine_distance_km(
                c1.latitude, c1.longitude, c2.latitude, c2.longitude
            )

        # Apply road circuity factor to convert straight-line to road distance
        estimated_distance_km = round(total_straight_km * circuity, 2)
        estimated_duration_mins = round((estimated_distance_km / speed_kmh) * 60.0, 1)

        simulated_geometry = self._generate_simulated_geometry(coordinates)

        return RouteCalculationResponse(
            distance_km=estimated_distance_km,
            duration_minutes=estimated_duration_mins,
            profile=profile,
            waypoints_count=len(coordinates),
            geometry=simulated_geometry,
            is_mocked=True,
            source="mocked",
            summary_note=(
                f"Simulated route calculation used: {reason}. "
                f"Estimated road distance using Haversine calculation with {circuity}x circuity factor "
                f"at {speed_kmh} km/h average velocity."
            ),
        )

    async def calculate_route(
        self,
        coordinates: List[Coordinate],
        profile: str = "driving-car",
    ) -> RouteCalculationResponse:
        """Calculate road route, distance, travel duration, and path geometry."""
        if len(coordinates) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least two waypoints (origin and destination) are required to calculate a route.",
            )

        ors_profile = self.PROFILE_MAPPING.get(profile, "driving-car")

        # Cache key based on profile and coordinate list
        coord_key = "_".join(f"{c.latitude:.4f},{c.longitude:.4f}" for c in coordinates)
        cache_key = f"ors:route:{ors_profile}:{coord_key}"
        cached = api_cache.get(cache_key)
        if cached is not None:
            logger.info(f"[CACHE HIT] Route calculation for {len(coordinates)} waypoints")
            cached_copy = cached.model_copy()
            cached_copy.source = "cached"
            return cached_copy

        # If ORS API key is missing, return cleanly identified simulation
        if not self.api_key or not self.api_key.strip():
            logger.info("ORS_API_KEY is not configured. Using simulated route calculation.")
            simulated_result = self._calculate_simulated_route(
                coordinates=coordinates,
                profile=profile,
                reason="ORS_API_KEY environment variable is not configured",
            )
            api_cache.set(cache_key, simulated_result, ttl=settings.CACHE_DEFAULT_TTL_SECONDS)
            return simulated_result

        # Call live OpenRouteService API
        # ORS expects coordinates as [[lon, lat], [lon, lat], ...]
        ors_coords = [[c.longitude, c.latitude] for c in coordinates]
        endpoint = f"{self.BASE_URL}/{ors_profile}/geojson"
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        body = {
            "coordinates": ors_coords,
        }

        async def _call():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(endpoint, json=body, headers=headers)
                if res.status_code in (401, 403):
                    logger.warning("ORS API authentication failed (invalid or expired key). Falling back to simulated route.")
                    return None
                res.raise_for_status()
                return res.json()

        try:
            data = await execute_with_retry(_call, operation_name="OpenRouteService live directions")
        except Exception as e:
            logger.error(f"Error calling live OpenRouteService: {e}. Falling back to simulation.")
            data = None

        if not data or "features" not in data or not data["features"]:
            simulated_result = self._calculate_simulated_route(
                coordinates=coordinates,
                profile=profile,
                reason="Live OpenRouteService request failed or rejected credentials; fallback simulation used",
            )
            api_cache.set(cache_key, simulated_result, ttl=settings.CACHE_DEFAULT_TTL_SECONDS)
            return simulated_result

        # Parse live ORS response
        feature = data["features"][0]
        properties = feature.get("properties", {})
        summary = properties.get("summary", {})
        geometry = feature.get("geometry", {})

        distance_meters = summary.get("distance", 0.0)
        duration_seconds = summary.get("duration", 0.0)

        raw_coordinates = geometry.get("coordinates", [])
        # Invert [lon, lat] -> [lat, lon] for our standardized API
        route_path = [[round(coord[1], 6), round(coord[0], 6)] for coord in raw_coordinates]

        live_result = RouteCalculationResponse(
            distance_km=round(distance_meters / 1000.0, 2),
            duration_minutes=round(duration_seconds / 60.0, 1),
            profile=profile,
            waypoints_count=len(coordinates),
            geometry=route_path,
            is_mocked=False,
            source="live",
            summary_note="Live route calculated via OpenRouteService API.",
        )

        api_cache.set(cache_key, live_result, ttl=settings.CACHE_DEFAULT_TTL_SECONDS)
        return live_result


ors_service = OpenRouteService()

