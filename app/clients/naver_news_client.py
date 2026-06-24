# ============================================================
# 파일 위치: app/clients/naver_news_client.py
# 역할:
#   - 네이버 뉴스 검색 API 호출만 담당합니다.
#   - DB 저장이나 비즈니스 판단은 하지 않습니다.
# ============================================================

import json
from typing import Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException

from app.core.config import ENV_PATH, settings


class NaverNewsClient:
    def __init__(self):
        self.client_id = settings.naver_client_id
        self.client_secret = settings.naver_client_secret
        self.base_url = settings.naver_news_base_url


        if not self.client_id or not self.client_secret:
            raise HTTPException(
                status_code=500,
                detail="네이버 뉴스 API 키가 설정되지 않았습니다. .env를 확인해주세요.",
            )

    def search_news(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date",
    ) -> List[Dict]:
        """
        네이버 뉴스 검색 API 호출

        sort:
        - sim: 정확도순
        - date: 날짜순
        """
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort,
        }

        url = f"{self.base_url}?{urlencode(params)}"

        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        request = Request(url, headers=headers, method="GET")

        try:
            with urlopen(request, timeout=10) as response:
                response_body = response.read().decode("utf-8")
                data = json.loads(response_body)
                return data.get("items", [])

        except HTTPError as e:
            error_body = e.read().decode("utf-8")

            raise HTTPException(
                status_code=e.code,
                detail=f"네이버 뉴스 API 호출 실패: {error_body}",
            )

        except URLError as e:
            raise HTTPException(
                status_code=502,
                detail=f"네이버 뉴스 API 연결 실패: {str(e)}",
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"네이버 뉴스 API 처리 중 오류 발생: {str(e)}",
            )