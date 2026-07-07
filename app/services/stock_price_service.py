# 파일 경로 : app/services/stock_price_service.py
# 파일 역할 : - 기간 검증, 최근 시세 조회, 차트 조회, 공공데이터 수집/저장 로직

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import HTTPException

from app.clients.public_stock_price_client import (
    PublicStockPriceClient,
    PublicStockApiError,
)
from app.repositories.stock_price_repository import StockPriceRepository
from app.schemas.stock_price_schema import (
    StockChartResponse,
    StockLatestPriceResponse,
    StockPriceCollectResponse,
    StockPriceItem,
)


class StockPriceService:
    PERIOD_LIMIT_MAP = {
        "7d": 7,
        "14d": 14,
        "30d": 30,
    }

    def __init__(
        self,
        repository: StockPriceRepository,
        public_stock_client: PublicStockPriceClient,
    ):
        self.repository = repository
        self.public_stock_client = public_stock_client

    def get_latest_price(self, stock_id: int) -> StockLatestPriceResponse:
        stock = self.repository.get_stock_by_id(stock_id)

        if not stock:
            raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

        latest_price = self.repository.get_latest_price(stock_id)

        if not latest_price:
            raise HTTPException(
                status_code=404,
                detail="최근 기준 시세 데이터가 없습니다. 먼저 시세 수집 API를 실행해주세요.",
            )

        return StockLatestPriceResponse(
            stock_id=stock.id,
            stock_code=stock.stock_code,
            stock_name=stock.stock_name,
            market=stock.market,

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

    def get_chart(self, stock_id: int, period: str) -> StockChartResponse:
        stock = self.repository.get_stock_by_id(stock_id)

        if not stock:
            raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

        if period not in self.PERIOD_LIMIT_MAP:
            raise HTTPException(
                status_code=400,
                detail="period는 7d, 14d, 30d만 사용할 수 있습니다.",
            )

        limit = self.PERIOD_LIMIT_MAP[period]
        prices = self.repository.get_recent_chart_prices(stock_id=stock_id, limit=limit)

        return StockChartResponse(
            stock_id=stock.id,
            stock_code=stock.stock_code,
            stock_name=stock.stock_name,
            period=period,
            items=[
                StockPriceItem(
                    price_date=price.price_date,
                    open_price=price.open_price,
                    high_price=price.high_price,
                    low_price=price.low_price,
                    close_price=price.close_price,
                    volume=price.volume,
                )
                for price in prices
            ],
        )

    def collect_stock_prices(self, stock_id: int, days: int = 45) -> StockPriceCollectResponse:
        """
        공공데이터포털에서 최근 n일 범위의 시세를 가져와 DB에 저장한다.

        기본값을 45일로 둔 이유:
        - 30일 차트를 만들 때 주말/공휴일 데이터가 빠질 수 있음
        - 넉넉하게 45일 조회 후 DB에서는 최근 30개 거래일만 사용
        """
        stock = self.repository.get_stock_by_id(stock_id)

        if not stock:
            raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")

        if days < 1 or days > 365:
            raise HTTPException(
                status_code=400,
                detail="days는 1 이상 365 이하로 입력해주세요.",
            )

        end_date = date.today()
        begin_date = end_date - timedelta(days=days)

        begin_bas_dt = begin_date.strftime("%Y%m%d")
        end_bas_dt = end_date.strftime("%Y%m%d")

        try:
            raw_items = self.public_stock_client.fetch_stock_prices(
                stock_code=stock.stock_code,
                begin_bas_dt=begin_bas_dt,
                end_bas_dt=end_bas_dt,
                num_of_rows=300,
            )

            saved_count = 0

            for item in raw_items:
                price_data = self._map_api_item_to_price_data(
                    stock_id=stock.id,
                    item=item,
                )
                self.repository.upsert_stock_price(price_data)
                saved_count += 1

            self.repository.commit()

        except PublicStockApiError as exc:
            self.repository.rollback()
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        except Exception as exc:
            self.repository.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"시세 저장 중 오류가 발생했습니다: {exc}",
            ) from exc

        return StockPriceCollectResponse(
            stock_id=stock.id,
            stock_code=stock.stock_code,
            stock_name=stock.stock_name,
            requested_days=days,
            fetched_count=len(raw_items),
            saved_count=saved_count,
            message="공공데이터 기반 주식 시세 저장이 완료되었습니다.",
        )
    
    def _to_decimal(self, value) -> Optional[Decimal]:
        """
        공공데이터 API에서 문자열로 내려오는 숫자 값을 Decimal로 변환합니다.
        예: "71000" -> Decimal("71000")
        """
        if value is None or value == "":
            return None

        try:
            return Decimal(str(value).replace(",", ""))
        except InvalidOperation:
            return None

    def _to_int(self, value) -> Optional[int]:
        """
        공공데이터 API에서 문자열로 내려오는 정수 값을 int로 변환합니다.
        예: "12345678" -> 12345678
        """
        if value is None or value == "":
            return None

        try:
            return int(str(value).replace(",", ""))
        except ValueError:
            return None


    def _map_api_item_to_price_data(self, stock_id: int, item: dict) -> dict:
        close_price = self._to_decimal(item.get("clpr"))
        price_change = self._to_decimal(item.get("vs"))

        previous_close = self._to_decimal("0")

        if close_price is not None and price_change is not None:
            previous_close = close_price - price_change

        return {
            "stock_id": stock_id,
            "price_date": self._parse_yyyymmdd(item.get("basDt")),

            # 가격 정보
            "close_price": close_price,
            "open_price": self._to_decimal(item.get("mkp")),
            "high_price": self._to_decimal(item.get("hipr")),
            "low_price": self._to_decimal(item.get("lopr")),

            # 전일 종가, 전일 대비, 등락률
            "previous_close": previous_close,
            "price_change": self._to_decimal(item.get("vs")),
            "change_rate": self._to_decimal(item.get("fltRt")),

            # 거래량, 거래대금
            "volume": self._to_int(item.get("trqu")),
            "trade_value": self._to_decimal(item.get("trPrc")),

            # 상장주식, 시가총액
            "listed_shares": self._to_int(item.get("lstgStCnt")),
            "market_cap": self._to_decimal(item.get("mrktTotAmt")),

            # 데이터 출처
            "source": "PUBLIC_DATA",
        }

    def _parse_yyyymmdd(self, value: Optional[str]) -> Optional[date]:
        if not value:
            return None

        try:
            return datetime.strptime(str(value), "%Y%m%d").date()
        except ValueError:
            return None

    def _to_int(self, value) -> Optional[int]:
        if value is None or value == "":
            return None

        try:
            return int(str(value).replace(",", ""))
        except ValueError:
            return None

    def _to_int(self, value) -> Optional[int]:
        if value is None or value == "":
            return None

        try:
            return int(str(value).replace(",", ""))
        except ValueError:
            return None