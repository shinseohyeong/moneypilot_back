# 파일 경로 : app/schemas/stock_schema.py
# 파일 역할 : 주식 검색 API가 프론트엔드에 어떤 형태로 응답할지 정함

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

class StockSearchItem(BaseModel):
    """
    주식 검색 결과 1개 항목

    예:
    {
        "stock_id": 1,
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "market": "KOSPI"
    }
    """

    stock_id: int = Field(..., description="주식 ID")
    stock_code: str = Field(..., description="종목 코드")
    stock_name: str = Field(..., description="종목명")
    market: Optional[str] = Field(None, description="시장 구분")


class StockSearchResponse(BaseModel):
    """
    주식 검색 API 응답 전체 구조
    """

    keyword: str = Field(..., description="검색어")
    count: int = Field(..., description="검색 결과 개수")
    items: List[StockSearchItem] = Field(default_factory=list, description="검색 결과 목록")

# ==============
# 종목 상세 조회
# ==============
class StockDetailLatestPrice(BaseModel):
    """
    종목 상세 화면에서 함께 보여줄 최근 기준 시세 정보입니다.
    실시간 현재가가 아니라 DB에 저장된 최신 거래일 기준 시세입니다.
    """

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


class StockDetailResponse(BaseModel):
    """
    종목 상세 조회 응답입니다.
    """

    stock_id: int
    stock_code: str
    stock_name: str
    market: str

    representative_sector: Optional[str] = None
    industry: Optional[str] = None
    is_active: bool

    latest_price: Optional[StockDetailLatestPrice] = None