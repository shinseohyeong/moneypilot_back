# ============================================================
# 파일 위치: app/schemas/stock_alert_schema.py
# 역할:
#   - 관심종목 뉴스 알림 API의 응답 schema를 정의합니다.
# ============================================================

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class StockAlertResponse(BaseModel):
    alert_id: int
    user_id: int

    stock_id: Optional[int] = None
    stock_name: Optional[str] = None

    news_id: Optional[int] = None
    sector_id: Optional[int] = None
    sector_name: Optional[str] = None

    alert_type: str
    title: str
    message: str

    is_read: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    read_at: Optional[datetime] = None


class StockAlertGenerateResponse(BaseModel):
    user_id: int
    checked_news_count: int
    generated_count: int
    duplicated_count: int
    items: List[StockAlertResponse]


class StockAlertListResponse(BaseModel):
    user_id: int
    total_count: int
    unread_count: int
    items: List[StockAlertResponse]


class StockAlertReadResponse(BaseModel):
    alert_id: int
    is_read: bool
    read_at: Optional[datetime] = None