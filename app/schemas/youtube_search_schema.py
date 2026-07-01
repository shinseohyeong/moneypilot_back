# ============================================================
# 파일 위치: app/schemas/youtube_search_schema.py
# 역할:
#   - 유튜브 경제 영상 검색 API의 응답 schema를 정의합니다.
#   - 프론트에서 영상 카드/iframe을 만들 수 있도록 필요한 정보를 반환합니다.
# ============================================================

from typing import List, Optional

from pydantic import BaseModel, Field


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

class YoutubeSummaryRequest(BaseModel):
    """
    유튜브 영상 요약 요청 schema입니다.

    검색 API 결과에서 받은 video_id를 넣거나,
    사용자가 직접 youtube_url을 넣을 수 있습니다.
    """

    video_id: Optional[str] = Field(default=None, description="YouTube video_id")
    youtube_url: Optional[str] = Field(default=None, description="YouTube 영상 URL")
    manual_transcript: Optional[str] = Field(
        default=None,
        description="자막 수집 실패 시 사용자가 직접 입력한 자막/본문",
    )


class YoutubeSummaryResponse(BaseModel):
    """
    유튜브 영상 요약 응답 schema입니다.
    """

    video_id: str
    title: str
    description: Optional[str] = None
    channel_title: Optional[str] = None
    published_at: Optional[str] = None
    thumbnail_url: Optional[str] = None
    watch_url: str
    embed_url: str
    transcript_available: bool
    transcript_source: str
    summary: str
    disclaimer: str