from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.api.dependencies import get_optional_current_user
    from app.database.connection import get_db
    from app.models.user import User
    from app.schemas.itinerary import (
        ItineraryGenerateRequest,
        ItineraryResponse,
        ItineraryValidateRequest,
        ItineraryValidationResponse,
    )
    from app.services.itinerary_service import itinerary_service
except ImportError:
    from backend.app.api.dependencies import get_optional_current_user
    from backend.app.database.connection import get_db
    from backend.app.models.user import User
    from backend.app.schemas.itinerary import (
        ItineraryGenerateRequest,
        ItineraryResponse,
        ItineraryValidateRequest,
        ItineraryValidationResponse,
    )
    from backend.app.services.itinerary_service import itinerary_service

router = APIRouter(prefix="/itinerary", tags=["Itinerary Generation & Budget Management"])


@router.post(
    "/generate",
    response_model=ItineraryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate personalized, multi-day travel itinerary with budget management",
    description=(
        "Synthesizes recommendation scoring, geographic clustering, 2-Opt route optimization, "
        "real-time weather adaptations, and comprehensive budget calculation to generate an optimal, "
        "constraint-checked multi-day travel schedule with arrival/departure times and meal breaks."
    ),
)
async def generate_itinerary(
    payload: ItineraryGenerateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ItineraryResponse:
    """Generate an itinerary based on user preferences and constraints."""
    user_id = current_user.id if current_user else None
    return await itinerary_service.generate_itinerary(
        request=payload,
        db=db,
        user_id=user_id,
    )


@router.get(
    "/{itinerary_id}",
    response_model=ItineraryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve previously generated itinerary by ID",
    description="Fetches an itinerary by its unique identifier from the persistence store.",
)
def get_itinerary(
    itinerary_id: str,
) -> ItineraryResponse:
    """Retrieve itinerary details."""
    itin = itinerary_service.get_itinerary(itinerary_id)
    if not itin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Itinerary with ID '{itinerary_id}' was not found.",
        )
    return itin


@router.post(
    "/validate",
    response_model=ItineraryValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate feasibility and constraint compliance of an itinerary",
    description=(
        "Performs constraint checking on an existing or proposed itinerary: chronological non-overlaps, "
        "venue opening hours adherence, daily touring hours limits, and budget overrun detection."
    ),
)
def validate_itinerary(
    payload: ItineraryValidateRequest,
) -> ItineraryValidationResponse:
    """Validate feasibility of an itinerary plan."""
    return itinerary_service.validate_existing_itinerary(payload)

