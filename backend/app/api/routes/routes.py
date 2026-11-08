from fastapi import APIRouter, status

try:
    from app.schemas.external import RouteCalculationRequest, RouteCalculationResponse
    from app.schemas.clustering_and_routing import (
        RouteOptimizationRequest,
        RouteOptimizationResponse,
    )
    from app.services.ors_service import ors_service
    from app.services.optimization_service import optimization_service
except ImportError:
    from backend.app.schemas.external import RouteCalculationRequest, RouteCalculationResponse
    from backend.app.schemas.clustering_and_routing import (
        RouteOptimizationRequest,
        RouteOptimizationResponse,
    )
    from backend.app.services.ors_service import ors_service
    from backend.app.services.optimization_service import optimization_service

router = APIRouter(prefix="/routes", tags=["Routing & Navigation"])


@router.post(
    "/calculate",
    response_model=RouteCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate road route, distance, travel duration, and path geometry",
    description="Calculates turn-by-turn road distance, estimated travel duration, and polyline coordinates between waypoints using OpenRouteService with automated fallback simulation.",
)
async def calculate_route(
    payload: RouteCalculationRequest,
) -> RouteCalculationResponse:
    return await ors_service.calculate_route(
        coordinates=payload.coordinates,
        profile=payload.profile,
    )


@router.post(
    "/optimize",
    response_model=RouteOptimizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Optimize visiting sequence and generate daily itineraries",
    description=(
        "Optimizes tourist visiting sequence using Nearest-Neighbor initialization and 2-Opt TSP local search. "
        "Partitions attractions into daily schedules respecting time limits, computes arrival/departure times, "
        "calculates total road distances, and quantifies percentage improvement over naive sequences."
    ),
)
async def optimize_route(
    payload: RouteOptimizationRequest,
) -> RouteOptimizationResponse:
    return await optimization_service.optimize_routes(payload)

