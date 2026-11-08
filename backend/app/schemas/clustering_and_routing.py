from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator


class POIInput(BaseModel):
    """Input representation of a tourist point of interest for clustering and routing."""

    id: Optional[Union[int, str]] = Field(default=None, description="Unique identifier for the POI")
    name: str = Field(..., min_length=1, max_length=200, description="Name of the place or attraction")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to 180)")
    category: Optional[str] = Field(default="attraction", description="Category or interest tag")
    address: Optional[str] = Field(default=None, description="Human-readable address")
    visit_duration_mins: int = Field(default=60, ge=0, le=720, description="Estimated time spent exploring in minutes")
    estimated_cost: Optional[float] = Field(default=0.0, ge=0.0, description="Estimated entry fee or visit cost")


class ClusterCentroid(BaseModel):
    """Centroid of a geographic cluster."""

    latitude: float
    longitude: float


class ClusterMember(BaseModel):
    """Member POI within a cluster."""

    id: Optional[Union[int, str]]
    name: str
    latitude: float
    longitude: float
    category: Optional[str] = None
    visit_duration_mins: int = 60


class ClusterBoundingBox(BaseModel):
    """Spatial bounding box of a cluster."""

    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


class ClusterGroup(BaseModel):
    """A spatial cluster of tourist attractions."""

    cluster_id: int = Field(..., description="Cluster identifier; -1 indicates noise/outliers")
    label: str = Field(..., description="Human-friendly label (e.g. 'Cluster 1', 'Noise / Outliers')")
    is_noise: bool = Field(..., description="True if marked as noise/outlier by DBSCAN")
    members_count: int = Field(..., description="Number of POIs in this cluster")
    centroid: Optional[ClusterCentroid] = Field(default=None, description="Geographic centroid")
    radius_km: float = Field(default=0.0, description="Maximum distance from centroid to any member in km")
    bounding_box: Optional[ClusterBoundingBox] = Field(default=None, description="Geographic envelope")
    places: List[ClusterMember] = Field(default_factory=list, description="List of attractions in this cluster")


class KMeansComparison(BaseModel):
    """Comparison evaluation against standard K-Means clustering."""

    k: int
    clusters_count: int
    inertia: Optional[float] = None
    silhouette_score: Optional[float] = None
    cluster_distribution: Dict[str, int] = Field(default_factory=dict)
    summary: str


class ClusteringRequest(BaseModel):
    """Request payload for geographic clustering."""

    places: List[POIInput] = Field(..., min_length=1, description="List of tourist attractions to cluster")
    eps_km: float = Field(default=3.5, gt=0.0, le=50.0, description="DBSCAN neighborhood search radius in kilometers")
    min_samples: int = Field(default=2, ge=1, le=20, description="Minimum POIs to form a dense core cluster")
    compare_kmeans: bool = Field(default=True, description="Whether to include K-Means baseline comparison")
    k: Optional[int] = Field(default=None, ge=1, le=20, description="Manual K for K-Means (defaults to sensible auto)")

    @field_validator("places")
    @classmethod
    def validate_places_non_empty(cls, v: List[POIInput]) -> List[POIInput]:
        if not v:
            raise ValueError("The places list must contain at least one point of interest.")
        return v


class ClusteringResponse(BaseModel):
    """Response payload containing spatial clusters and algorithmic explanation."""

    algorithm_used: str = "DBSCAN (Density-Based Spatial Clustering of Applications with Noise)"
    metric: str = "Haversine (Great-Circle Geodetic Distance on WGS-84 Sphere)"
    eps_km: float
    min_samples: int
    total_places: int
    clusters_count: int
    noise_count: int
    clusters: List[ClusterGroup]
    kmeans_comparison: Optional[KMeansComparison] = None
    dbscan_suitability_explanation: str


class RouteOptimizationRequest(BaseModel):
    """Request payload for route optimization and itinerary sequencing."""

    places: List[POIInput] = Field(..., min_length=1, description="Attractions to visit")
    start_location: Optional[POIInput] = Field(default=None, description="Starting point (hotel, airport, origin)")
    end_location: Optional[POIInput] = Field(default=None, description="Ending point (hotel, return destination)")
    transportation: str = Field(
        default="driving-car",
        pattern="^(driving-car|foot-walking|cycling-regular)$",
        description="Mode of travel: driving-car, foot-walking, or cycling-regular",
    )
    daily_available_hours: float = Field(
        default=8.0, gt=0.5, le=24.0, description="Maximum touring hours available per day"
    )
    start_time: str = Field(
        default="09:00",
        pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
        description="Starting time of day in 24-hour HH:MM format",
    )
    total_days: Optional[int] = Field(
        default=None, ge=1, le=14, description="Optional maximum days to distribute the trip across"
    )

    @field_validator("places")
    @classmethod
    def validate_places_count(cls, v: List[POIInput]) -> List[POIInput]:
        if not v:
            raise ValueError("The places list must contain at least one point of interest.")
        return v


class RouteStop(BaseModel):
    """A scheduled stop on the daily travel route."""

    stop_order: int
    place_id: Optional[Union[int, str]] = None
    name: str
    latitude: float
    longitude: float
    category: Optional[str] = None
    arrival_time: str
    departure_time: str
    visit_duration_mins: int
    leg_distance_km: float
    leg_travel_time_mins: float
    is_start_location: bool = False
    is_end_location: bool = False


class DailyRoute(BaseModel):
    """Optimized itinerary and path for a single travel day."""

    day_number: int
    stops: List[RouteStop]
    total_distance_km: float
    total_travel_time_mins: float
    total_visit_time_mins: float
    total_day_duration_mins: float
    geometry: List[List[float]] = Field(default_factory=list, description="Array of [lat, lon] waypoints")
    summary: str


class RouteComparison(BaseModel):
    """Quantitative comparison between initial unoptimized sequence and 2-Opt optimized route."""

    initial_distance_km: float
    optimized_distance_km: float
    distance_saved_km: float
    improvement_percentage: float
    initial_travel_time_mins: float
    optimized_travel_time_mins: float
    time_saved_mins: float
    method_used: str = "Nearest-Neighbor Construction + 2-Opt Local Search"
    details: str


class RouteOptimizationResponse(BaseModel):
    """Response payload containing optimized visiting sequences, schedule, and route comparison."""

    transportation: str
    total_days: int
    total_places_visited: int
    total_distance_km: float
    total_travel_time_mins: float
    total_visit_time_mins: float
    comparison: RouteComparison
    daily_routes: List[DailyRoute]
    is_mocked: bool
    source: str
    summary_note: str
