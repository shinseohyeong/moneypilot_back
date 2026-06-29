# ============================================================
# 파일 위치: app/services/news_sentiment_service.py
# 역할:
#   - 뉴스 감정분석 조회/분석 비즈니스 로직을 담당합니다.
#   - OpenAI를 직접 호출하지 않고, 기존 NewsSummaryService를 재사용합니다.
#   - news_summaries.sentiment 값을 감정분석 결과로 반환합니다.
# ============================================================

from typing import Any, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.disclaimer import get_investment_disclaimer
from app.schemas.news_sentiment_schema import NewsSentimentResponse
from app.services.news_summary_service import NewsSummaryService


class NewsSentimentService:
    def __init__(self, db: Session):
        self.db = db
        self.news_summary_service = NewsSummaryService(db)

    def get_news_sentiment(self, news_id: int) -> NewsSentimentResponse:
        """
        저장된 뉴스 요약 결과에서 sentiment를 조회합니다.

        요약이 없다면 새로 생성하지 않고 404를 반환합니다.
        """
        try:
            summary = self.news_summary_service.get_news_summary(news_id=news_id)
            return self._to_response(summary)

        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "감정분석 결과가 없습니다. "
                        "POST /api/v1/news/{news_id}/sentiment/analyze를 먼저 실행해주세요."
                    ),
                )
            raise

    def analyze_news_sentiment(
        self,
        news_id: int,
        force_refresh: bool = False,
    ) -> NewsSentimentResponse:
        """
        뉴스 감정분석을 실행합니다.

        내부적으로 기존 뉴스 요약 생성 기능을 재사용합니다.
        요약 생성 결과에 포함된 sentiment를 감정분석 결과로 반환합니다.
        """
        summary = self.news_summary_service.create_news_summary(
            news_id=news_id,
            force_refresh=force_refresh,
        )

        return self._to_response(summary)

    # ------------------------------------------------------------
    # 내부 함수
    # ------------------------------------------------------------
    def _to_response(self, summary: Any) -> NewsSentimentResponse:
        """
        NewsSummaryResponse를 NewsSentimentResponse로 변환합니다.
        """
        sentiment = self._normalize_sentiment(
            getattr(summary, "sentiment", None)
        )

        return NewsSentimentResponse(
            news_id=summary.news_id,
            summary_id=summary.summary_id,
            sentiment=sentiment,
            sentiment_label=self._to_korean_label(sentiment),
            one_line_summary=getattr(summary, "one_line_summary", None),
            positive_factors=self._safe_list(
                getattr(summary, "positive_factors", [])
            ),
            risk_factors=self._safe_list(
                getattr(summary, "risk_factors", [])
            ),
            investment_note=getattr(summary, "investment_note", None),
            model_name=getattr(summary, "model_name", None),
            disclaimer=get_investment_disclaimer(),
        )

    def _normalize_sentiment(self, sentiment: Any) -> str:
        """
        sentiment 값을 POSITIVE / NEUTRAL / NEGATIVE 중 하나로 정리합니다.
        """
        if not sentiment:
            return "NEUTRAL"

        normalized = str(sentiment).upper()

        if normalized not in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
            return "NEUTRAL"

        return normalized

    def _to_korean_label(self, sentiment: str) -> str:
        """
        영문 감정값을 화면 표시용 한글 라벨로 변환합니다.
        """
        labels = {
            "POSITIVE": "긍정",
            "NEUTRAL": "중립",
            "NEGATIVE": "부정",
        }

        return labels.get(sentiment, "중립")

    def _safe_list(self, value: Any) -> List[str]:
        """
        positive_factors, risk_factors 값을 안전하게 list[str]로 변환합니다.
        """
        if value is None:
            return []

        if isinstance(value, list):
            return [str(item) for item in value]

        return [str(value)]