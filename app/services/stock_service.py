# 파일 경로 : app/services/stock_service.py
# 파일 역할 : 비즈니스 로직 처리
#           - router에서 받은 검색어 검증
#           - repository에서 가져온 DB 결과를 응답 형태로 변환

from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.stock_repository import StockRepository
from app.schemas.stock_schema import StockSearchItem, StockSearchResponse


class StockService:
    """
    주식 관련 비즈니스 로직을 담당하는 service 클래스
    """

    def __init__(self, db: Session):
        self.stock_repository = StockRepository(db)

    def search_stocks(
        self,
        keyword: str,
        market: Optional[str] = None,
        limit: int = 20,
    ) -> StockSearchResponse:
        """
        주식 검색 서비스 로직

        1. 검색어 검증
        2. repository에 DB 조회 요청
        3. DB 모델 객체를 응답 schema로 변환
        """

        keyword = keyword.strip()

        if not keyword:
            raise HTTPException(
                status_code=400,
                detail="검색어를 입력해주세요.",
            )

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="limit은 1 이상 100 이하로 입력해주세요.",
            )

        stocks = self.stock_repository.search_stocks(
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