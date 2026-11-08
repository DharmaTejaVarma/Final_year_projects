import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from app.algorithms.route_optimizer import time_str_to_minutes
    from app.schemas.itinerary import (
        ConstraintViolation,
        ItineraryDayPlan,
        ItineraryStop,
        ItineraryValidationResponse,
    )
except ImportError:
    from backend.app.algorithms.route_optimizer import time_str_to_minutes
    from backend.app.schemas.itinerary import (
        ConstraintViolation,
        ItineraryDayPlan,
        ItineraryStop,
        ItineraryValidationResponse,
    )


def parse_opening_hours_window(opening_hours_str: Optional[str]) -> Optional[Tuple[int, int]]:
    """Parse opening hours strings into daily (open_minute, close_minute) window.

    Supports common formats:
    - '09:00-18:00', '09:00 - 18:00', '10:00-17:30'
    - 'Mon-Sun 09:00 - 18:00'
    - '9:00-17:00'
    """
    if not opening_hours_str or not opening_hours_str.strip():
        return None

    text = opening_hours_str.strip()

    if "closed" in text.lower() and not any(char.isdigit() for char in text):
        return None

    # Search for pattern HH:MM - HH:MM or H:MM - H:MM
    match = re.search(r"(\d{1,2}):(\d{2})\s*(?:-|to)\s*(\d{1,2}):(\d{2})", text)
    if match:
        h1, m1, h2, m2 = match.groups()
        open_mins = int(h1) * 60 + int(m1)
        close_mins = int(h2) * 60 + int(m2)
        # Handle 24-hour closure edge case (e.g. 00:00 closing = end of day 1440)
        if close_mins <= open_mins and close_mins == 0:
            close_mins = 1440
        return open_mins, close_mins

    return None


