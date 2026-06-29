# ============================================================
# 파일 위치: app/repositories/news_summary_repository.py
# 역할:
#   - 뉴스 원문 조회와 뉴스 요약 저장/조회 DB 작업을 담당합니다.
#   - commit/rollback은 하지 않습니다.
# ============================================================

from typing import Optional

from sqlalchemy.orm import Session

from app.models.news_model import NewsArticle, NewsSummary


class NewsSummaryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_article_by_id(self, news_id: int) -> Optional[NewsArticle]:
        """
        news_articles에서 뉴스 1건을 조회합니다.
        """
        return (
            self.db.query(NewsArticle)
            .filter(
                NewsArticle.id == news_id,
                NewsArticle.is_active == True,  # noqa: E712
            )
            .first()
        )

    def get_latest_summary_by_news_id(self, news_id: int) -> Optional[NewsSummary]:
        """
        해당 뉴스의 최신 요약 1건을 조회합니다.

        news_summaries.news_id가 unique라면 order_by는 없어도 되지만,
        혹시 여러 번 생성된 경우를 대비해 최신 id 기준으로 가져옵니다.
        """
        return (
            self.db.query(NewsSummary)
            .filter(NewsSummary.news_id == news_id)
            .order_by(NewsSummary.id.desc())
            .first()
        )

    def create_summary(self, summary: NewsSummary) -> NewsSummary:
        """
        새 뉴스 요약을 저장합니다.
        """
        self.db.add(summary)
        self.db.flush()
        return summary

    def update_summary(self, summary: NewsSummary) -> NewsSummary:
        """
        기존 뉴스 요약 객체의 변경 내용을 flush합니다.
        """
        self.db.flush()
        return summary