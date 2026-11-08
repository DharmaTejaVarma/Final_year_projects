from typing import Any, Dict, List, Optional, Tuple

OUTDOOR_KEYWORDS = {
    "fort",
    "garden",
    "park",
    "zoo",
    "monument",
    "lake",
    "ruins",
    "beach",
    "hiking",
    "viewpoint",
    "outdoor",
    "waterfall",
    "safari",
    "tomb",
    "amusement_park",
    "nature_reserve",
    "botanical_garden",
}

INDOOR_KEYWORDS = {
    "museum",
    "gallery",
    "palace",
    "mall",
    "shopping",
    "theatre",
    "cinema",
    "aquarium",
    "cultural_centre",
    "indoor",
    "planetarium",
    "science_centre",
    "art_centre",
    "library",
}

# Weather codes from Open-Meteo corresponding to precipitation or severe conditions
RAIN_WEATHER_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}
SNOW_WEATHER_CODES = {71, 73, 75, 77, 85, 86}
STORM_WEATHER_CODES = {95, 96, 99}


def is_outdoor_venue(
    category: Optional[str] = None,
    name: Optional[str] = None,
    explicit_flag: Optional[bool] = None,
) -> bool:
    """Determine whether a tourist attraction is predominantly outdoors and weather-sensitive."""
    if explicit_flag is not None:
        return explicit_flag

    text = f"{name or ''} {category or ''}".lower()

    # Check indoor indicators first
    for indoor_kw in INDOOR_KEYWORDS:
        if indoor_kw in text:
            return False

    # Check outdoor indicators
    for outdoor_kw in OUTDOOR_KEYWORDS:
        if outdoor_kw in text:
            return True

    # Default to True for heritage/tourism sights unless classified indoor
    return True


def evaluate_daily_weather_favorability(
    weather_data: Optional[Dict[str, Any]],
) -> Tuple[bool, float, str]:
    """Evaluate whether forecast conditions on a specific travel day are favorable for outdoor touring.

    Returns:
        (is_favorable, suitability_multiplier, condition_summary)
    """
    if not weather_data:
        return True, 1.0, "Weather forecast unavailable; assuming normal conditions."

    precip_mm = float(weather_data.get("precipitation_mm", 0.0) or 0.0)
    wcode = int(weather_data.get("weather_code", 0) or 0)
    wind_kmh = float(weather_data.get("wind_speed_kmh", 0.0) or 0.0)
    temp_c = weather_data.get("temperature_celsius")

    # Severe Thunderstorm
    if wcode in STORM_WEATHER_CODES or precip_mm >= 10.0:
        return (
            False,
            0.30,
            f"Severe thunderstorms / torrential rainfall forecasted (precipitation: {precip_mm}mm).",
        )

    # Moderate to Heavy Rain
    if wcode in RAIN_WEATHER_CODES or precip_mm >= 2.0:
        return (
            False,
            0.50,
            f"Precipitation forecasted ({precip_mm}mm, weather code {wcode}). Rain expected.",
        )

    # Snowfall
    if wcode in SNOW_WEATHER_CODES:
        return (
            False,
            0.55,
            f"Snowfall / freezing precipitation forecasted ({precip_mm}mm).",
        )

    # High Gale Winds
    if wind_kmh >= 45.0:
        return (
            False,
            0.70,
            f"High winds forecasted ({wind_kmh} km/h). Outdoor walking may be impeded.",
        )

    # Extreme Heat
    if temp_c is not None and float(temp_c) >= 42.0:
        return (
            False,
            0.60,
            f"Extreme heat alert ({temp_c}°C). Midday outdoor touring carries heat exhaustion risk.",
        )

    return True, 1.0, "Weather conditions favorable for outdoor tourism."


def adjust_attraction_weather(
    poi_name: str,
    category: Optional[str],
    is_outdoor: bool,
    weather_data: Optional[Dict[str, Any]],
    available_indoor_alternatives: Optional[List[str]] = None,
) -> Tuple[float, Optional[str], Optional[str]]:
    """Adjust individual attraction suitability based on weather and suggest indoor alternatives.

    Crucial principle: NEVER silently override or delete user-selected attractions.
    Instead, adjust the score component, attach an explicit warning, and recommend indoor alternatives.

    Returns:
        (weather_suitability_score, weather_warning, indoor_alternative_suggested)
    """
    is_favorable, multiplier, summary = evaluate_daily_weather_favorability(weather_data)

    if not is_outdoor:
        # Indoor venues remain fully suitable regardless of rain
        return 1.0, None, None

    if is_favorable:
        return 1.0, None, None

    # Outdoor venue during unfavorable weather
    suitability_score = round(multiplier, 2)
    warning = (
        f"Unfavorable weather on this date: {summary} "
        f"Outdoor exploration at '{poi_name}' is retained per your preferences, but indoor alternatives are recommended."
    )

    suggested_alternative: Optional[str] = None
    if available_indoor_alternatives:
        suggested_alternative = available_indoor_alternatives[0]

    return suitability_score, warning, suggested_alternative

