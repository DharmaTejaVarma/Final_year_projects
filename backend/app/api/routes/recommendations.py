from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

try:
    from app.database.connection import get_db
    from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
    from app.services.recommendation_service import recommendation_service
except ImportError:
    from backend.app.database.connection import get_db
    from backend.app.schemas.recommendation import RecommendationRequest, RecommendationResponse
    from backend.app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["Recommendation Engine"])


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate context-aware POI recommendations",
    description="Scores and ranks tourist attractions using 6 normalized dimensions: Preference (P), Distance (D), Time (T), Weather (W), Category (C), and Budget (B). Includes transparent factor breakdowns, baseline comparisons, and dynamic explanations.",
)
async def generate_recommendations(
    payload: RecommendationRequest,
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    return await recommendation_service.get_recommendations(
        request=payload,
        db=db,
    )

