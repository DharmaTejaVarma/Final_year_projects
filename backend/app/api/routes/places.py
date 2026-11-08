from typing import Optional
from fastapi import APIRouter, Path, Query, status

try:
    from app.schemas.external import PlaceDetailsResponse, PlacesSearchResponse
    from app.services.geoapify_service import geoapify_service
except ImportError:
    from backend.app.schemas.external import PlaceDetailsResponse, PlacesSearchResponse
    from backend.app.services.geoapify_service import geoapify_service

router = APIRouter(prefix="/places", tags=["Places & Attractions"])


@router.get(
    "/search",
    response_model=PlacesSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search places, tourist attractions, and restaurants",
    description="Discovers points of interest around geographic coordinates using Geoapify Places API with category filtering and deduplication.",
)
async def search_places(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Center latitude (-90 to 90)"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Center longitude (-180 to 180)"),
    radius: int = Query(default=5000, ge=500, le=50000, description="Search radius in meters (500 to 50,000)"),
    type: Optional[str] = Query(
        default=None,
        description="Shortcut type filter: 'attraction' (sights, landmarks), 'restaurant' (dining, cafes), or leave empty for general attractions.",
    ),
    categories: Optional[str] = Query(
        default=None,
        description="Custom comma-separated Geoapify category IDs (e.g., 'tourism.attraction,catering.restaurant')",
    ),
    query: Optional[str] = Query(
        default=None,
        description="Optional name/keyword filter within the area",
    ),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of items to return"),
) -> PlacesSearchResponse:
    # Resolve category filters
    resolved_categories = categories
    if not resolved_categories:
        if type == "restaurant":
            resolved_categories = "catering.restaurant,catering.cafe"
        elif type == "attraction":
            resolved_categories = "tourism.attraction,tourism.sights,entertainment.museum,heritage"
        else:
            resolved_categories = "tourism.attraction,tourism.sights,entertainment.museum,heritage"

    places, source = await geoapify_service.search_places(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius,
        categories=resolved_categories,
        query=query,
        limit=limit,
    )

    return PlacesSearchResponse(
        total=len(places),
        source=source,
        center={"latitude": latitude, "longitude": longitude},
        radius_meters=radius,
        places=places,
    )


@router.get(
    "/{place_id}",
    response_model=PlaceDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve detailed information for a specific place",
    description="Fetches full metadata, contact information, hours, and attributes for a Geoapify place identifier.",
)
async def get_place_details(
    place_id: str = Path(..., min_length=1, description="Geoapify place identifier"),
) -> PlaceDetailsResponse:
    place_item, raw_feature, source = await geoapify_service.get_place_details(place_id=place_id)
    return PlaceDetailsResponse(
        place=place_item,
        source=source,
        raw_details=raw_feature.get("properties"),
    )

