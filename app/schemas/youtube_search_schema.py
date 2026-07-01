# ============================================================
# 파일 위치: app/schemas/youtube_search_schema.py
# 역할:
#   - 유튜브 경제 영상 검색 API의 응답 schema를 정의합니다.
#   - 프론트에서 영상 카드/iframe을 만들 수 있도록 필요한 정보를 반환합니다.
# ============================================================

from typing import List, Optional

from pydantic import BaseModel


class YoutubeSearchItem(BaseModel):
    """
    유튜브 검색 결과 영상 1개에 대한 응답 schema입니다.
    """

    video_id: str
    title: str
    description: Optional[str] = None
    channel_title: Optional[str] = None
    published_at: Optional[str] = None
    thumbnail_url: Optional[str] = None
    watch_url: str
    embed_url: str


class YoutubeSearchResponse(BaseModel):
    """
    유튜브 영상 검색 응답 schema입니다.
    """

    query: str
    total_count: int
    items: List[YoutubeSearchItem]