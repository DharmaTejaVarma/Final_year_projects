from typing import Any, Dict, List, Union
from app.schemas.report import (
    AttractionMetrics,
    BudgetUtilization,
    CategoryDistributionItem,
    DailyExpenseItem,
    DailyTravelDurationItem,
    DistanceComparisonItem,
    ReportAnalytics,
    ScoreDistributionItem,
)


class AnalyticsService:
    """Computes comprehensive visual analytics from generated travel itineraries."""

    @staticmethod
    def _extract_dict(obj: Any) -> Dict[str, Any]:
        """Convert Pydantic model or dict to dictionary representation."""
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif hasattr(obj, "dict"):
            return obj.dict()
        elif isinstance(obj, dict):
            return obj
        return {}

    def compute_itinerary_analytics(self, itinerary: Union[Dict[str, Any], Any]) -> ReportAnalytics:
        """Process an itinerary and generate the 7 required visualization datasets."""
        data = self._extract_dict(itinerary)

        days = data.get("days", [])
        budget = data.get("budget_summary", {})
        if hasattr(budget, "model_dump"):
            budget = budget.model_dump()
        elif not isinstance(budget, dict):
            budget = {}

        cb = budget.get("by_category") or budget.get("category_breakdown") or {}
        if hasattr(cb, "model_dump"):
            cb = cb.model_dump()
        elif not isinstance(cb, dict):
            cb = {}

        total_days = max(len(days), 1)

        # 1. Category Distribution
        category_counts: Dict[str, int] = {}
        all_stops: List[Dict[str, Any]] = []
        for day in days:
            stops = day.get("stops", [])
            for s in stops:
                all_stops.append(s)
                cat = (s.get("category") or "Sightseeing").strip().capitalize()
                category_counts[cat] = category_counts.get(cat, 0) + 1

        total_cat_stops = max(sum(category_counts.values()), 1)
        category_distribution: List[CategoryDistributionItem] = []
        for cat, cnt in category_counts.items():
            category_distribution.append(
                CategoryDistributionItem(
                    category=cat,
                    count=cnt,
                    percentage=round((cnt / total_cat_stops) * 100.0, 1),
                )
            )

        if not category_distribution:
            category_distribution.append(
                CategoryDistributionItem(category="General Attraction", count=1, percentage=100.0)
            )

        # 2. Recommendation Score Distribution
        score_distribution: List[ScoreDistributionItem] = []
        for s in all_stops:
            name = s.get("name", "Attraction")
            raw_score = s.get("recommendation_score")
            score = float(raw_score) if raw_score is not None else 0.85
            score = max(0.0, min(1.0, score))

            if score >= 0.90:
                band = "Exceptional (0.90-1.00)"
            elif score >= 0.80:
                band = "High (0.80-0.89)"
            elif score >= 0.70:
                band = "Good (0.70-0.79)"
            else:
                band = "Moderate (< 0.70)"

            score_distribution.append(
                ScoreDistributionItem(
                    attraction_name=name,
                    score=round(score, 3),
                    score_band=band,
                )
            )

        # 3. Daily Expense Distribution
        daily_expense_distribution: List[DailyExpenseItem] = []
        total_transport = float(cb.get("transportation", 0.0))
        total_food = float(cb.get("food", 0.0))
        total_accom = float(cb.get("accommodation", 0.0))

        daily_transport_alloc = round(total_transport / total_days, 2)
        daily_food_alloc = round(total_food / total_days, 2)
        daily_accom_alloc = round(total_accom / total_days, 2)

        for day in days:
            day_num = int(day.get("day_number", 1))
            date_str = str(day.get("date", f"Day {day_num}"))
            day_stops = day.get("stops", [])

            day_entrance = sum(float(s.get("total_entrance_fee", 0.0)) for s in day_stops)
            day_cost = float(
                day.get(
                    "daily_estimated_cost",
                    day_entrance + daily_transport_alloc + daily_food_alloc + daily_accom_alloc,
                )
            )

            daily_expense_distribution.append(
                DailyExpenseItem(
                    day_number=day_num,
                    date=date_str,
                    total_cost=round(day_cost, 2),
                    entrance_fees=round(day_entrance, 2),
                    food=daily_food_alloc,
                    transportation=daily_transport_alloc,
                    accommodation=daily_accom_alloc,
                )
            )

        # 4. Daily Travel Duration
        daily_travel_duration: List[DailyTravelDurationItem] = []
        for day in days:
            day_num = int(day.get("day_number", 1))
            date_str = str(day.get("date", f"Day {day_num}"))
            travel_mins = float(day.get("daily_travel_time_mins", 45.0))
            visit_mins = float(day.get("daily_visit_time_mins", 180.0))
            total_mins = float(day.get("daily_total_duration_mins", travel_mins + visit_mins))

            daily_travel_duration.append(
                DailyTravelDurationItem(
                    day_number=day_num,
                    date=date_str,
                    travel_time_mins=round(travel_mins, 1),
                    visit_time_mins=round(visit_mins, 1),
                    total_duration_mins=round(total_mins, 1),
                    travel_hours=round(travel_mins / 60.0, 2),
                    visit_hours=round(visit_mins / 60.0, 2),
                )
            )

        # 5. Distance Comparison
        distance_comparison: List[DistanceComparisonItem] = []
        cumulative_dist = 0.0
        for day in days:
            day_num = int(day.get("day_number", 1))
            date_str = str(day.get("date", f"Day {day_num}"))
            dist = float(day.get("daily_distance_km", 12.0))
            cumulative_dist += dist

            distance_comparison.append(
                DistanceComparisonItem(
                    day_number=day_num,
                    date=date_str,
                    distance_km=round(dist, 2),
                    cumulative_distance_km=round(cumulative_dist, 2),
                )
            )

        # 6. Budget Utilization
        total_budget = float(budget.get("total_budget", data.get("budget", 5000.0)))
        total_cost = float(budget.get("estimated_total_cost", data.get("total_estimated_cost", 0.0)))
        remaining = float(budget.get("remaining_budget", max(0.0, total_budget - total_cost)))
        overrun = float(budget.get("budget_overrun", max(0.0, total_cost - total_budget)))
        travelers = max(int(data.get("travelers_count", 1)), 1)
        cost_per_person = float(budget.get("cost_per_traveler", round(total_cost / travelers, 2)))

        utilization_pct = round((total_cost / total_budget) * 100.0, 1) if total_budget > 0 else 100.0

        budget_utilization = BudgetUtilization(
            total_budget=round(total_budget, 2),
            estimated_cost=round(total_cost, 2),
            remaining_budget=round(remaining, 2),
            utilization_percentage=utilization_pct,
            cost_per_traveler=round(cost_per_person, 2),
            is_over_budget=(overrun > 0.0),
            budget_overrun=round(overrun, 2),
        )

        # 7. Attraction Volume and Environmental Metrics
        total_rec = int(data.get("total_attractions_scheduled", len(all_stops)))
        outdoor_cnt = sum(1 for s in all_stops if s.get("is_outdoor", False))
        indoor_cnt = len(all_stops) - outdoor_cnt
        verified_hours_cnt = sum(1 for s in all_stops if s.get("opening_hours_status") == "verified")
        avg_visit_mins = (
            round(sum(float(s.get("visit_duration_mins", 90)) for s in all_stops) / max(len(all_stops), 1), 1)
        )

        attraction_metrics = AttractionMetrics(
            total_recommended=total_rec,
            scheduled_count=len(all_stops),
            outdoor_count=outdoor_cnt,
            indoor_count=indoor_cnt,
            average_visit_duration_mins=avg_visit_mins,
            verified_opening_hours_count=verified_hours_cnt,
        )

        return ReportAnalytics(
            category_distribution=category_distribution,
            score_distribution=score_distribution,
            daily_expense_distribution=daily_expense_distribution,
            daily_travel_duration=daily_travel_duration,
            distance_comparison=distance_comparison,
            budget_utilization=budget_utilization,
            attraction_metrics=attraction_metrics,
        )


analytics_service = AnalyticsService()

