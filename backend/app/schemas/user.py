from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

try:
    from app.schemas.preferences import UserPreferenceResponse, UserPreferenceUpdate
except ImportError:
    from backend.app.schemas.preferences import UserPreferenceResponse, UserPreferenceUpdate


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=100, description="Password with minimum 6 characters")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    preferences: Optional[UserPreferenceUpdate] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    preferences: Optional[UserPreferenceResponse] = None

    model_config = ConfigDict(from_attributes=True)

