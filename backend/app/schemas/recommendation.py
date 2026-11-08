from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

try:
    from app.algorithms.poi_scoring import ScoringWeights
except ImportError:
    from backend.app.algorithms.poi_scoring import ScoringWeights


class WeightsConfig(BaseModel):
    """Customizable weights for the 6 recommendation scoring dimensions."""
    preference: float = Field(default=0.30, ge=0.0, le=1.0)
    distance: float = Field(default=0.15, ge=0.0, le=1.0)
    time: float = Field(default=0.15, ge=0.0, le=1.0)
    weather: float = Field(default=0.15, ge=0.0, le=1.0)
    category: float = Field(default=0.15, ge=0.0, le=1.0)
    budget: float = Field(default=0.10, ge=0.0, le=1.0)

    @field_validator("*", mode="before")
    @classmethod
    def convert_non_negative(cls, v: Any) -> float:
        try:
            val = float(v)
            if val < 0.0:
                raise ValueError("Weight cannot be negative")
            return val
        except (ValueError, TypeError):
            raise ValueError(f"Invalid weight value: {v}")

    def to_scoring_weights(self) -> ScoringWeights:
        return ScoringWeights(
            preference=self.preference,
            distance=self.distance,
            time=self.time,
            weather=self.weather,
            category=self.category,
            budget=self.budget,
        ).normalized()


class RecommendationRequest(BaseModel):
    """Traveler input profile and trip context for POI recommendation."""
    destination: str = Field(
        ...,
        min_length=2,
        examples=["Hyderabad"],
        description="Target destination city or region name",
    )
    interests: List[str] = Field(
        default_factory=lambda: ["Historical Places", "Food", "Photography"],
        examples=[["Historical Places", "Food", "Photography"]],
        description="List of traveler interest categories or activity tags",
    )
    budget: Optional[float] = Field(
        default=5000.0,
        ge=0.0,
        examples=[5000.0],
        description="Total trip budget in local currency (e.g., INR ₹5,000)",
    )
    available_duration_days: int = Field(
        default=2,
        ge=1,
        le=30,
        examples=[2],
        description="Duration of the trip in days",
    )
    transportation: str = Field(
        default="Car",
        examples=["Car"],
        description="Travel mode: Car, Walking, Public Transit, Bicycle",
    )
    daily_touring_hours: float = Field(
        default=8.0,
        ge=1.0,
        le=16.0,
        description="Estimated active hours available per day",
    )
    max_distance_km: Optional[float] = Field(
        default=35.0,
        ge=1.0,
        le=150.0,
        description="Maximum search radius from destination center in km",
    )
    origin_latitude: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Optional traveler starting latitude",
    )
    origin_longitude: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Optional traveler starting longitude",
    )
    weights: Optional[WeightsConfig] = None
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of recommendations to return",
    )


class FactorScores(BaseModel):
    """Normalized [0.0 - 1.0] factor scores for an individual POI."""
    preference: float = Field(description="Preference matching score (P)")
    distance: float = Field(description="Distance suitability score (D)")
    time: float = Field(description="Temporal feasibility score (T)")
    weather: float = Field(description="Weather suitability score (W)")
    category: float = Field(description="Category compatibility score (C)")
    budget: float = Field(description="Budget suitability score (B)")


class RecommendedPOI(BaseModel):
    """Context-aware recommended point of interest with transparent scoring breakdown."""
    place_id: str
    name: str
    category: str
    categories: List[str] = Field(default_factory=list)
    latitude: float
    longitude: float
    address: Optional[str] = None
    distance_km: Optional[float] = None
    estimated_duration_mins: Optional[int] = None
    entrance_fee: Optional[float] = None
    factor_scores: FactorScores
    final_score: float
    baseline_preference_score: float
    rank: int
    explanation: str
    flags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    image_attribution: Optional[str] = None
    image_source: Optional[str] = None


class BaselineComparison(BaseModel):
    """Empirical comparison between context-aware multi-criteria scoring and preference baseline."""
    average_context_score: float
    average_baseline_score: float
    rank_displacements: int = Field(
        description="Number of places whose rank shifted due to contextual factors (weather, distance, time, budget)",
    )
    summary: str


class RecommendationResponse(BaseModel):
    """Complete response payload containing ranked POIs and algorithmic metadata."""
    destination: str
    destination_coordinates: Dict[str, float]
    total_candidates_analyzed: int
    total_recommended: int
    weights_applied: Dict[str, float]
    weather_context: Optional[Dict[str, Any]] = None
    recommendations: List[RecommendedPOI]
    baseline_comparison: BaselineComparison

