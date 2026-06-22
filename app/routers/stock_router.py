# 파일 경로 : app/routers/stock_router.py
# 파일 역할 : 실제 API URL을 만드는 파일
#           - GET /api/v1/stocks/search

# 20260619 인계 사항 : 나중에 GET /api/v1/stocks/{stock_id}를 추가할 때 /search 라우터를 {stock_id}보다 위에 생성

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.stock_schema import StockSearchResponse
from app.services.stock_service import StockService

from app.clients.public_stock_price_client import PublicStockPriceClient
from app.repositories.stock_price_repository import StockPriceRepository
from app.services.stock_price_service import StockPriceService
from app.schemas.stock_price_schema import (
    StockLatestPriceResponse,
    StockChartResponse,
    StockPriceCollectResponse,
)


router = APIRouter(
    prefix="/api/v1/stocks",
    tags=["Stocks"],
)


@router.get(
    "/search",
    response_model=StockSearchResponse,
    summary="주식 검색",
    description="종목명 또는 종목코드로 주식을 검색합니다.",
)
def search_stocks(
    keyword: str = Query(..., min_length=1, description="검색어. 예: 삼성, 005930"),
    market: Optional[str] = Query(None, description="시장 구분. 예: KOSPI, KOSDAQ"),
    limit: int = Query(20, ge=1, le=100, description="검색 결과 최대 개수"),
    db: Session = Depends(get_db),
):
    stock_service = StockService(db)

    return stock_service.search_stocks(
        keyword=keyword,
        market=market,
        limit=limit,
    )


def get_stock_price_service(db: Session = Depends(get_db)) -> StockPriceService:
    repository = StockPriceRepository(db)
    public_stock_client = PublicStockPriceClient()
    return StockPriceService(repository, public_stock_client)


@router.get(
    "/{stock_id}/price",
    response_model=StockLatestPriceResponse,
    summary="최근 기준 시세 조회",
)
def get_stock_latest_price(
    stock_id: int = Path(..., description="stocks 테이블의 id"),
    service: StockPriceService = Depends(get_stock_price_service),
):
    return service.get_latest_price(stock_id)


@router.get(
    "/{stock_id}/chart",
    response_model=StockChartResponse,
    summary="종목 차트 조회",
)
def get_stock_chart(
    stock_id: int = Path(..., description="stocks 테이블의 id"),
    period: str = Query("30d", description="차트 기간: 7d, 14d, 30d"),
    service: StockPriceService = Depends(get_stock_price_service),
):
    return service.get_chart(stock_id=stock_id, period=period)


@router.post(
    "/{stock_id}/prices/collect",
    response_model=StockPriceCollectResponse,
    summary="공공데이터 기반 주식 시세 수집",
)
def collect_stock_prices(
    stock_id: int = Path(..., description="stocks 테이블의 id"),
    days: int = Query(45, description="최근 며칠 범위의 데이터를 수집할지"),
    service: StockPriceService = Depends(get_stock_price_service),
):
    return service.collect_stock_prices(stock_id=stock_id, days=days)