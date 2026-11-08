from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserPreferenceBase(BaseModel):
    preferred_categories: Optional[str] = None
    preferred_activities: Optional[str] = None
    preferred_transport: Optional[str] = None
    preferred_budget: Optional[str] = None
    preferred_travel_style: Optional[str] = None


class UserPreferenceCreate(UserPreferenceBase):
    pass


class UserPreferenceUpdate(BaseModel):
    preferred_categories: Optional[str] = None
    preferred_activities: Optional[str] = None
    preferred_transport: Optional[str] = None
    preferred_budget: Optional[str] = None
    preferred_travel_style: Optional[str] = None


class UserPreferenceResponse(UserPreferenceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

