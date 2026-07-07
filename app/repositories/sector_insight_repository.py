# ============================================================
# 파일 위치: app/repositories/sector_insight_repository.py
# 역할:
#   - 섹터 인사이트 생성에 필요한 DB 조회/저장 작업을 담당합니다.
#   - commit/rollback은 하지 않습니다.
# ============================================================

from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.news_model import (
    NewsArticle,
    NewsSectorMapping,
    NewsSummary,
    SectorInsight,
)
from app.models.stock_model import StockSector


class SectorInsightRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_sector_news_rows(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> List[Tuple[NewsSectorMapping, StockSector, NewsArticle]]:
        return (
            self.db.query(NewsSectorMapping, StockSector, NewsArticle)
            .join(StockSector, StockSector.id == NewsSectorMapping.sector_id)
            .join(NewsArticle, NewsArticle.id == NewsSectorMapping.news_id)
            .filter(
                NewsArticle.is_active == True,  # noqa: E712
                or_(
                    and_(
                        NewsArticle.published_at.isnot(None),
                        NewsArticle.published_at >= start_datetime,
                        NewsArticle.published_at <= end_datetime,
                    ),
                    and_(
                        NewsArticle.published_at.is_(None),
                        NewsArticle.collected_at >= start_datetime,
                        NewsArticle.collected_at <= end_datetime,
                    ),
                ),
            )
            .all()
        )

    def get_latest_summary_by_news_id(
        self,
        news_id: int,
    ) -> Optional[NewsSummary]:
        return (
            self.db.query(NewsSummary)
            .filter(NewsSummary.news_id == news_id)
            .order_by(NewsSummary.id.desc())
            .first()
        )

    def get_insight(
        self,
        sector_id: int,
        insight_date: date,
        period_days: int,
    ) -> Optional[SectorInsight]:
        return (
            self.db.query(SectorInsight)
            .filter(
                SectorInsight.sector_id == sector_id,
                SectorInsight.insight_date == insight_date,
                SectorInsight.period_days == period_days,
            )
            .first()
        )

    def create_insight(self, insight: SectorInsight) -> SectorInsight:
        self.db.add(insight)
        self.db.flush()
        return insight

    def list_insights(
        self,
        insight_date: date,
        period_days: int,
    ) -> List[Tuple[SectorInsight, StockSector]]:
        return (
            self.db.query(SectorInsight, StockSector)
            .join(StockSector, StockSector.id == SectorInsight.sector_id)
            .filter(
                SectorInsight.insight_date == insight_date,
                SectorInsight.period_days == period_days,
            )
            .order_by(SectorInsight.issue_score.desc())
            .all()
        )