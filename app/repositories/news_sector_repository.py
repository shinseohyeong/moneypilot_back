# ============================================================
# 파일 위치: app/repositories/news_sector_repository.py
# 역할:
#   - 뉴스 섹터 분류에 필요한 DB 조회/저장 작업을 담당합니다.
#   - commit/rollback은 하지 않습니다.
# ============================================================

from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.dialects.mysql import insert as mysql_insert
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
    
    def upsert_mapping(
        self,
        news_id: int,
        sector_id: int,
        matched_keywords: List[str],
        relevance_score: Decimal,
    ) -> NewsSectorMapping:
        """
        뉴스-섹터 매핑을 저장합니다.

        같은 news_id, sector_id 조합이 이미 있으면
        키워드와 관련도 점수를 갱신합니다.
        """
        statement = mysql_insert(NewsSectorMapping).values(
            news_id=news_id,
            sector_id=sector_id,
            matched_keywords=matched_keywords,
            relevance_score=relevance_score,
        )

        statement = statement.on_duplicate_key_update(
            matched_keywords=statement.inserted.matched_keywords,
            relevance_score=statement.inserted.relevance_score,
        )

        self.db.execute(statement)
        self.db.flush()

        mapping = self.get_mapping(
            news_id=news_id,
            sector_id=sector_id,
        )

        if not mapping:
            raise RuntimeError("뉴스-섹터 매핑 저장 결과를 조회하지 못했습니다.")

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