from fastapi import APIRouter, status

try:
    from app.schemas.health import HealthResponse
except ImportError:
    from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Health Check",
    description="Returns the operational status of the TravelSenseAI backend service.",
)
async def check_health() -> HealthResponse:
    """Return backend service status."""
    return HealthResponse(
        status="success",
        message="TravelSenseAI backend is running",
    )

