# ============================================================
# 파일 위치: app/schemas/news_sentiment_schema.py
# 역할:
#   - 뉴스 감정분석 API의 요청/응답 schema를 정의합니다.
#   - 실제 감정값은 news_summaries.sentiment 값을 활용합니다.
# ============================================================

from typing import List, Optional

from pydantic import BaseModel, Field


class NewsSentimentAnalyzeRequest(BaseModel):
    # True면 기존 요약/감정분석 결과가 있어도 LLM으로 다시 생성합니다.
    force_refresh: bool = False


class NewsSentimentResponse(BaseModel):
    news_id: int
    summary_id: int

    sentiment: str
    sentiment_label: str

    one_line_summary: Optional[str] = None
    positive_factors: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)

    investment_note: Optional[str] = None
    model_name: Optional[str] = None
    disclaimer: str