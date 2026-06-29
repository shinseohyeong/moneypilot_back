# ============================================================
# 파일 위치: app/schemas/news_sector_schema.py
# 역할:
#   - 뉴스 산업/테마 분류 API의 응답 schema를 정의합니다.
# ============================================================

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class NewsSectorItemResponse(BaseModel):
    sector_id: int
    sector_name: str
    risk_level: Optional[str] = None
    matched_keywords: List[str] = []
    relevance_score: Optional[str] = None
    created_at: Optional[datetime] = None


class NewsSectorClassifyResponse(BaseModel):
    news_id: int
    matched_count: int
    items: List[NewsSectorItemResponse]


class NewsSectorListResponse(BaseModel):
    news_id: int
    total_count: int
    items: List[NewsSectorItemResponse]