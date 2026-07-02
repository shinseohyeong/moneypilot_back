# ============================================================
# 파일 위치: app/clients/naver_news_client.py
# 역할:
#   - 네이버 뉴스 검색 API 호출을 담당합니다.
#   - 외부 API 호출 코드는 service가 아니라 client에 둡니다.
# ============================================================

import os
from typing import Any, Dict

import requests
from fastapi import HTTPException


class NaverNewsClient:
    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        self.news_search_url = os.getenv(
            "NAVER_NEWS_SEARCH_URL",
            "https://openapi.naver.com/v1/search/news.json",
        )

        if not self.client_id or not self.client_secret:
            raise HTTPException(
                status_code=500,
                detail="네이버 뉴스 API 환경변수가 설정되지 않았습니다.",
            )

    def search_news(
        self,
        keyword: str,
        display: int = 10,
        start: int = 1,
        sort: str = "date",
    ) -> Dict[str, Any]:
        """
        네이버 뉴스 검색 API를 호출합니다.

        sort:
        - date: 날짜순
        - sim: 정확도순
        """
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }

        params = {
            "query": keyword,
            "display": display,
            "start": start,
            "sort": sort,
        }

        try:
            response = requests.get(
                self.news_search_url,
                headers=headers,
                params=params,
                timeout=10,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"네이버 뉴스 API 호출 실패: {response.text}",
                )

            return response.json()

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"네이버 뉴스 API 호출 중 오류가 발생했습니다: {str(e)}",
            )


def get_naver_news_client() -> NaverNewsClient:
    """
    NaverNewsClient 객체를 생성해서 반환합니다.
    service에서 직접 class를 만들지 않고 이 함수를 통해 가져옵니다.
    """
    return NaverNewsClient()