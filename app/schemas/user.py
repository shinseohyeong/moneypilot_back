"""
schemas/user.py — 사용자 프로필 요청/응답 스키마
팀 모델 기준: username, phone (nickname/profile_image_url 컬럼 없음)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserProfileUpdate(BaseModel):
    """내 정보 수정 (username, phone, password 중 전달된 것만)"""
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