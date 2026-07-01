# ============================================================
# 파일 위치: app/clients/youtube_client.py
# 역할:
#   - YouTube Data API v3를 호출해 공개 유튜브 영상을 검색합니다.
#   - service가 API 호출 세부사항을 몰라도 되도록 client로 분리합니다.
# ============================================================

from typing import Any, Dict, List

import requests
from fastapi import HTTPException

from app.core.config import settings


class YoutubeClient:
    """
    YouTube Data API 호출 client입니다.
    """

    YOUTUBE_SEARCH_API_URL = "https://www.googleapis.com/youtube/v3/search"

    def search_videos(
        self,
        query: str,
        max_results: int = 5,
        order: str = "date",
    ) -> List[Dict[str, Any]]:
        """
        검색어를 기반으로 공개 유튜브 영상을 검색합니다.

        order:
        - date: 최신순
        - relevance: 관련도순
        - viewCount: 조회수순
        """
        if not settings.youtube_api_key:
            raise HTTPException(
                status_code=500,
                detail="YOUTUBE_API_KEY가 설정되지 않았습니다. .env를 확인해주세요.",
            )

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": order,
            "regionCode": "KR",
            "relevanceLanguage": "ko",
            "safeSearch": "moderate",
            "key": settings.youtube_api_key,
        }

        try:
            response = requests.get(
                self.YOUTUBE_SEARCH_API_URL,
                params=params,
                timeout=10,
            )
            response.raise_for_status()

        except requests.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"YouTube Data API 호출 중 오류가 발생했습니다: {str(e)}",
            )

        data = response.json()
        return data.get("items", [])


def get_youtube_client() -> YoutubeClient:
    """
    YoutubeClient 인스턴스를 반환합니다.
    """
    return YoutubeClient()