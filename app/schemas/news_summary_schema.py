# ============================================================
# 파일 위치: app/schemas/news_summary_schema.py
# 역할:
#   - 뉴스 요약 생성 요청/응답 데이터 형태를 정의합니다.
#   - API 응답 필드는 snake_case를 사용합니다.
# ============================================================

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NewsSummaryCreateRequest(BaseModel):
    """
    뉴스 요약 생성 요청 schema

    force_refresh:
    - False: 이미 요약이 있으면 기존 요약 반환
    - True: 기존 요약이 있어도 LLM으로 다시 생성
    """

    force_refresh: bool = Field(default=False)


class NewsSummaryResponse(BaseModel):
    """
    뉴스 요약 응답 schema
    """

    summary_id: int
    news_id: int

    one_line_summary: Optional[str] = None
    summary_text: Optional[str] = None

    positive_factors: List[str] = []
    risk_factors: List[str] = []

    investment_note: Optional[str] = None
    sentiment: Optional[str] = None
    model_name: Optional[str] = None

    disclaimer: str

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None