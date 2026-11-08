from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CategoryDistributionItem(BaseModel):
    """Categorical breakdown of scheduled attractions."""
    category: str
    count: int
    percentage: float


class ScoreDistributionItem(BaseModel):
    """Recommendation engine score for an individual attraction."""
    attraction_name: str
    score: float = Field(..., ge=0.0, le=1.0)
    score_band: str = Field(..., description="e.g. 'Exceptional (0.9-1.0)', 'High (0.8-0.9)'")


class DailyExpenseItem(BaseModel):
    """Daily expense breakdown by operational categories."""
    day_number: int
    date: str
    total_cost: float
    entrance_fees: float
    food: float
    transportation: float
    accommodation: float = 0.0


class DailyTravelDurationItem(BaseModel):
    """Comparison of active visit duration vs transit duration."""
    day_number: int
    date: str
    travel_time_mins: float
    visit_time_mins: float
    total_duration_mins: float
    travel_hours: float
    visit_hours: float


class DistanceComparisonItem(BaseModel):
    """Road distance traversed per day and cumulative progress."""
    day_number: int
    date: str
    distance_km: float
    cumulative_distance_km: float


class BudgetUtilization(BaseModel):
    """Financial capacity vs algorithmic expenditure metrics."""
    total_budget: float
    estimated_cost: float
    remaining_budget: float
    utilization_percentage: float
    cost_per_traveler: float
    is_over_budget: bool
    budget_overrun: float


class AttractionMetrics(BaseModel):
    """Attraction volume and environmental characteristics."""
    total_recommended: int
    scheduled_count: int
    outdoor_count: int
    indoor_count: int
    average_visit_duration_mins: float
    verified_opening_hours_count: int


class ReportAnalytics(BaseModel):
    """Container for all 7 required visualization data models."""
    category_distribution: List[CategoryDistributionItem]
    score_distribution: List[ScoreDistributionItem]
    daily_expense_distribution: List[DailyExpenseItem]
    daily_travel_duration: List[DailyTravelDurationItem]
    distance_comparison: List[DistanceComparisonItem]
    budget_utilization: BudgetUtilization
    attraction_metrics: AttractionMetrics


class ReportGenerateRequest(BaseModel):
    """Payload to request PDF dossier and analytics computation."""
    itinerary_id: Optional[str] = Field(
        default=None,
        description="ID of a previously generated itinerary cached in the backend"
    )
    itinerary_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Full itinerary dictionary if already available on client side"
    )
    title: Optional[str] = Field(
        default=None,
        description="Optional custom document title"
    )
    planning_notes: Optional[str] = Field(
        default=None,
        description="Custom travel guidelines or user notes"
    )


class ReportMetadataResponse(BaseModel):
    """Comprehensive report metadata and computed visual analytics."""
    report_id: str
    itinerary_id: str
    title: str
    destination: str
    travel_dates: str
    travelers_count: int
    total_days: int
    total_cost: float
    total_distance_km: float
    total_duration_hours: float
    file_size_bytes: int
    created_at: str
    download_url: str
    analytics: ReportAnalytics
    summary: Dict[str, Any]

