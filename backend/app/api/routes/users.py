from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

try:
    from app.api.dependencies import get_current_active_user
    from app.core.logger import logger
    from app.database.connection import get_db
    from app.models.user import User, UserPreference
    from app.schemas.user import UserResponse, UserUpdate
except ImportError:
    from backend.app.api.dependencies import get_current_active_user
    from backend.app.core.logger import logger
    from backend.app.database.connection import get_db
    from backend.app.models.user import User, UserPreference
    from backend.app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user profile",
    description="Returns detailed profile information and travel preferences for the currently authenticated user.",
)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put(
    "/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update authenticated user profile",
    description="Updates user profile attributes (such as full name) and travel preferences.",
)
async def update_user_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    # Update user basic profile attributes
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()

    # Update or create user preferences
    if payload.preferences is not None:
        if current_user.preferences is None:
            current_user.preferences = UserPreference(user_id=current_user.id)
            db.add(current_user.preferences)

        pref_data = payload.preferences.model_dump(exclude_unset=True)
        for key, value in pref_data.items():
            setattr(current_user.preferences, key, value)

    db.commit()
    db.refresh(current_user)

    logger.info(f"User profile updated: id={current_user.id}")
    return UserResponse.model_validate(current_user)