def validate_itinerary_plan(
    destination: str,
    start_date: str,
    end_date: str,
    budget: float,
    daily_available_hours: float,
    days: List[ItineraryDayPlan],
    total_cost: Optional[float] = None,
) -> ItineraryValidationResponse:
    """Perform rigorous constraint verification across all days, stops, and budget allocations.

    Validates:
    - Date ordering and trip duration.
    - Time non-overlap between consecutive visits and transit legs.
    - Compliance with verified venue opening hours.
    - Adherence to daily available touring hours.
    - Identification of unknown or missing parameters.
    - Budget feasibility and overrun detection.
    """
    violations: List[ConstraintViolation] = []
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Date Validation
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        if e_date < s_date:
            err = f"Invalid date range: start_date ({start_date}) occurs after end_date ({end_date})."
            errors.append(err)
            violations.append(
                ConstraintViolation(
                    rule="DATE_CHRONOLOGY",
                    severity="error",
                    description=err,
                )
            )
        else:
            num_days = (e_date - s_date).days + 1
            if len(days) != num_days:
                warn = f"Day count mismatch: date span implies {num_days} days, but itinerary has {len(days)} day plans."
                warnings.append(warn)
    except ValueError as ve:
        err = f"Invalid date format: {ve}. Expected YYYY-MM-DD."
        errors.append(err)
        violations.append(
            ConstraintViolation(
                rule="DATE_FORMAT",
                severity="error",
                description=err,
            )
        )

    # 2. Daily Schedule Constraints Validation
    daily_max_minutes = int(daily_available_hours * 60.0)

    for day in days:
        day_num = day.day_number

        # Check total daily duration
        if day.daily_total_duration_mins > daily_max_minutes + 15:  # 15 min leeway
            warn = (
                f"Day {day_num} total duration ({day.daily_total_duration_mins:.0f} mins) "
                f"exceeds daily available touring limit of {daily_max_minutes} mins ({daily_available_hours}h)."
            )
            warnings.append(warn)
            violations.append(
                ConstraintViolation(
                    rule="DAILY_TIME_LIMIT",
                    day_number=day_num,
                    severity="warning",
                    description=warn,
                )
            )

        # Check stops chronology and overlaps
        prev_departure_min: Optional[int] = None
        prev_stop_name: Optional[str] = None

        for stop in day.stops:
            stop_name = stop.name
            arr_min = time_str_to_minutes(stop.arrival_time)
            dep_min = time_str_to_minutes(stop.departure_time)

            # Check interior stop duration
            if dep_min < arr_min and not stop.is_start_location and not stop.is_end_location:
                err = f"Day {day_num} stop '{stop_name}': departure time ({stop.departure_time}) is before arrival time ({stop.arrival_time})."
                errors.append(err)
                violations.append(
                    ConstraintViolation(
                        rule="NEGATIVE_DURATION",
                        day_number=day_num,
                        stop_name=stop_name,
                        severity="error",
                        description=err,
                    )
                )

            # Check overlap with previous stop
            if prev_departure_min is not None:
                # Minimum arrival must be prev departure + travel duration (with 1 min tolerance)
                min_valid_arrival = prev_departure_min + int(round(stop.travel_duration_mins)) - 1
                if arr_min < min_valid_arrival:
                    err = (
                        f"Day {day_num}: Overlapping schedule between '{prev_stop_name}' (departs {prev_departure_min//60:02d}:{prev_departure_min%60:02d}) "
                        f"and '{stop_name}' (arrives {stop.arrival_time}) with travel duration {stop.travel_duration_mins:.1f} mins."
                    )
                    errors.append(err)
                    violations.append(
                        ConstraintViolation(
                            rule="TRANSIT_OVERLAP",
                            day_number=day_num,
                            stop_name=stop_name,
                            severity="error",
                            description=err,
                        )
                    )

            # Check Opening Hours Compliance
            if stop.opening_hours:
                window = parse_opening_hours_window(stop.opening_hours)
                if window:
                    open_m, close_m = window
                    # If visit starts before opening or ends after closing (ignoring hotel starts/ends)
                    if not stop.is_start_location and not stop.is_end_location:
                        if arr_min < open_m - 15:  # 15 mins early arrival tolerance
                            warn = (
                                f"Day {day_num} stop '{stop_name}' arrives at {stop.arrival_time}, "
                                f"which is before opening time ({open_m//60:02d}:{open_m%60:02d})."
                            )
                            warnings.append(warn)
                            violations.append(
                                ConstraintViolation(
                                    rule="VISIT_BEFORE_OPENING",
                                    day_number=day_num,
                                    stop_name=stop_name,
                                    severity="warning",
                                    description=warn,
                                )
                            )
                        if dep_min > close_m + 15:  # 15 mins tolerance
                            warn = (
                                f"Day {day_num} stop '{stop_name}' departs at {stop.departure_time}, "
                                f"which is after closing time ({close_m//60:02d}:{close_m%60:02d})."
                            )
                            warnings.append(warn)
                            violations.append(
                                ConstraintViolation(
                                    rule="VISIT_AFTER_CLOSING",
                                    day_number=day_num,
                                    stop_name=stop_name,
                                    severity="warning",
                                    description=warn,
                                )
                            )
            elif not stop.is_start_location and not stop.is_end_location:
                # Clearly identify unknown opening hours
                warn = f"Day {day_num} stop '{stop_name}': Opening hours are unverified. Confirm locally before visiting."
                warnings.append(warn)

            prev_departure_min = dep_min
            prev_stop_name = stop_name

    # 3. Budget Feasibility Check
    if total_cost is not None and total_cost > budget:
        overrun = total_cost - budget
        warn = f"Budget overrun detected: Total estimated cost (₹{total_cost:.2f}) exceeds budget (₹{budget:.2f}) by ₹{overrun:.2f}."
        warnings.append(warn)
        violations.append(
            ConstraintViolation(
                rule="BUDGET_OVERRUN",
                severity="warning",
                description=warn,
            )
        )

    is_valid = len(errors) == 0
    can_generate = is_valid

    summary = (
        f"Validation complete: {'FEASIBLE' if is_valid else 'INFEASIBLE'}. "
        f"{len(errors)} blocking errors, {len(warnings)} non-blocking warnings detected."
    )

    return ItineraryValidationResponse(
        is_valid=is_valid,
        can_generate=can_generate,
        violations_count=len(violations),
        warnings_count=len(warnings),
        errors=errors,
        warnings=warnings,
        violations=violations,
        feasibility_summary=summary,
    )

