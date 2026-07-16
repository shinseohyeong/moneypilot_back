# ============================================================
# 파일 위치: app/services/youtube_search_service.py
# 역할:
#   - 유튜브 경제 영상 검색 비즈니스 로직을 담당합니다.
#   - YouTube API 결과를 프론트에서 사용하기 쉬운 응답 형태로 변환합니다.
# ============================================================

import html

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.clients.llm_client import get_llm_client
from app.clients.youtube_client import get_youtube_client
from app.core.disclaimer import get_investment_disclaimer
from app.schemas.youtube_search_schema import (
    YoutubeSearchItem,
    YoutubeSearchResponse,
    YoutubeSummaryRequest,
    YoutubeSummaryResponse,
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
        max_results: int = 6,
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
    
    def summarize_youtube_video(
        self,
        request: YoutubeSummaryRequest,
    ) -> YoutubeSummaryResponse:
        """
        검색 결과에서 선택한 YouTube 영상을 요약합니다.
        """
        video_id = self._resolve_video_id(request)

        metadata = self.youtube_client.get_video_metadata(video_id=video_id)

        transcript_text = self.youtube_client.get_transcript_text(video_id=video_id)
        transcript_source = "youtube_transcript_api"

        if not transcript_text and request.manual_transcript:
            transcript_text = request.manual_transcript
            transcript_source = "manual_transcript"

        if not transcript_text:
            transcript_source = "metadata_only"

        summary = self._generate_youtube_summary(
            title=metadata["title"],
            description=metadata["description"],
            transcript_text=transcript_text,
        )

        return YoutubeSummaryResponse(
            video_id=metadata["video_id"],
            title=html.unescape(metadata["title"]),
            description=html.unescape(metadata["description"] or ""),
            channel_title=html.unescape(metadata["channel_title"] or ""),
            published_at=metadata["published_at"],
            thumbnail_url=metadata["thumbnail_url"],
            watch_url=metadata["watch_url"],
            embed_url=metadata["embed_url"],
            transcript_available=bool(transcript_text),
            transcript_source=transcript_source,
            summary=summary,
            disclaimer=get_investment_disclaimer(),
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
    
    def _resolve_video_id(
        self,
        request: YoutubeSummaryRequest,
    ) -> str:
        """
        요청에서 video_id를 결정합니다.
        """
        if request.video_id:
            return self.youtube_client.extract_video_id(request.video_id)

        if request.youtube_url:
            return self.youtube_client.extract_video_id(request.youtube_url)

        raise HTTPException(
            status_code=400,
            detail="video_id 또는 youtube_url 중 하나는 반드시 입력해야 합니다.",
        )

    def _generate_youtube_summary(
        self,
        title: str,
        description: str,
        transcript_text: str | None,
    ) -> str:
        """
        LLM으로 유튜브 경제 영상 요약을 생성합니다.
        """
        source_text = transcript_text or "자막이 없어 영상 제목과 설명만 제공됩니다."

        system_prompt = (
            "너는 MoneyPilot의 경제 영상 요약 assistant다. "
            "영상 제목, 설명, 자막을 바탕으로 핵심 내용을 요약한다. "
            "투자 권유, 매수/매도 추천, 수익 보장, 목표가 제시는 금지한다. "
            "제공된 정보에 없는 내용을 지어내지 않는다. "
            "한국어로 답변한다."
        )

        user_prompt = f"""
아래 유튜브 경제/금융 영상 정보를 요약해줘.

[영상 제목]
{title}

[영상 설명]
{description}

[영상 자막 또는 대체 텍스트]
{source_text[:12000]}

요약 형식:
1. 한 줄 요약
2. 핵심 내용 3~5개
3. 경제/금융 관점에서 참고할 포인트
4. 주의할 점
5. 투자 유의 문구

주의:
- 직접 투자 권유 금지
- 매수/매도 추천 금지
- 목표가 제시 금지
- 자막이 없으면 제목과 설명만 기반으로 요약했다고 밝혀줘
"""

        try:
            llm_client = get_llm_client()
            return llm_client.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"유튜브 영상 요약 LLM 호출 중 오류가 발생했습니다: {str(e)}",
            )