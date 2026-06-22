# 파일 경로 : app/schemas/stock_schema.py
# 파일 역할 : 주식 검색 API가 프론트엔드에 어떤 형태로 응답할지 정함

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


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