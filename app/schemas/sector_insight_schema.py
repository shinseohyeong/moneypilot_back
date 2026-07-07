# ============================================================
# 파일 위치: app/schemas/sector_insight_schema.py
# 역할:
#   - 섹터 인사이트 생성/조회 API 응답 schema를 정의합니다.
# ============================================================

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class SectorInsightItemResponse(BaseModel):
    insight_id: int
    sector_id: int
    sector_name: str
    risk_level: Optional[str] = None

    insight_date: date
    period_days: int

    news_count: int
    positive_count: int
    neutral_count: int
    negative_count: int

    main_keywords: List[str] = []

    issue_score: Optional[str] = None
    insight_summary: Optional[str] = None
    risk_summary: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SectorInsightGenerateResponse(BaseModel):
    insight_date: date
    period_days: int
    generated_count: int
    items: List[SectorInsightItemResponse]


class SectorInsightListResponse(BaseModel):
    insight_date: date
    period_days: int
    total_count: int
    items: List[SectorInsightItemResponse]