# ============================================================
# 파일 위치: app/routers/news_router.py
# 역할:
#   - 뉴스 관련 HTTP 요청을 받습니다.
#   - 실제 수집/저장/조회 로직은 NewsService에 위임합니다.
# ============================================================

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.news_schema import (
    EconomyNewsCollectRequest,
    NewsCollectResponse,
    NewsListResponse,
    StockNewsCollectRequest,
)
from app.services.news_service import NewsService

router = APIRouter(prefix="/api/v1", tags=["News"])


def get_news_service(db: Session = Depends(get_db)) -> NewsService:
    """
    NewsService 객체를 생성합니다.

    Service는 DB 세션을 받아 repository와 client를 사용합니다.
    """
    return NewsService(db)


@router.post(
    "/news/economy/collect",
    response_model=NewsCollectResponse,
    summary="경제 뉴스 수집",
)
def collect_economy_news(
    request: EconomyNewsCollectRequest,
    service: NewsService = Depends(get_news_service),
):
    """
    네이버 뉴스 API에서 경제 뉴스를 수집해 DB에 저장합니다.
    """
    return service.collect_economy_news(
        query=request.query,
        display=request.display,
        sort=request.sort,
    )


@router.get(
    "/news/economy",
    response_model=NewsListResponse,
    summary="경제 뉴스 조회",
)
def get_economy_news(
    limit: int = Query(default=20, ge=1, le=100),
    service: NewsService = Depends(get_news_service),
):
    """
    DB에 저장된 경제 뉴스를 최신순으로 조회합니다.
    """
    return service.get_economy_news(limit=limit)


@router.post(
    "/stocks/{stock_id}/news/collect",
    response_model=NewsCollectResponse,
    summary="종목 뉴스 수집",
)
def collect_stock_news(
    request: StockNewsCollectRequest,
    stock_id: int = Path(..., ge=1),
    service: NewsService = Depends(get_news_service),
):
    """
    특정 종목의 뉴스를 네이버 뉴스 API에서 수집해 DB에 저장합니다.
    """
    return service.collect_stock_news(
        stock_id=stock_id,
        query=request.query,
        display=request.display,
        sort=request.sort,
    )


@router.get(
    "/stocks/{stock_id}/news",
    response_model=NewsListResponse,
    summary="종목 뉴스 조회",
)
def get_stock_news(
    stock_id: int = Path(..., ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    service: NewsService = Depends(get_news_service),
):
    """
    DB에 저장된 특정 종목 뉴스를 최신순으로 조회합니다.
    """
    return service.get_stock_news(
        stock_id=stock_id,
        limit=limit,
    )