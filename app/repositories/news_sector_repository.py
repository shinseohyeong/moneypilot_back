# ============================================================
# 파일 위치: app/repositories/news_sector_repository.py
# 역할:
#   - 뉴스 섹터 분류에 필요한 DB 조회/저장 작업을 담당합니다.
#   - commit/rollback은 하지 않습니다.
# ============================================================

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.news_model import NewsArticle, NewsSectorMapping, NewsSummary
from app.models.stock_model import StockSector, SectorKeyword


class NewsSectorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_article_by_id(self, news_id: int) -> Optional[NewsArticle]:
        """
        뉴스 1건을 조회합니다.
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
        뉴스의 최신 요약 1건을 조회합니다.
        """
        return (
            self.db.query(NewsSummary)
            .filter(NewsSummary.news_id == news_id)
            .order_by(NewsSummary.id.desc())
            .first()
        )

    def list_active_sector_keywords(self) -> List[Tuple[StockSector, SectorKeyword]]:
        """
        활성화된 섹터와 섹터 키워드를 함께 조회합니다.
        """
        return (
            self.db.query(StockSector, SectorKeyword)
            .join(SectorKeyword, SectorKeyword.sector_id == StockSector.id)
            .filter(StockSector.is_active == True)  # noqa: E712
            .all()
        )

    def get_mapping(
        self,
        news_id: int,
        sector_id: int,
    ) -> Optional[NewsSectorMapping]:
        """
        특정 뉴스-섹터 매핑이 이미 존재하는지 확인합니다.
        """
        return (
            self.db.query(NewsSectorMapping)
            .filter(
                NewsSectorMapping.news_id == news_id,
                NewsSectorMapping.sector_id == sector_id,
            )
            .first()
        )

    def create_mapping(self, mapping: NewsSectorMapping) -> NewsSectorMapping:
        """
        뉴스-섹터 매핑을 새로 저장합니다.
        """
        self.db.add(mapping)
        self.db.flush()
        return mapping

    def list_news_sector_mappings(
        self,
        news_id: int,
    ) -> List[Tuple[NewsSectorMapping, StockSector]]:
        """
        특정 뉴스의 섹터 분류 결과를 조회합니다.
        """
        return (
            self.db.query(NewsSectorMapping, StockSector)
            .join(StockSector, StockSector.id == NewsSectorMapping.sector_id)
            .filter(NewsSectorMapping.news_id == news_id)
            .order_by(NewsSectorMapping.relevance_score.desc())
            .all()
        )