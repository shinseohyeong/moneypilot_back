# 파일 경로 : app/services/stock_service.py
# 파일 역할 : 비즈니스 로직 처리
#           - router에서 받은 검색어 검증
#           - repository에서 가져온 DB 결과를 응답 형태로 변환

from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.stock_repository import StockRepository
from app.schemas.stock_schema import (
    StockSearchItem,
    StockSearchResponse,
    StockDetailLatestPrice,
    StockDetailResponse,
)


class StockService:
    """
    주식 관련 비즈니스 로직을 담당하는 service 클래스
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = StockRepository(db)

    def search_stocks(self, keyword: str, market: str | None = None, limit: int = 10):
        stocks = self.repository.search_stocks(
            keyword=keyword,
            market=market,
            limit=limit,
        )

        items = [
            StockSearchItem(
                stock_id=stock.id,
                stock_code=stock.stock_code,
                stock_name=stock.stock_name,
                market=stock.market,
            )
            for stock in stocks
        ]

        return StockSearchResponse(
            keyword=keyword,
            count=len(items),
            items=items,
        )
    
    def get_stock_detail(self, stock_id: int) -> StockDetailResponse:
        """
        종목 상세 정보를 조회합니다.

        조회 내용:
        - stocks 테이블의 종목 기본 정보
        - stock_prices 테이블의 최근 기준 시세
        """
        stock = self.repository.get_stock_by_id(stock_id)

        if not stock:
            raise HTTPException(
                status_code=404,
                detail="종목을 찾을 수 없습니다.",
            )

        latest_price = self.repository.get_latest_price_by_stock_id(stock_id)

        return StockDetailResponse(
            stock_id=stock.id,
            stock_code=stock.stock_code,
            stock_name=stock.stock_name,
            market=stock.market,
            representative_sector=stock.representative_sector,
            industry=stock.industry,
            is_active=stock.is_active,
            latest_price=self._to_latest_price(latest_price),
        )

    def _to_latest_price(self, latest_price) -> StockDetailLatestPrice | None:
        """
        StockPrice 모델 객체를 종목 상세 응답용 schema로 변환합니다.
        최근 시세 데이터가 없으면 None을 반환합니다.
        """
        if not latest_price:
            return None

        return StockDetailLatestPrice(
            price_date=latest_price.price_date,
            close_price=latest_price.close_price,
            previous_close=latest_price.previous_close,
            price_change=latest_price.price_change,
            change_rate=latest_price.change_rate,
            open_price=latest_price.open_price,
            high_price=latest_price.high_price,
            low_price=latest_price.low_price,
            volume=latest_price.volume,
            trade_value=latest_price.trade_value,
            listed_shares=latest_price.listed_shares,
            market_cap=latest_price.market_cap,
        )