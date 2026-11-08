import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ScoringWeights:
    """Configurable weights for multi-criteria context-aware POI scoring.
    
    Default weights sum to 1.00:
    Preference = 0.30
    Distance   = 0.15
    Time       = 0.15
    Weather    = 0.15
    Category   = 0.15
    Budget     = 0.10
    """
    preference: float = 0.30
    distance: float = 0.15
    time: float = 0.15
    weather: float = 0.15
    category: float = 0.15
    budget: float = 0.10

    def normalized(self) -> "ScoringWeights":
        """Return a new ScoringWeights instance with weights strictly summing to 1.0."""
        total = (
            abs(self.preference)
            + abs(self.distance)
            + abs(self.time)
            + abs(self.weather)
            + abs(self.category)
            + abs(self.budget)
        )
        if total <= 0:
            raise ValueError("Sum of weights must be greater than zero")
        return ScoringWeights(
            preference=abs(self.preference) / total,
            distance=abs(self.distance) / total,
            time=abs(self.time) / total,
            weather=abs(self.weather) / total,
            category=abs(self.category) / total,
            budget=abs(self.budget) / total,
        )

    def to_dict(self) -> Dict[str, float]:
        norm = self.normalized()
        return {
            "preference": round(norm.preference, 4),
            "distance": round(norm.distance, 4),
            "time": round(norm.time, 4),
            "weather": round(norm.weather, 4),
            "category": round(norm.category, 4),
            "budget": round(norm.budget, 4),
        }


# Semantic vocabulary mapping user interests to domain keywords & tags
INTEREST_SYNONYMS: Dict[str, Set[str]] = {
    "historical places": {
        "history", "historic", "heritage", "monument", "fort", "castle",
        "palace", "ruins", "memorial", "tomb", "archaeological", "landmark",
        "ancient", "unesco", "temple", "mosque", "church", "cathedral",
    },
    "history": {
        "history", "historic", "heritage", "monument", "fort", "palace",
        "memorial", "ancient", "museum", "archaeological",
    },
    "culture": {
        "culture", "cultural", "museum", "art", "gallery", "theatre",
        "monument", "heritage", "temple", "craft", "exhibition",
    },
    "food": {
        "food", "restaurant", "catering", "cafe", "dining", "cuisine",
        "bistro", "bakery", "street_food", "eatery", "fast_food", "tea", "coffee",
    },
    "photography": {
        "viewpoint", "view", "panoramic", "scenic", "landscape", "monument",
        "architecture", "park", "garden", "lake", "waterfront", "skyline",
        "nature", "waterfall", "sunset", "heritage",
    },
    "nature": {
        "nature", "park", "garden", "lake", "forest", "waterfall", "wildlife",
        "zoo", "botanical", "river", "mountain", "beach", "natural",
    },
    "adventure": {
        "adventure", "hiking", "trekking", "climbing", "safari", "rafting",
        "camp", "outdoor", "sports", "trail",
    },
    "shopping": {
        "shopping", "market", "bazaar", "mall", "store", "craft", "souvenir",
    },
    "nightlife": {
        "nightlife", "bar", "pub", "club", "lounge", "live_music",
    },
    "relaxation": {
        "spa", "wellness", "resort", "park", "garden", "beach", "lake",
    },
}

# Categories classified as inherently outdoor or indoor
OUTDOOR_KEYWORDS = {
    "viewpoint", "park", "garden", "nature", "lake", "waterfall", "hiking",
    "outdoor", "beach", "trail", "zoo", "safari", "ruins", "fort", "monument",
}
INDOOR_KEYWORDS = {
    "museum", "gallery", "art", "theatre", "restaurant", "cafe", "bistro",
    "shopping", "mall", "palace", "temple", "indoor", "cinema", "exhibition",
}


def _tokenize(text: str) -> Set[str]:
    """Tokenize and clean text into lowercase alphanumeric word tokens."""
    if not text:
        return set()
    cleaned = "".join(c.lower() if c.isalnum() else " " for c in text)
    return {w for w in cleaned.split() if len(w) > 2}


