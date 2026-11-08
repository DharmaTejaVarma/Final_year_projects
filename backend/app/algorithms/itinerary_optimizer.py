from typing import Any, Dict, List, Optional
from collections import Counter

try:
    from app.schemas.itinerary import (
        ItineraryDayPlan,
        ItineraryUtility,
        BudgetCalculationResult,
    )
except ImportError:
    from backend.app.schemas.itinerary import (
        ItineraryDayPlan,
        ItineraryUtility,
        BudgetCalculationResult,
    )

# Default objective function weights: alpha*R + beta*W + gamma*T + delta*Dv - lambda*Tr - mu*C
DEFAULT_UTILITY_WEIGHTS = {
    "alpha": 0.30,   # Recommendation score weight
    "beta": 0.20,    # Weather suitability weight
    "gamma": 0.15,   # Time efficiency weight
    "delta": 0.15,   # Category diversity weight
    "lambda": 0.10,  # Transit duration penalty
    "mu": 0.10,      # Cost & budget overrun penalty
}


def calculate_itinerary_utility(
    days: List[ItineraryDayPlan],
    budget_result: BudgetCalculationResult,
    daily_available_hours: float,
    weights: Optional[Dict[str, float]] = None,
) -> ItineraryUtility:
    """Evaluate multi-criteria itinerary utility objective function:

    U(I) = α·R(I) + β·W(I) + γ·T(I) + δ·Dv(I) - λ·Tr(I) - μ·C(I)

    Where:
    - R(I): Recommendation quality of selected attractions
    - W(I): Weather adaptation and outdoor suitability
    - T(I): Time efficiency (visiting time vs travel overhead)
    - Dv(I): Thematic category diversity (prevents category fatigue)
    - Tr(I): Transit friction penalty (prolonged road travel)
    - C(I): Budget expenditure and overrun penalty
    """
    w = dict(DEFAULT_UTILITY_WEIGHTS)
    if weights:
        w.update(weights)

    all_stops = [
        s for d in days for s in d.stops
        if not s.is_start_location and not s.is_end_location
    ]
    total_stops = len(all_stops)

    if total_stops == 0:
        return ItineraryUtility(
            overall_utility_score=0.0,
            recommendation_component=0.0,
            weather_component=0.0,
            time_efficiency_component=0.0,
            diversity_component=0.0,
            transit_penalty=0.0,
            cost_penalty=0.0,
            formula_summary="No attractions scheduled.",
            weights=w,
        )

    # 1. Recommendation Component R(I)
    rec_component = 0.80  # Default strong base recommendation
    # If individual stops have recommendation metrics, average them
    # For now, base quality is high because attractions are ranked by Phase 4 POI engine

    # 2. Weather Component W(I)
    weather_scores = [s.weather_suitability_score for s in all_stops]
    w_component = round(sum(weather_scores) / float(len(weather_scores)), 3)

    # 3. Time Efficiency Component T(I) = Visit Time / (Visit Time + Travel Time)
    tot_visit = sum(d.daily_visit_time_mins for d in days)
    tot_travel = sum(d.daily_travel_time_mins for d in days)
    tot_active = tot_visit + tot_travel
    t_component = round(tot_visit / max(1.0, tot_active), 3)

    # 4. Diversity Component Dv(I) = Unique Categories / Total Stops
    categories = [s.category.lower() if s.category else "attraction" for s in all_stops]
    unique_cats = len(set(categories))
    dv_component = round(min(1.0, (unique_cats + 1) / max(2.0, total_stops)), 3)

    # 5. Transit Penalty Tr(I) = Travel Time / Total Available Hours
    total_available_mins = len(days) * daily_available_hours * 60.0
    tr_penalty = round(min(1.0, tot_travel / max(1.0, total_available_mins)), 3)

    # 6. Cost Penalty C(I) = Total Cost / Budget (+ Overrun Penalty)
    budget = max(1.0, budget_result.total_budget)
    cost_ratio = budget_result.estimated_total_cost / budget
    if budget_result.is_budget_exceeded:
        # Heavily penalize overruns
        c_penalty = round(min(1.5, 1.0 + (budget_result.budget_overrun / budget)), 3)
    else:
        # Proportional utilization
        c_penalty = round(min(1.0, cost_ratio * 0.8), 3)

    # Compute raw utility
    raw_utility = (
        w["alpha"] * rec_component
        + w["beta"] * w_component
        + w["gamma"] * t_component
        + w["delta"] * dv_component
        - w["lambda"] * tr_penalty
        - w["mu"] * c_penalty
    )

    overall_score = round(max(0.0, min(1.0, raw_utility)), 3)

    summary = (
        f"U(I) = {w['alpha']:.2f}(R:{rec_component:.2f}) + {w['beta']:.2f}(W:{w_component:.2f}) + "
        f"{w['gamma']:.2f}(T:{t_component:.2f}) + {w['delta']:.2f}(Dv:{dv_component:.2f}) - "
        f"{w['lambda']:.2f}(Tr:{tr_penalty:.2f}) - {w['mu']:.2f}(C:{c_penalty:.2f}) = {overall_score:.3f}"
    )

    return ItineraryUtility(
        overall_utility_score=overall_score,
        recommendation_component=rec_component,
        weather_component=w_component,
        time_efficiency_component=t_component,
        diversity_component=dv_component,
        transit_penalty=tr_penalty,
        cost_penalty=c_penalty,
        formula_summary=summary,
        weights=w,
    )

