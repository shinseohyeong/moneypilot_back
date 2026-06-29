# 파일 경로 : app/routers/stock_router.py
# 파일 역할 : 실제 API URL을 만드는 파일
#           - GET /api/v1/stocks/search

# 20260619 인계 사항 : 나중에 GET /api/v1/stocks/{stock_id}를 추가할 때 /search 라우터를 {stock_id}보다 위에 생성

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.stock_schema import StockSearchResponse, StockSearchResponse, StockDetailResponse
from app.services.stock_service import StockService

from app.clients.public_stock_price_client import PublicStockPriceClient
from app.repositories.stock_price_repository import StockPriceRepository
from app.services.stock_price_service import StockPriceService
from app.schemas.stock_price_schema import (
    StockLatestPriceResponse,
    StockChartResponse,
    StockPriceCollectResponse,
)

from app.repositories.stock_watchlist_repository import StockWatchlistRepository
from app.services.stock_watchlist_service import StockWatchlistService
from app.schemas.stock_watchlist_schema import (
    StockWatchlistCategoryCreate,
    StockWatchlistCategoryDeleteResponse,
    StockWatchlistCategoryItem,
    StockWatchlistCategoryListResponse,
    StockWatchlistCategoryUpdate,
    StockWatchlistCreate,
    StockWatchlistDeleteResponse,
    StockWatchlistGroupedResponse,
    StockWatchlistItem,
    StockWatchlistUpdate,
)

from app.schemas.stock_report_schema import (
    StockReportListResponse,
    StockReportResponse,
)
from app.services.stock_report_service import StockReportService

from app.schemas.stock_alert_schema import (
    StockAlertGenerateResponse,
    StockAlertListResponse,
    StockAlertReadResponse,
)
from app.services.stock_alert_service import StockAlertService

router = APIRouter(
    prefix="/api/v1/stocks",
    tags=["Stocks"],
)

def get_stock_report_service(db: Session = Depends(get_db)) -> StockReportService:
    """
    관심종목 요약 리포트 service 객체를 생성합니다.
    """
    return StockReportService(db)

def get_stock_alert_service(db: Session = Depends(get_db)) -> StockAlertService:
    """
    관심종목 뉴스 알림 service 객체를 생성합니다.
    """
    return StockAlertService(db)

# ====================
# 주식 조회
# ====================
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

# ====================
# 관심종목
# ====================
def get_stock_watchlist_service(
    db: Session = Depends(get_db),
) -> StockWatchlistService:
    repository = StockWatchlistRepository(db)
    return StockWatchlistService(repository)

# ============================================================
# 관심종목 카테고리 API
# ============================================================

@router.post(
    "/watchlist/categories",
    response_model=StockWatchlistCategoryItem,
    summary="관심종목 카테고리 생성",
)
def create_watchlist_category(
    request: StockWatchlistCategoryCreate,
    user_id: int = Query(1, description="임시 사용자 ID. 인증 연동 후 current_user로 교체 예정"),
    service: StockWatchlistService = Depends(get_stock_watchlist_service),
):
    return service.create_category(user_id=user_id, request=request)


@router.get(
    "/watchlist/categories",
    response_model=StockWatchlistCategoryListResponse,
    summary="관심종목 카테고리 목록 조회",
)
def get_watchlist_categories(
    user_id: int = Query(1, description="임시 사용자 ID. 인증 연동 후 current_user로 교체 예정"),
    service: StockWatchlistService = Depends(get_stock_watchlist_service),
):
    return service.get_categories(user_id=user_id)


@router.patch(
    "/watchlist/categories/{category_id}",
    response_model=StockWatchlistCategoryItem,
    summary="관심종목 카테고리 수정",
)
def update_watchlist_category(
    category_id: int,
    request: StockWatchlistCategoryUpdate,
    user_id: int = Query(1, description="임시 사용자 ID. 인증 연동 후 current_user로 교체 예정"),
    service: StockWatchlistService = Depends(get_stock_watchlist_service),
):
    return service.update_category(
        user_id=user_id,
        category_id=category_id,
        request=request,
    )


@router.delete(
    "/watchlist/categories/{category_id}",
    response_model=StockWatchlistCategoryDeleteResponse,
    summary="관심종목 카테고리 삭제",
)
def delete_watchlist_category(
    category_id: int,
    user_id: int = Query(1, description="임시 사용자 ID. 인증 연동 후 current_user로 교체 예정"),
    service: StockWatchlistService = Depends(get_stock_watchlist_service),
):
    return service.delete_category(
        user_id=user_id,
        category_id=category_id,
    )


# ============================================================
# 관심종목 API
# ============================================================

@router.post(
    "/watchlist",
    response_model=StockWatchlistItem,
    summary="관심종목 추가",
)
def create_watchlist(
    request: StockWatchlistCreate,
    user_id: int = Query(1, description="임시 사용자 ID. 인증 연동 후 current_user로 교체 예정"),
    service: StockWatchlistService = Depends(get_stock_watchlist_service),
):
    return service.create_watchlist(user_id=user_id, request=request)


