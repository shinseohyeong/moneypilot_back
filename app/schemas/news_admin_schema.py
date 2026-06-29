# 파일 경로 : app/schemas/news_admin_schema.py
# 파일 역할 : 
            # - 관리자 뉴스 수집 설정/로그 요청·응답 schema

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class NewsCollectionSettingCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    provider: str = Field(default="NAVER", max_length=50)
    interval_minutes: int = Field(default=60, ge=1)
    display_count: int = Field(default=10, ge=1, le=100)
    sort: str = Field(default="date", max_length=20)
    is_active: bool = True


class NewsCollectionSettingUpdate(BaseModel):
    keyword: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    provider: Optional[str] = Field(default=None, max_length=50)
    interval_minutes: Optional[int] = Field(default=None, ge=1)
    display_count: Optional[int] = Field(default=None, ge=1, le=100)
    sort: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None


class NewsCollectionSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str
    category: Optional[str]
    provider: str
    interval_minutes: int
    display_count: int
    sort: str
    is_active: bool
    last_collected_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class NewsCollectionSettingListResponse(BaseModel):
    total_count: int
    items: List[NewsCollectionSettingResponse]


class NewsCollectionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    setting_id: Optional[int]
    keyword: str
    provider: str
    status: str
    requested_count: int
    saved_count: int
    duplicated_count: int
    error_message: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]
    created_at: Optional[datetime]


class NewsCollectionLogListResponse(BaseModel):
    total_count: int
    items: List[NewsCollectionLogResponse]