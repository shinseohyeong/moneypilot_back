# 파일 경로 : app/repositories/stock_price_repository.py
# 파일 역할 : stocks, stock_prices DB 조회/저장 담당

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.stock_model import Stock, StockPrice


class StockPriceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_stock_by_id(self, stock_id: int):
        return (
            self.db.query(Stock)
            .filter(
                Stock.id == stock_id,
                Stock.is_active == True,
            )
            .first()
        )

    def get_latest_price(self, stock_id: int) -> Optional[StockPrice]:
        return (
            self.db.query(StockPrice)
            .filter(StockPrice.stock_id == stock_id)
            .order_by(StockPrice.price_date.desc())
            .first()
        )

    def get_recent_chart_prices(self, stock_id: int, limit: int) -> List[StockPrice]:
        """
        최근 n개 거래일 데이터를 가져온다.
        주말/공휴일에는 거래 데이터가 없으므로 '최근 7일'을 날짜 범위가 아니라
        '최근 7개 거래일 데이터'로 처리하는 방식이 차트에 더 안정적이다.
        """
        rows = (
            self.db.query(StockPrice)
            .filter(StockPrice.stock_id == stock_id)
            .order_by(StockPrice.price_date.desc())
            .limit(limit)
            .all()
        )

        # 프론트 차트는 오래된 날짜 → 최신 날짜 순서가 보기 좋으므로 뒤집어서 반환
        return list(reversed(rows))

    def upsert_stock_price(self, price_data: dict) -> StockPrice:
        """
        같은 stock_id + price_date 데이터가 있으면 UPDATE,
        없으면 INSERT.
        """
        existing_price = (
            self.db.query(StockPrice)
            .filter(
                StockPrice.stock_id == price_data["stock_id"],
                StockPrice.price_date == price_data["price_date"],
            )
            .first()
        )

        if existing_price:
            for key, value in price_data.items():
                setattr(existing_price, key, value)
            return existing_price

        new_price = StockPrice(**price_data)
        self.db.add(new_price)
        return new_price

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()