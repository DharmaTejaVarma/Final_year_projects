from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ==============================================================================
# GEOAPIFY DESTINATIONS SCHEMAS
# ==============================================================================
class DestinationItem(BaseModel):
    name: str
    formatted: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: float
    longitude: float
    place_id: Optional[str] = None
    bbox: Optional[Dict[str, float]] = None


class DestinationSearchResponse(BaseModel):
    query: str
    total: int
    source: str = Field(description="'live' or 'cached'")
    results: List[DestinationItem]


# ==============================================================================
# GEOAPIFY PLACES & ATTRACTIONS SCHEMAS
# ==============================================================================
class PlaceItem(BaseModel):
    place_id: str
    name: str
    category: str
    categories: List[str] = Field(default_factory=list)
    address: Optional[str] = None
    latitude: float
    longitude: float
    distance_meters: Optional[float] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_attribution: Optional[str] = None
    image_source: Optional[str] = None


class AttractionImageQuery(BaseModel):
    name: str
    city: Optional[str] = None
    attraction_id: Optional[str] = None


class AttractionImageItem(BaseModel):
    attraction_name: str
    city: Optional[str] = None
    attraction_id: Optional[str] = None
    image_url: str
    image_source: str
    image_attribution: Optional[str] = None
    image_verified: bool = True
    is_placeholder: bool = False


class BatchAttractionImageRequest(BaseModel):
    places: List[AttractionImageQuery]


class BatchAttractionImageResponse(BaseModel):
    total: int
    images: List[AttractionImageItem]



class PlacesSearchResponse(BaseModel):
    total: int
    source: str = Field(description="'live' or 'cached'")
    center: Dict[str, float]
    radius_meters: int
    places: List[PlaceItem]


class PlaceDetailsResponse(BaseModel):
    place: PlaceItem
    source: str
    raw_details: Optional[Dict[str, Any]] = None


# ==============================================================================
# OPENROUTESERVICE ROUTE SCHEMAS
# ==============================================================================
class Coordinate(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0, description="Latitude between -90 and 90")
    longitude: float = Field(ge=-180.0, le=180.0, description="Longitude between -180 and 180")


class RouteCalculationRequest(BaseModel):
    coordinates: List[Coordinate] = Field(
        min_length=2,
        description="List of at least two waypoints [origin, ..., destination]",
        examples=[
            [
                {"latitude": 35.6762, "longitude": 139.6503},
                {"latitude": 35.7148, "longitude": 139.7967},
            ]
        ]
    )
    profile: str = Field(
        default="driving-car",
        description="Travel profile: 'driving-car', 'foot-walking', or 'cycling-regular'",
        examples=["driving-car"]
    )

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str) -> str:
        valid_profiles = {"driving-car", "foot-walking", "cycling-regular"}
        clean_v = v.strip().lower()
        if clean_v not in valid_profiles:
            raise ValueError(f"Invalid profile '{v}'. Must be one of: {', '.join(valid_profiles)}")
        return clean_v


class RouteCalculationResponse(BaseModel):
    distance_km: float
    duration_minutes: float
    profile: str
    waypoints_count: int
    geometry: List[List[float]] = Field(
        description="Array of [lat, lon] coordinate pairs defining the route path"
    )
    is_mocked: bool = Field(description="True if route was computed via fallback/simulation rather than live ORS API")
    source: str = Field(description="'live', 'cached', or 'mocked'")
    summary_note: Optional[str] = None


# ==============================================================================
# OPEN-METEO WEATHER SCHEMAS
# ==============================================================================
class CurrentWeather(BaseModel):
    temperature_celsius: float
    humidity_percent: Optional[float] = None
    wind_speed_kmh: float
    weather_code: int
    condition: str


class DailyForecast(BaseModel):
    date: str
    weather_code: int
    condition: str
    max_temp_celsius: float
    min_temp_celsius: float
    precipitation_mm: float
    max_wind_speed_kmh: float


class WeatherForecastResponse(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    source: str = Field(description="'live' or 'cached'")
    current: Optional[CurrentWeather] = None
    daily: List[DailyForecast] = Field(default_factory=list)
    warning: Optional[str] = None

