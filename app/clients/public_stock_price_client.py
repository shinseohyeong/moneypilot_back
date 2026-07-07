# 파일 경로 : app/clients/public_stock_price_client.py
# 파일 역할 :  - 공공데이터포털 금융위원회_주식시세정보 API 호출
#             - API 응답 JSON에서 item 리스트만 추출

import os
from urllib.parse import unquote
from typing import List, Optional

import requests


class PublicStockApiError(Exception):
    pass


class PublicStockPriceClient:
    BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"

    def __init__(self):
        service_key = os.getenv("PUBLIC_DATA_STOCK_SERVICE_KEY")

        if not service_key:
            raise PublicStockApiError(
                "PUBLIC_DATA_STOCK_SERVICE_KEY가 .env에 설정되어 있지 않습니다."
            )

        # 공공데이터포털 키가 URL 인코딩된 상태로 복사되는 경우가 많아서 한 번 풀어준다.
        self.service_key = unquote(service_key)

    def fetch_stock_prices(
        self,
        stock_code: str,
        begin_bas_dt: Optional[str] = None,
        end_bas_dt: Optional[str] = None,
        bas_dt: Optional[str] = None,
        num_of_rows: int = 100,
        page_no: int = 1,
    ) -> List[dict]:
        """
        공공데이터포털에서 특정 종목의 주식 시세를 조회한다.

        stock_code: 005930 같은 6자리 종목코드
        begin_bas_dt: YYYYMMDD
        end_bas_dt: YYYYMMDD
        bas_dt: YYYYMMDD, 특정 날짜만 조회할 때 사용
        """

        params = {
            "serviceKey": self.service_key,
            "resultType": "json",
            "numOfRows": num_of_rows,
            "pageNo": page_no,

            # API에는 srtnCd 정확검색 파라미터가 없고 likeSrtnCd가 제공됨
            "likeSrtnCd": stock_code,
        }

        if bas_dt:
            params["basDt"] = bas_dt

        if begin_bas_dt:
            params["beginBasDt"] = begin_bas_dt

        if end_bas_dt:
            params["endBasDt"] = end_bas_dt

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise PublicStockApiError(f"공공데이터 API 요청 실패: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise PublicStockApiError("공공데이터 API 응답을 JSON으로 변환할 수 없습니다.") from exc

        api_response = data.get("response", {})
        header = api_response.get("header", {})
        body = api_response.get("body", {})

        result_code = header.get("resultCode")
        result_msg = header.get("resultMsg")

        if result_code != "00":
            raise PublicStockApiError(
                f"공공데이터 API 오류: result_code={result_code}, result_msg={result_msg}"
            )

        items = body.get("items", {})
        raw_items = []

        if isinstance(items, dict):
            raw_items = items.get("item", [])
        elif isinstance(items, list):
            raw_items = items

        # item이 1개일 때 dict로 내려오는 경우 방어
        if isinstance(raw_items, dict):
            raw_items = [raw_items]

        if not raw_items:
            return []

        # likeSrtnCd 검색이므로 혹시 모를 부분검색 결과를 정확히 한 번 더 필터링
        return [
            item for item in raw_items
            if str(item.get("srtnCd", "")).zfill(6) == stock_code
        ]