# ==============================================================================
# 1. PREFERENCE MATCHING SCORE (P)
# ==============================================================================
def calculate_preference_score(
    user_interests: List[str],
    place_categories: List[str],
    place_name: str = "",
    place_description: str = "",
) -> float:
    """Calculate the preference matching score P in [0.0, 1.0].
    
    Evaluates semantic overlap between user interest tags and POI metadata.
    """
    if not user_interests:
        return 0.5  # Neutral baseline when user provided no interests

    place_tokens = set()
    for cat in place_categories:
        place_tokens.update(_tokenize(cat.replace(".", " ").replace("_", " ")))
    place_tokens.update(_tokenize(place_name))
    place_tokens.update(_tokenize(place_description))

    if not place_tokens:
        return 0.3  # Minimal score if place has no descriptive metadata

    matches_count = 0
    total_interests = len(user_interests)

    for interest in user_interests:
        interest_lower = interest.strip().lower()
        interest_tokens = _tokenize(interest_lower)
        synonyms = INTEREST_SYNONYMS.get(interest_lower, interest_tokens)
        all_interest_terms = interest_tokens | synonyms

        # Check direct or synonym intersection
        overlap = all_interest_terms & place_tokens
        if overlap:
            matches_count += 1

    match_ratio = matches_count / total_interests

    # Scale score with a slight boost for top matches
    if match_ratio >= 1.0:
        return 1.0
    elif match_ratio >= 0.66:
        return 0.85
    elif match_ratio >= 0.33:
        return 0.65
    elif match_ratio > 0.0:
        return 0.45
    else:
        return 0.15


# ==============================================================================
# 2. DISTANCE SUITABILITY SCORE (D)
# ==============================================================================
def calculate_distance_score(
    distance_km: Optional[float],
    max_radius_km: float = 25.0,
) -> float:
    """Calculate distance suitability score D in [0.0, 1.0].
    
    Places closer to the origin/city center receive a higher score.
    Returns 0.5 if distance data is unavailable.
    """
    if distance_km is None:
        return 0.5

    if distance_km < 0.0:
        distance_km = 0.0

    if max_radius_km <= 0.0:
        max_radius_km = 25.0

    # Clamped linear distance decay
    score = 1.0 - (distance_km / max_radius_km)
    return round(max(0.0, min(1.0, score)), 4)


# ==============================================================================
# 3. TEMPORAL FEASIBILITY SCORE (T)
# ==============================================================================
def calculate_time_score(
    visit_duration_mins: Optional[int],
    daily_available_hours: float = 8.0,
    opening_hours: Optional[str] = None,
    proposed_visit_hour: Optional[int] = None,
) -> float:
    """Calculate temporal feasibility score T in [0.0, 1.0].
    
    Scores how well the estimated visit duration fits into the traveler's daily schedule.
    Handles verified opening hours if provided.
    """
    # 1. Opening hours check
    if opening_hours and proposed_visit_hour is not None:
        # If explicitly known closed, severe penalty
        closed_keywords = ["closed", "permanently closed"]
        if any(w in opening_hours.lower() for w in closed_keywords):
            return 0.0

    if visit_duration_mins is None:
        return 0.5  # Neutral when duration is unrecorded

    if visit_duration_mins <= 0:
        visit_duration_mins = 60

    available_mins = max(daily_available_hours * 60.0, 60.0)

    # Ideal single attraction duration is between 45 and 150 minutes
    if 45 <= visit_duration_mins <= 150:
        base_score = 0.95
    elif visit_duration_mins < 45:
        base_score = 0.80  # Quick stop
    elif visit_duration_mins <= 240:
        base_score = 0.70  # Half-day activity
    elif visit_duration_mins <= available_mins:
        base_score = 0.50  # Consumes entire day
    else:
        # Exceeds daily available time
        ratio = available_mins / float(visit_duration_mins)
        base_score = max(0.10, ratio * 0.40)

    return round(base_score, 4)


