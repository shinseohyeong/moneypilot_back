# 파일 위치: app/schemas/stock_watchlist_schema.py
# 파일 역할: 관심종목 카테고리/관심종목 API의 요청, 응답 데이터 구조 정의

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# =========================
# 관심종목 카테고리 Schema
# =========================

class StockWatchlistCategoryCreate(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=100)
    display_order: int = 0
    is_default: bool = False


class StockWatchlistCategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_order: Optional[int] = None
    is_default: Optional[bool] = None


class StockWatchlistCategoryItem(BaseModel):
    category_id: int
    category_name: str
    display_order: int
    is_default: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StockWatchlistCategoryListResponse(BaseModel):
    items: List[StockWatchlistCategoryItem]


class StockWatchlistCategoryDeleteResponse(BaseModel):
    category_id: int
    message: str


# =========================
# 관심종목 Schema
# =========================

class StockWatchlistCreate(BaseModel):
    category_id: int
    stock_id: int
    memo: Optional[str] = Field(None, max_length=255)
    alert_enabled: bool = False
    alert_price: Optional[Decimal] = None


class StockWatchlistUpdate(BaseModel):
    # category_id를 받으면 다른 카테고리로 이동 가능
    category_id: Optional[int] = None
    memo: Optional[str] = Field(None, max_length=255)
    alert_enabled: Optional[bool] = None
    alert_price: Optional[Decimal] = None


class StockWatchlistLatestPrice(BaseModel):
    price_date: date
    close_price: Decimal
    price_change: Optional[Decimal] = None
    change_rate: Optional[Decimal] = None
    volume: Optional[int] = None
    market_cap: Optional[Decimal] = None


class StockWatchlistItem(BaseModel):
    watchlist_id: int

    category_id: int
    category_name: str

    stock_id: int
    stock_code: str
    stock_name: str
    market: str

    memo: Optional[str] = None
    alert_enabled: bool
    alert_price: Optional[Decimal] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    latest_price: Optional[StockWatchlistLatestPrice] = None


class StockWatchlistCategoryGroup(BaseModel):
    category_id: int
    category_name: str
    display_order: int
    is_default: bool
    items: List[StockWatchlistItem]


class StockWatchlistGroupedResponse(BaseModel):
    categories: List[StockWatchlistCategoryGroup]


class StockWatchlistDeleteResponse(BaseModel):
    watchlist_id: int
    message: str