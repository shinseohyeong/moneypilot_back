# ============================================================
# 파일 위치: app/services/news_summary_service.py
# 역할:
#   - 뉴스 요약 생성/조회 비즈니스 로직을 담당합니다.
#   - news_articles를 조회하고, LLM으로 요약한 뒤 news_summaries에 저장합니다.
#   - commit/rollback 트랜잭션 처리를 담당합니다.
# ============================================================

import json
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.clients.llm_client import get_llm_client
from app.models.news_model import NewsSummary
from app.repositories.news_summary_repository import NewsSummaryRepository
from app.schemas.news_summary_schema import NewsSummaryResponse
from app.core.disclaimer import get_investment_disclaimer

class NewsSummaryService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = NewsSummaryRepository(db)
        self.llm_client = get_llm_client()

    def create_news_summary(
        self,
        news_id: int,
        force_refresh: bool = False,
    ) -> NewsSummaryResponse:
        """
        뉴스 요약 생성

        흐름:
        1. news_id로 뉴스 조회
        2. 기존 요약 존재 여부 확인
        3. force_refresh=False이고 기존 요약이 있으면 기존 요약 반환
        4. 없거나 force_refresh=True이면 LLM 요약 생성
        5. news_summaries에 저장 또는 갱신
        6. commit
        """
        article = self.repository.get_article_by_id(news_id)

        if not article:
            raise HTTPException(
                status_code=404,
                detail="해당 뉴스를 찾을 수 없습니다.",
            )

        existing_summary = self.repository.get_latest_summary_by_news_id(news_id)

        if existing_summary and not force_refresh:
            return self._to_response(existing_summary)

        try:
            llm_result = self.llm_client.summarize_news(
                title=article.title,
                description=article.description,
                content=article.content,
            )

            if existing_summary and force_refresh:
                summary = existing_summary
                summary.one_line_summary = llm_result.get("one_line_summary")
                summary.summary_text = llm_result.get("summary_text")
                summary.positive_factors = self._dump_list(
                    llm_result.get("positive_factors")
                )
                summary.risk_factors = self._dump_list(
                    llm_result.get("risk_factors")
                )
                summary.investment_note = llm_result.get("investment_note")
                summary.sentiment = llm_result.get("sentiment")
                summary.model_name = self.llm_client.model_name

                saved_summary = self.repository.update_summary(summary)

            else:
                summary = NewsSummary(
                    news_id=news_id,
                    one_line_summary=llm_result.get("one_line_summary"),
                    summary_text=llm_result.get("summary_text"),
                    positive_factors=self._dump_list(
                        llm_result.get("positive_factors")
                    ),
                    risk_factors=self._dump_list(
                        llm_result.get("risk_factors")
                    ),
                    investment_note=llm_result.get("investment_note"),
                    sentiment=llm_result.get("sentiment"),
                    model_name=self.llm_client.model_name,
                )

                saved_summary = self.repository.create_summary(summary)

            self.db.commit()
            self.db.refresh(saved_summary)

            return self._to_response(saved_summary)

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"뉴스 요약 생성 중 오류가 발생했습니다: {str(e)}",
            )

    def get_news_summary(self, news_id: int) -> NewsSummaryResponse:
        """
        저장된 뉴스 요약 조회
        """
        article = self.repository.get_article_by_id(news_id)

        if not article:
            raise HTTPException(
                status_code=404,
                detail="해당 뉴스를 찾을 수 없습니다.",
            )

        summary = self.repository.get_latest_summary_by_news_id(news_id)

        if not summary:
            raise HTTPException(
                status_code=404,
                detail="해당 뉴스의 요약이 아직 생성되지 않았습니다.",
            )

        return self._to_response(summary)

    # ------------------------------------------------------------
    # 내부 변환 함수
    # ------------------------------------------------------------
    def _to_response(self, summary: NewsSummary) -> NewsSummaryResponse:
        """
        NewsSummary 모델을 API 응답 schema로 변환합니다.
        """
        return NewsSummaryResponse(
            summary_id=summary.id,
            news_id=summary.news_id,
            one_line_summary=summary.one_line_summary,
            summary_text=summary.summary_text,
            positive_factors=self._load_list(summary.positive_factors),
            risk_factors=self._load_list(summary.risk_factors),
            investment_note=summary.investment_note,
            sentiment=summary.sentiment,
            model_name=summary.model_name,
            disclaimer=get_investment_disclaimer(),
            created_at=getattr(summary, "created_at", None),
            updated_at=getattr(summary, "updated_at", None),
        )

    def _dump_list(self, value: Any) -> str:
        """
        LLM이 반환한 list 값을 DB에 저장하기 위해 JSON 문자열로 변환합니다.

        positive_factors, risk_factors 컬럼이 Text/String이면 이 방식이 안전합니다.
        컬럼이 JSON 타입이라면 나중에 이 부분은 list 그대로 저장하도록 바꿀 수 있습니다.
        """
        if value is None:
            value = []

        if not isinstance(value, list):
            value = [str(value)]

        return json.dumps(value, ensure_ascii=False)

    def _load_list(self, value: Optional[Any]) -> List[str]:
        """
        DB에 저장된 JSON 문자열을 list[str]로 복원합니다.
        """
        if value is None:
            return []

        if isinstance(value, list):
            return value

        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
            return [str(parsed)]

        except Exception:
            return [str(value)]