# ==============================================================================
# 4. WEATHER SUITABILITY SCORE (W)
# ==============================================================================
def calculate_weather_score(
    weather_code: Optional[int],
    precipitation_mm: Optional[float],
    place_categories: List[str],
    max_temp_celsius: Optional[float] = None,
) -> float:
    """Calculate weather suitability score W in [0.0, 1.0].
    
    Differentiates between outdoor weather-sensitive places and indoor weather-resilient venues.
    """
    if weather_code is None and precipitation_mm is None:
        return 0.5  # Neutral when weather data is unavailable

    # Determine venue type
    cat_text = " ".join(place_categories).lower()
    is_outdoor = any(w in cat_text for w in OUTDOOR_KEYWORDS)
    is_indoor = any(w in cat_text for w in INDOOR_KEYWORDS)

    # Precipitation indicator
    is_raining = (precipitation_mm is not None and precipitation_mm > 0.5) or (
        weather_code is not None and (50 <= weather_code <= 67 or 80 <= weather_code <= 99)
    )
    is_severe = weather_code is not None and (weather_code >= 95 or weather_code in (65, 67, 75, 82))
    is_clear = weather_code is not None and weather_code in (0, 1, 2)

    # Extreme heat check
    is_extreme_heat = max_temp_celsius is not None and max_temp_celsius > 38.0

    if is_severe:
        return 0.85 if is_indoor else 0.15

    if is_raining:
        if is_indoor:
            # Rainy days favor museums, galleries, cafes
            return 0.95
        elif is_outdoor:
            return 0.25
        else:
            return 0.50

    if is_extreme_heat:
        return 0.90 if is_indoor else 0.40

    if is_clear:
        if is_outdoor:
            return 1.0
        else:
            return 0.80

    # Mild/overcast default
    return 0.75


# ==============================================================================
# 5. BUDGET SUITABILITY SCORE (B)
# ==============================================================================
def calculate_budget_score(
    entrance_fee: Optional[float],
    user_budget: Optional[float],
    total_trip_days: int = 1,
) -> float:
    """Calculate budget suitability score B in [0.0, 1.0].
    
    Evaluates entrance fee against traveler's total or daily budget.
    Does not invent fees if missing.
    """
    if entrance_fee is None or user_budget is None:
        return 0.5  # Neutral when financial data is missing

    if entrance_fee <= 0.0:
        return 1.0  # Free attractions have maximum budget suitability

    if user_budget <= 0.0:
        return 0.2  # Zero budget for paid place

    # Normalize by daily budget capacity
    days = max(total_trip_days, 1)
    daily_budget = user_budget / float(days)

    fee_ratio = entrance_fee / daily_budget

    if fee_ratio <= 0.10:
        return 0.95
    elif fee_ratio <= 0.25:
        return 0.85
    elif fee_ratio <= 0.50:
        return 0.70
    elif fee_ratio <= 1.0:
        return 0.50
    elif entrance_fee <= user_budget:
        return 0.30
    else:
        # Exceeds total trip budget
        return 0.05


# ==============================================================================
# 6. CATEGORY COMPATIBILITY SCORE (C)
# ==============================================================================
def calculate_category_score(
    place_categories: List[str],
    target_categories: Optional[List[str]] = None,
    already_selected_categories: Optional[List[str]] = None,
) -> float:
    """Calculate category compatibility score C in [0.0, 1.0].
    
    Balances target theme affinity and diversity across the itinerary.
    """
    if not target_categories and not already_selected_categories:
        return 0.70  # Standard healthy baseline

    score = 0.60

    # 1. Target category affinity
    if target_categories:
        target_tokens = set()
        for tc in target_categories:
            tc_clean = tc.lower().strip()
            target_tokens.update(_tokenize(tc_clean))
            target_tokens.update(INTEREST_SYNONYMS.get(tc_clean, set()))

        place_tokens = set()
        for pc in place_categories:
            place_tokens.update(_tokenize(pc.replace(".", " ").replace("_", " ")))

        if target_tokens & place_tokens:
            score += 0.30
        else:
            score -= 0.10

    # 2. Diversity penalty if category is already heavily represented
    if already_selected_categories:
        cat_matches = sum(
            1 for c in place_categories if any(sc in c for sc in already_selected_categories)
        )
        if cat_matches > 3:
            score -= 0.15

    return round(max(0.10, min(1.0, score)), 4)


