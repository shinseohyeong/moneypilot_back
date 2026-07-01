# ============================================================
# 파일 위치: app/services/youtube_search_service.py
# 역할:
#   - 유튜브 경제 영상 검색 비즈니스 로직을 담당합니다.
#   - YouTube API 결과를 프론트에서 사용하기 쉬운 응답 형태로 변환합니다.
# ============================================================

import html
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.clients.youtube_client import get_youtube_client
from app.schemas.youtube_search_schema import (
    YoutubeSearchItem,
    YoutubeSearchResponse,
)


class YoutubeSearchService:
    """
    유튜브 경제 영상 검색 service입니다.
    """

    ALLOWED_ORDERS = {"date", "relevance", "viewCount"}

    def __init__(self, db: Session):
        self.db = db
        self.youtube_client = get_youtube_client()

    def search_youtube_videos(
        self,
        query: str,
        max_results: int = 5,
        order: str = "date",
    ) -> YoutubeSearchResponse:
        """
        사용자의 검색어로 경제/금융 관련 유튜브 영상을 검색합니다.
        """
        cleaned_query = query.strip()

        if not cleaned_query:
            raise HTTPException(
                status_code=400,
                detail="검색어를 입력해주세요.",
            )

        if order not in self.ALLOWED_ORDERS:
            raise HTTPException(
                status_code=400,
                detail="order는 date, relevance, viewCount 중 하나여야 합니다.",
            )

        # 너무 일반적인 검색어일 때 경제/금융 맥락을 살짝 보강합니다.
        search_query = self._build_search_query(cleaned_query)

        raw_items = self.youtube_client.search_videos(
            query=search_query,
            max_results=max_results,
            order=order,
        )

        items = [self._to_search_item(item) for item in raw_items]
        items = [item for item in items if item is not None]

        return YoutubeSearchResponse(
            query=cleaned_query,
            total_count=len(items),
            items=items,
        )

    def _build_search_query(self, query: str) -> str:
        """
        사용자의 자연어 검색어를 유튜브 검색용 query로 보정합니다.
        """
        economy_keywords = [
            "경제",
            "금리",
            "주식",
            "증시",
            "환율",
            "코스피",
            "부동산",
            "투자",
            "금융",
        ]

        if any(keyword in query for keyword in economy_keywords):
            return query

        return f"{query} 경제 금융"

    def _to_search_item(self, item: dict) -> YoutubeSearchItem | None:
        """
        YouTube API 응답 item을 YoutubeSearchItem으로 변환합니다.
        """
        video_id = item.get("id", {}).get("videoId")

        if not video_id:
            return None

        snippet = item.get("snippet", {})
        thumbnails = snippet.get("thumbnails", {})

        thumbnail_url = None

        if thumbnails.get("high"):
            thumbnail_url = thumbnails["high"].get("url")
        elif thumbnails.get("medium"):
            thumbnail_url = thumbnails["medium"].get("url")
        elif thumbnails.get("default"):
            thumbnail_url = thumbnails["default"].get("url")

        return YoutubeSearchItem(
            video_id=video_id,
            title=html.unescape(snippet.get("title") or ""),
            description=html.unescape(snippet.get("description") or ""),
            channel_title=html.unescape(snippet.get("channelTitle") or ""),
            published_at=snippet.get("publishedAt"),
            thumbnail_url=thumbnail_url,
            watch_url=f"https://www.youtube.com/watch?v={video_id}",
            embed_url=f"https://www.youtube.com/embed/{video_id}",
        )