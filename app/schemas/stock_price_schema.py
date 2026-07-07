# 파일 경로 : app/schemas/stock_schema.py
# 파일 역할 : 최근 기준 시세 응답, 차트 응답, 수집 결과 응답 schema

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class StockPriceItem(BaseModel):
    price_date: date
    open_price: Optional[int] = None
    high_price: Optional[int] = None
    low_price: Optional[int] = None
    close_price: int
    volume: Optional[int] = None


class StockLatestPriceResponse(BaseModel):
    stock_id: int
    stock_code: str
    stock_name: str
    market: str

    price_label: str = "최근 거래일 종가"

    price_date: date

    close_price: Decimal
    previous_close: Optional[Decimal] = None
    price_change: Optional[Decimal] = None
    change_rate: Optional[Decimal] = None

    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None

    volume: Optional[int] = None
    trade_value: Optional[Decimal] = None

    listed_shares: Optional[int] = None
    market_cap: Optional[Decimal] = None
    

class StockChartResponse(BaseModel):
    stock_id: int
    stock_code: str
    stock_name: str
    period: str
    items: List[StockPriceItem]


class StockPriceCollectResponse(BaseModel):
    stock_id: int
    stock_code: str
    stock_name: str
    requested_days: int
    fetched_count: int
    saved_count: int
    message: str