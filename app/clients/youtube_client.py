# ============================================================
# 파일 위치: app/clients/youtube_client.py
# 역할:
#   - YouTube Data API v3를 호출해 공개 유튜브 영상을 검색합니다.
#   - service가 API 호출 세부사항을 몰라도 되도록 client로 분리합니다.
#   - 영상 메타데이터를 조회하고, 자막 수집을 시도합니다.
# ============================================================

import re
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import requests
from fastapi import HTTPException
from youtube_transcript_api import YouTubeTranscriptApi

from app.core.config import settings


class YoutubeClient:
    """
    YouTube Data API 호출 client입니다.
    """

    YOUTUBE_SEARCH_API_URL = "https://www.googleapis.com/youtube/v3/search"
    YOUTUBE_VIDEO_API_URL = "https://www.googleapis.com/youtube/v3/videos"

    def search_videos(
        self,
        query: str,
        max_results: int = 6,
        order: str = "date",
    ) -> List[Dict[str, Any]]:
        """
        검색어를 기반으로 공개 유튜브 영상을 검색합니다.
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
                timeout=(3, 10),
            )
            response.raise_for_status()

        except requests.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"YouTube Data API 호출 중 오류가 발생했습니다: {str(e)}",
            )

        data = response.json()
        return data.get("items", [])

    def extract_video_id(self, youtube_url: str) -> str:
        """
        다양한 YouTube URL 형식에서 video_id를 추출합니다.
        """
        parsed = urlparse(youtube_url)

        if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
            query = parse_qs(parsed.query)
            video_ids = query.get("v")

            if video_ids:
                return video_ids[0]

            path_parts = [part for part in parsed.path.split("/") if part]

            if len(path_parts) >= 2 and path_parts[0] in ("shorts", "embed"):
                return path_parts[1]

        if parsed.hostname in ("youtu.be", "www.youtu.be"):
            return parsed.path.lstrip("/")

        if re.fullmatch(r"[A-Za-z0-9_-]{11}", youtube_url):
            return youtube_url

        raise HTTPException(
            status_code=400,
            detail="유효한 YouTube URL 또는 video_id가 아닙니다.",
        )

    def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        YouTube Data API로 영상 제목/설명/썸네일을 조회합니다.
        """
        if not settings.youtube_api_key:
            raise HTTPException(
                status_code=500,
                detail="YOUTUBE_API_KEY가 설정되지 않았습니다. .env를 확인해주세요.",
            )

        params = {
            "part": "snippet",
            "id": video_id,
            "key": settings.youtube_api_key,
        }

        try:
            response = requests.get(
                self.YOUTUBE_VIDEO_API_URL,
                params=params,
                timeout=(3, 10),
            )
            response.raise_for_status()

        except requests.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"YouTube 영상 정보 조회 중 오류가 발생했습니다: {str(e)}",
            )

        data = response.json()
        items = data.get("items", [])

        if not items:
            raise HTTPException(
                status_code=404,
                detail="해당 YouTube 영상을 찾을 수 없습니다.",
            )

        snippet = items[0].get("snippet", {})
        thumbnails = snippet.get("thumbnails", {})

        thumbnail_url = None

        if thumbnails.get("high"):
            thumbnail_url = thumbnails["high"].get("url")
        elif thumbnails.get("medium"):
            thumbnail_url = thumbnails["medium"].get("url")
        elif thumbnails.get("default"):
            thumbnail_url = thumbnails["default"].get("url")

        return {
            "video_id": video_id,
            "title": snippet.get("title") or "",
            "description": snippet.get("description") or "",
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),
            "thumbnail_url": thumbnail_url,
            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
            "embed_url": f"https://www.youtube.com/embed/{video_id}",
        }

    def get_transcript_text(self, video_id: str) -> Optional[str]:
        """
        YouTube 영상 자막을 조회합니다.

        자막이 없거나 접근에 실패하면 None을 반환합니다.
        """
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript = ytt_api.fetch(
                video_id,
                languages=["ko", "en"],
            )

            texts = []

            for snippet in transcript:
                text = getattr(snippet, "text", None)

                if text:
                    texts.append(text)

            transcript_text = " ".join(texts).strip()

            return transcript_text or None

        except Exception:
            return None


def get_youtube_client() -> YoutubeClient:
    return YoutubeClient()