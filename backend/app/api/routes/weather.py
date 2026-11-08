from datetime import date
from typing import Optional
from fastapi import APIRouter, Query, status

try:
    from app.schemas.external import WeatherForecastResponse
    from app.services.weather_service import weather_service
except ImportError:
    from backend.app.schemas.external import WeatherForecastResponse
    from backend.app.services.weather_service import weather_service

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get(
    "/forecast",
    response_model=WeatherForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve weather forecast for geographic coordinates",
    description="Retrieves current conditions, temperature ranges, precipitation probabilities, and daily outlook using Open-Meteo API.",
)
async def get_weather_forecast(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Latitude (-90 to 90)"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Longitude (-180 to 180)"),
    start_date: Optional[date] = Query(
        default=None,
        description="Optional start date for targeted forecast window (YYYY-MM-DD)",
    ),
    end_date: Optional[date] = Query(
        default=None,
        description="Optional end date for targeted forecast window (YYYY-MM-DD)",
    ),
) -> WeatherForecastResponse:
    return await weather_service.get_forecast(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
    )

