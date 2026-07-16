# ============================================================
# 파일 위치: app/schemas/news_schema.py
# 역할:
#   - 뉴스 수집/조회 API의 요청/응답 형식을 정의합니다.
#   - API JSON 필드는 snake_case를 사용합니다.
# ============================================================

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NewsArticleResponse(BaseModel):
    """
    뉴스 기사 1건 응답 schema

    DB 모델 NewsArticle의 주요 필드를
    프론트에서 쓰기 좋게 내려줍니다.
    """

    news_id: int

    title: str
    description: Optional[str] = None
    content: Optional[str] = None

    original_link: Optional[str] = None
    api_link: Optional[str] = None

    source_name: Optional[str] = None
    provider: str
    search_keyword: Optional[str] = None

    published_at: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    is_active: bool


class StockNewsArticleResponse(NewsArticleResponse):
    """
    종목 뉴스 응답 schema

    종목 뉴스는 mapping 테이블 정보도 같이 내려줄 수 있습니다.
    """

    stock_id: int
    matched_keyword: Optional[str] = None
    relevance_score: Optional[str] = None


class NewsListResponse(BaseModel):
    """
    뉴스 목록 조회 응답 schema
    """

    total_count: int
    items: List[NewsArticleResponse]


class StockNewsListResponse(BaseModel):
    """
    종목 뉴스 목록 조회 응답 schema
    """

    stock_id: int
    total_count: int
    items: List[StockNewsArticleResponse]


class EconomyNewsCollectRequest(BaseModel):
    """
    경제 뉴스 수집 요청 schema

    query 기본값은 '경제'로 둡니다.
    나중에 '금리', '환율', '증시' 등으로 바꿔 수집할 수 있습니다.
    """

    query: str = Field(default="경제", min_length=1, max_length=100)
    display: int = Field(default=10, ge=1, le=100)
    sort: str = Field(default="date")
    days: int = Field(default=30, ge=1, le=90)


class StockNewsCollectRequest(BaseModel):
    """
    종목 뉴스 수집 요청 schema

    query가 없으면 service에서 '{stock_name} 주식'으로 자동 생성합니다.
    """

    query: Optional[str] = Field(default=None, max_length=100)
    display: int = Field(default=10, ge=1, le=100)
    sort: str = Field(default="date")
    days: int = Field(default=30, ge=1, le=90)


class NewsCollectResponse(BaseModel):
    """
    뉴스 수집 결과 응답 schema
    """

    query: str
    requested_count: int
    fetched_count: int

    # news_articles에 새로 저장된 기사 수
    saved_count: int

    # 이미 news_articles에 존재하던 기사 수
    duplicated_count: int

    # 종목 뉴스 수집 시 stock_news_mappings에 새로 연결된 수
    mapped_count: int = 0

    items: List[NewsArticleResponse]