@router.get(
    "/watchlist",
    response_model=StockWatchlistGroupedResponse,
    summary="관심종목 목록 조회",
)
def get_watchlists(
    user_id: int = Query(1, description="임시 사용자 ID. 인증 연동 후 current_user로 교체 예정"),
    service: StockWatchlistService = Depends(get_stock_watchlist_service),
):
    return service.get_watchlists(user_id=user_id)


@router.patch(
    "/watchlist/{watchlist_id}",
    response_model=StockWatchlistItem,
    summary="관심종목 수정",
)
def update_watchlist(
    watchlist_id: int,
    request: StockWatchlistUpdate,
    user_id: int = Query(1, description="임시 사용자 ID. 인증 연동 후 current_user로 교체 예정"),
    service: StockWatchlistService = Depends(get_stock_watchlist_service),
):
    return service.update_watchlist(
        user_id=user_id,
        watchlist_id=watchlist_id,
        request=request,
    )


@router.delete(
    "/watchlist/{watchlist_id}",
    response_model=StockWatchlistDeleteResponse,
    summary="관심종목 삭제",
)
def delete_watchlist(
    watchlist_id: int,
    user_id: int = Query(1, description="임시 사용자 ID. 인증 연동 후 current_user로 교체 예정"),
    service: StockWatchlistService = Depends(get_stock_watchlist_service),
):
    return service.delete_watchlist(
        user_id=user_id,
        watchlist_id=watchlist_id,
    )

@router.post(
    "/reports/generate",
    response_model=StockReportResponse,
    summary="관심종목 요약 리포트 생성",
)
def generate_stock_report(
    user_id: int,
    service: StockReportService = Depends(get_stock_report_service),
):
    """
    사용자의 관심종목을 기준으로 현재가, 뉴스 요약, 섹터 흐름, 위험 요인을 종합한 리포트를 생성합니다.
    """
    return service.generate_stock_report(user_id=user_id)


@router.get(
    "/reports",
    response_model=StockReportListResponse,
    summary="관심종목 요약 리포트 목록 조회",
)
def list_stock_reports(
    user_id: int,
    limit: int = 20,
    service: StockReportService = Depends(get_stock_report_service),
):
    """
    사용자의 관심종목 요약 리포트 목록을 조회합니다.
    """
    return service.list_stock_reports(
        user_id=user_id,
        limit=limit,
    )


@router.get(
    "/reports/{report_id}",
    response_model=StockReportResponse,
    summary="관심종목 요약 리포트 상세 조회",
)
def get_stock_report(
    report_id: int,
    service: StockReportService = Depends(get_stock_report_service),
):
    """
    저장된 관심종목 요약 리포트 상세를 조회합니다.
    """
    return service.get_stock_report(report_id=report_id)

@router.post(
    "/alerts/generate",
    response_model=StockAlertGenerateResponse,
    summary="관심종목 뉴스 알림 생성",
)
def generate_stock_alerts(
    user_id: int,
    days: int = 7,
    service: StockAlertService = Depends(get_stock_alert_service),
):
    """
    사용자의 관심종목 관련 최근 뉴스를 기반으로 대시보드 알림을 생성합니다.
    """
    return service.generate_stock_alerts(
        user_id=user_id,
        days=days,
    )


@router.get(
    "/alerts",
    response_model=StockAlertListResponse,
    summary="관심종목 뉴스 알림 목록 조회",
)
def list_stock_alerts(
    user_id: int,
    unread_only: bool = False,
    limit: int = 50,
    service: StockAlertService = Depends(get_stock_alert_service),
):
    """
    사용자의 관심종목 뉴스 알림 목록을 조회합니다.
    """
    return service.list_stock_alerts(
        user_id=user_id,
        unread_only=unread_only,
        limit=limit,
    )


@router.patch(
    "/alerts/{alert_id}/read",
    response_model=StockAlertReadResponse,
    summary="관심종목 뉴스 알림 읽음 처리",
)
def mark_stock_alert_as_read(
    alert_id: int,
    service: StockAlertService = Depends(get_stock_alert_service),
):
    """
    알림 1건을 읽음 처리합니다.
    """
    return service.mark_alert_as_read(alert_id=alert_id)


# ====================
# 차트/시세 조회
# ====================

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


# ====================
# 공공데이터 주식 시세 수집
# ====================
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

# ====================
# 종목 상세 조회
# ====================
@router.get(
    "/{stock_id}",
    response_model=StockDetailResponse,
    summary="종목 상세 조회",
    description="특정 종목의 기본 정보와 최근 기준 시세를 조회합니다.",
)
def get_stock_detail(
    stock_id: int = Path(..., description="stocks 테이블의 id"),
    db: Session = Depends(get_db),
):
    stock_service = StockService(db)
    return stock_service.get_stock_detail(stock_id=stock_id)