# ==============================================================================
# 7. FINAL MULTI-CRITERIA SCORING & BASELINE
# ==============================================================================
def calculate_final_score(
    factor_scores: Dict[str, float],
    weights: Optional[ScoringWeights] = None,
) -> float:
    """Compute the multi-criteria composite score R(p_i) = sum(w_k * x_ik).
    
    Guarantees result is strictly bounded in [0.0, 1.0].
    """
    w = (weights or ScoringWeights()).normalized()

    composite = (
        w.preference * factor_scores.get("preference", 0.5)
        + w.distance * factor_scores.get("distance", 0.5)
        + w.time * factor_scores.get("time", 0.5)
        + w.weather * factor_scores.get("weather", 0.5)
        + w.category * factor_scores.get("category", 0.5)
        + w.budget * factor_scores.get("budget", 0.5)
    )

    return round(max(0.0, min(1.0, composite)), 4)


def calculate_baseline_score(preference_score: float) -> float:
    """Compute baseline recommendation score (pure preference matching).
    
    Used for academic and empirical performance comparison against the context-aware model.
    """
    return round(max(0.0, min(1.0, preference_score)), 4)


# ==============================================================================
# 8. EXPLANATION GENERATOR
# ==============================================================================
def generate_recommendation_explanation(
    place_name: str,
    factor_scores: Dict[str, float],
    user_interests: List[str],
) -> str:
    """Generate dynamic, explainable recommendation justification."""
    p_score = factor_scores.get("preference", 0.5)
    d_score = factor_scores.get("distance", 0.5)
    t_score = factor_scores.get("time", 0.5)
    w_score = factor_scores.get("weather", 0.5)
    b_score = factor_scores.get("budget", 0.5)

    reasons: List[str] = []

    # Preference factor
    if p_score >= 0.70 and user_interests:
        interests_str = ", ".join(user_interests[:2]).lower()
        reasons.append(f"matches your interest in {interests_str}")
    elif p_score >= 0.50 and user_interests:
        reasons.append("partially aligns with your travel interests")

    # Time factor
    if t_score >= 0.85:
        reasons.append("fits your available travel schedule")

    # Weather factor
    if w_score >= 0.85:
        reasons.append("is well-suited for current weather conditions")

    # Distance factor
    if d_score >= 0.80:
        reasons.append("is conveniently located near your destination area")

    # Budget factor
    if b_score >= 0.90:
        reasons.append("is cost-effective for your budget")

    if not reasons:
        reasons.append("offers a balanced experience across travel time, weather, and proximity")

    # Format into complete sentence
    if len(reasons) == 1:
        justification = reasons[0]
    else:
        justification = f"{reasons[0]} and {reasons[1]}"

    return f"{place_name} was recommended because it {justification}."


# ==============================================================================
# 9. RANKING & TIE-BREAKING
# ==============================================================================
def rank_recommendations(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort candidates descending by final_score with multi-tier tie-breaking.
    
    Tie-breaking hierarchy:
    1. final_score (descending)
    2. preference score (descending)
    3. distance score (descending)
    """
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (
            item.get("final_score", 0.0),
            item.get("factor_scores", {}).get("preference", 0.0),
            item.get("factor_scores", {}).get("distance", 0.0),
        ),
        reverse=True,
    )

    for rank_idx, item in enumerate(sorted_candidates, start=1):
        item["rank"] = rank_idx

    return sorted_candidates
