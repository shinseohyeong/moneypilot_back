from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    phone: Optional[str]
    login_type: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}