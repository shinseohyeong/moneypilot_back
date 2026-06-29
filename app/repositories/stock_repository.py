# 파일 경로 : app/repositories/stock_repository.py
# 파일 역할 : DB에서 stocks 테이블을 직접 조회하는 파일
#            SQLAlchemy 쿼리는 여기에서 담당

from typing import List, Optional
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.stock_model import Stock, StockPrice


class StockRepository:
    """
    "stocks" 테이블과 직접 통신하는 repository 클래스

    service에서는 DB 쿼리를 직접 작성하지 않고,
    이 repository를 통해 필요한 데이터를 가져온다.
    """

    def __init__(self, db: Session):
        self.db = db

    def search_stocks(
        self,
        keyword: str,
        market: Optional[str] = None,
        limit: int = 20,
    ) -> List[Stock]:
        """
        종목명 또는 종목코드로 주식을 검색한다.

        검색 대상:
        - stock_name
        - stock_code

        예:
        keyword="삼성" -> 삼성전자, 삼성SDI 등
        keyword="005930" -> 삼성전자
        """

        like_keyword = f"%{keyword}%"

        query = self.db.query(Stock).filter(
            or_( # 조건1 또는 조건2 중 하나라도 맞으면 조회
                Stock.stock_name.like(like_keyword),
                Stock.stock_code.like(like_keyword),
            )
        )

        # 시장 구분이 들어온 경우에만 필터링한다.
        # 예: KOSPI, KOSDAQ
        if market:
            query = query.filter(Stock.market == market)

        # stock_name 컬럼 기준으로 오름차순 정렬
        # 검색 결과가 너무 많이 나오지 않도록 limit을 건다.
        return query.order_by(Stock.stock_name.asc()).limit(limit).all()
    
    def get_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        """
        stock_id로 종목 기본 정보를 조회합니다.

        stock_id는 stocks 테이블의 id 값입니다.
        """
        return (
            self.db.query(Stock)
            .filter(
                Stock.id == stock_id,
                Stock.is_active == True,
            )
            .first()
        )

    def get_latest_price_by_stock_id(self, stock_id: int) -> Optional[StockPrice]:
        """
        특정 종목의 최근 기준 시세를 조회합니다.

        실시간 현재가가 아니라 stock_prices 테이블에 저장된
        가장 최신 price_date 데이터를 가져옵니다.
        """
        return (
            self.db.query(StockPrice)
            .filter(
                StockPrice.stock_id == stock_id,
                StockPrice.source == "PUBLIC_DATA",
            )
            .order_by(StockPrice.price_date.desc())
            .first()
        )