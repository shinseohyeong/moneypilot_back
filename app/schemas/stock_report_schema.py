# ============================================================
# 파일 위치: app/schemas/stock_report_schema.py
# 역할:
#   - 관심종목 요약 리포트 생성/조회 API 응답 schema를 정의합니다.
# ============================================================

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class StockReportItemResponse(BaseModel):
    item_id: int
    stock_id: int
    stock_code: str
    stock_name: str

    current_price: Optional[str] = None
    change_rate: Optional[str] = None

    news_summary: Optional[str] = None
    sector_summary: Optional[str] = None
    risk_factors: Optional[str] = None

    created_at: Optional[datetime] = None


class StockReportResponse(BaseModel):
    report_id: int
    user_id: int
    report_date: date
    report_title: str

    market_summary: Optional[str] = None
    sector_summary: Optional[str] = None
    watchlist_summary: Optional[str] = None
    risk_summary: Optional[str] = None
    disclaimer: str

    created_at: Optional[datetime] = None
    items: List[StockReportItemResponse] = []


class StockReportListItemResponse(BaseModel):
    report_id: int
    user_id: int
    report_date: date
    report_title: str
    created_at: Optional[datetime] = None


class StockReportListResponse(BaseModel):
    user_id: int
    total_count: int
    items: List[StockReportListItemResponse]