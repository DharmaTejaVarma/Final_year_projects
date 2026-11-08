from typing import Optional
from fastapi import APIRouter, Query, status

try:
    from app.schemas.external import DestinationSearchResponse
    from app.services.geoapify_service import geoapify_service
except ImportError:
    from backend.app.schemas.external import DestinationSearchResponse
    from backend.app.services.geoapify_service import geoapify_service

router = APIRouter(prefix="/destinations", tags=["Destinations"])


@router.get(
    "/search",
    response_model=DestinationSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search destination coordinates and geocoding",
    description="Geocodes a destination name or query string using Geoapify API, returning coordinates, address details, and bounding boxes.",
)
async def search_destinations(
    q: str = Query(..., min_length=1, description="Destination query (e.g., 'Tokyo', 'Paris', 'Rome, Italy')"),
    limit: int = Query(default=5, ge=1, le=20, description="Maximum number of candidate destinations to return"),
) -> DestinationSearchResponse:
    results, source = await geoapify_service.search_destinations(query=q, limit=limit)
    return DestinationSearchResponse(
        query=q,
        total=len(results),
        source=source,
        results=results,
    )

