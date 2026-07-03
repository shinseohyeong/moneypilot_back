from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=2, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    profile_image_url: Optional[str]
    login_type: str
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}