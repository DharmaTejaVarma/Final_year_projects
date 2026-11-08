import math
from typing import Any, Dict, List, Optional, Tuple

try:
    from app.schemas.itinerary import (
        BudgetCalculationResult,
        ExpenseCategoryBreakdown,
        PriceCategoryBreakdown,
    )
except ImportError:
    from backend.app.schemas.itinerary import (
        BudgetCalculationResult,
        ExpenseCategoryBreakdown,
        PriceCategoryBreakdown,
    )

# Mode transport cost parameters (per km in INR)
TRANSPORT_RATES = {
    "driving-car": 18.0,      # Fuel, cab, or private car service per km
    "cycling-regular": 2.0,   # Bicycle rental amortized per km
    "foot-walking": 0.0,      # Free pedestrian transit
}

# Daily meal cost per person by tier (in INR)
MEAL_TIER_RATES = {
    "budget": 500.0,
    "moderate": 1000.0,
    "luxury": 2500.0,
}

# Nightly accommodation room rates (in INR)
ACCOMMODATION_RATES = {
    "budget": 1800.0,
    "standard": 3500.0,
    "luxury": 7500.0,
}

# Conservative placeholder entrance fee per person when price is unknown
DEFAULT_ESTIMATED_ENTRANCE_FEE = 150.0
CONTINGENCY_PERCENTAGE = 0.08  # 8% emergency / miscellaneous buffer


def calculate_itinerary_budget(
    total_budget: float,
    travelers_count: int,
    total_days: int,
    total_distance_km: float,
    transportation: str,
    stops_data: List[Dict[str, Any]],
    include_accommodation: bool = False,
    accommodation_type: str = "standard",
    dietary_budget_tier: str = "moderate",
) -> BudgetCalculationResult:
    """Calculate comprehensive multi-category itinerary budget with explicit provenance separation.

    Separates prices into:
    - Verified: Confirmed by official place data.
    - User-provided: Explicitly set by the traveler.
    - Estimated: Standard rates (transport per km, meals, accommodation).
    - Unknown: Missing entrance fees estimated conservatively (never assumed to be zero).
    """
    travelers_count = max(1, travelers_count)
    total_days = max(1, total_days)

    verified_cost = 0.0
    user_provided_cost = 0.0
    estimated_cost = 0.0
    unknown_cost = 0.0
    unknown_prices_count = 0

    total_entrance_fees = 0.0
    notes: List[str] = []

    # 1. Attraction Entrance Fees Calculation
    for stop in stops_data:
        # Ignore starting/ending hotel checkpoints
        if stop.get("is_start_location") or stop.get("is_end_location"):
            continue

        fee_val = stop.get("entrance_fee")
        is_verified = bool(stop.get("is_fee_verified", False))
        is_user_provided = bool(stop.get("is_user_provided", False))

        if fee_val is not None:
            fee_per_person = float(fee_val)
            fee_total_stop = fee_per_person * travelers_count
            total_entrance_fees += fee_total_stop

            if is_verified:
                verified_cost += fee_total_stop
            elif is_user_provided:
                user_provided_cost += fee_total_stop
            else:
                estimated_cost += fee_total_stop
        else:
            # Crucial: Do not assume missing prices are zero!
            fee_per_person = DEFAULT_ESTIMATED_ENTRANCE_FEE
            fee_total_stop = fee_per_person * travelers_count
            total_entrance_fees += fee_total_stop
            unknown_cost += fee_total_stop
            unknown_prices_count += 1

            stop_name = stop.get("name", "Unknown Attraction")
            notes.append(
                f"Entrance fee for '{stop_name}' is unverified; applied conservative placeholder of ₹{fee_per_person:.0f}/person."
            )

    # 2. Transportation Expenses Calculation
    rate_per_km = TRANSPORT_RATES.get(transportation, TRANSPORT_RATES["driving-car"])
    transport_total = round(total_distance_km * rate_per_km, 2)
    estimated_cost += transport_total

    # 3. Food & Dining Expenses Calculation
    daily_meal_rate = MEAL_TIER_RATES.get(dietary_budget_tier, MEAL_TIER_RATES["moderate"])
    food_total = round(daily_meal_rate * travelers_count * total_days, 2)
    estimated_cost += food_total

    # 4. Accommodation Expenses Calculation (when requested)
    accommodation_total = 0.0
    if include_accommodation and total_days > 1:
        nights = total_days - 1
        rooms_needed = math.ceil(travelers_count / 2.0)
        nightly_room_rate = ACCOMMODATION_RATES.get(accommodation_type, ACCOMMODATION_RATES["standard"])
        accommodation_total = round(nights * rooms_needed * nightly_room_rate, 2)
        estimated_cost += accommodation_total
        notes.append(
            f"Included {accommodation_type} accommodation: {nights} night(s) × {rooms_needed} room(s) @ ₹{nightly_room_rate}/night."
        )

    # 5. Contingency Buffer Calculation
    base_subtotal = transport_total + total_entrance_fees + food_total + accommodation_total
    contingency_buffer = round(base_subtotal * CONTINGENCY_PERCENTAGE, 2)
    estimated_cost += contingency_buffer

    # Overall Totals
    estimated_total_cost = round(base_subtotal + contingency_buffer, 2)
    cost_per_traveler = round(estimated_total_cost / travelers_count, 2)
    remaining_budget = round(total_budget - estimated_total_cost, 2)
    budget_overrun = round(max(0.0, estimated_total_cost - total_budget), 2)
    is_budget_exceeded = estimated_total_cost > total_budget

    if is_budget_exceeded:
        notes.append(
            f"Budget exceeded by ₹{budget_overrun:.2f}. Total estimated cost (₹{estimated_total_cost:.2f}) "
            f"surpasses allocated budget of ₹{total_budget:.2f}."
        )

    by_provenance = PriceCategoryBreakdown(
        verified=round(verified_cost, 2),
        user_provided=round(user_provided_cost, 2),
        estimated=round(estimated_cost, 2),
        unknown=round(unknown_cost, 2),
    )

    by_category = ExpenseCategoryBreakdown(
        transportation=round(transport_total, 2),
        entrance_fees=round(total_entrance_fees, 2),
        food=round(food_total, 2),
        accommodation=round(accommodation_total, 2),
        contingency_buffer=round(contingency_buffer, 2),
    )

    return BudgetCalculationResult(
        total_budget=round(total_budget, 2),
        estimated_total_cost=estimated_total_cost,
        cost_per_traveler=cost_per_traveler,
        remaining_budget=remaining_budget,
        budget_overrun=budget_overrun,
        is_budget_exceeded=is_budget_exceeded,
        unknown_prices_count=unknown_prices_count,
        has_unknown_expenses=unknown_prices_count > 0,
        by_provenance=by_provenance,
        by_category=by_category,
        budget_notes=notes,
    )

