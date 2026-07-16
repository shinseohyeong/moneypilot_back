# ============================================================
# 파일 위치: app/routers/youtube_router.py
# 역할:
#   - 유튜브 영상 검색 관련 API 엔드포인트를 정의합니다.
# ============================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.youtube_search_schema import (
    YoutubeSearchResponse,
    YoutubeSummaryRequest,
    YoutubeSummaryResponse,
)
from app.services.youtube_search_service import YoutubeSearchService


router = APIRouter()


def get_youtube_search_service(
    db: Session = Depends(get_db),
) -> YoutubeSearchService:
    """
    YoutubeSearchService 의존성 주입 함수입니다.
    """
    return YoutubeSearchService(db)


@router.get(
    "/search",
    response_model=YoutubeSearchResponse,
    summary="유튜브 경제 영상 검색",
)
def search_youtube_videos(
    query: str = Query(..., description="검색어 예: 오늘 경제 뉴스, 금리 교육 영상"),
    max_results: int = Query(default=6, ge=1, le=10),
    order: str = Query(default="date", description="date, relevance, viewCount"),
    service: YoutubeSearchService = Depends(get_youtube_search_service),
) -> YoutubeSearchResponse:
    """
    검색어를 기반으로 경제/금융 관련 유튜브 영상을 검색합니다.
    """
    return service.search_youtube_videos(
        query=query,
        max_results=max_results,
        order=order,
    )

@router.post(
    "/summary",
    response_model=YoutubeSummaryResponse,
    summary="유튜브 경제 영상 요약",
)
def summarize_youtube_video(
    request: YoutubeSummaryRequest,
    service: YoutubeSearchService = Depends(get_youtube_search_service),
) -> YoutubeSummaryResponse:
    """
    선택한 유튜브 영상의 제목, 설명, 자막을 기반으로 경제/금융 요약을 생성합니다.
    """
    return service.summarize_youtube_video(request)