# 파일 경로 : app/routers/stock_router.py
# 파일 역할 : 실제 API URL을 만드는 파일
#           - GET /api/v1/stocks/search

# 20260619 인계 사항 : 나중에 GET /api/v1/stocks/{stock_id}를 추가할 때 /search 라우터를 {stock_id}보다 위에 생성

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.stock_schema import StockSearchResponse
from app.services.stock_service import StockService


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
    keyword: str = Query(
        ...,
        min_length=1,
        description="검색어. 예: 삼성, 005930",
    ),
    market: Optional[str] = Query(
        None,
        description="시장 구분. 예: KOSPI, KOSDAQ",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="검색 결과 최대 개수",
    ),
    db: Session = Depends(get_db),
):
    """
    주식 검색 API

    사용 예:
    GET /api/v1/stocks/search?keyword=삼성
    GET /api/v1/stocks/search?keyword=005930
    GET /api/v1/stocks/search?keyword=삼성&market=KOSPI&limit=10
    """

    stock_service = StockService(db)

    return stock_service.search_stocks(
        keyword=keyword,
        market=market,
        limit=limit,
    )