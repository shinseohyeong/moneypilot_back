# ============================================================
# 파일 위치: app/repositories/news_repository.py
# 역할:
#   - 뉴스 관련 DB 조회/저장을 담당합니다.
#   - commit/rollback은 절대 하지 않습니다.
#   - 트랜잭션 처리는 service에서 담당합니다.
# ============================================================

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.news_model import NewsArticle, StockNewsMapping
from app.models.stock_model import Stock


class NewsRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------
    # Stock 조회
    # ------------------------------------------------------------
    def get_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        """
        stock_id로 종목을 조회합니다.

        종목 뉴스 수집 시
        검색어를 자동으로 만들기 위해 사용합니다.
        """
        return (
            self.db.query(Stock)
            .filter(Stock.id == stock_id)
            .first()
        )

    # ------------------------------------------------------------
    # NewsArticle 조회/저장
    # ------------------------------------------------------------
    def get_article_by_url_hash(self, url_hash: str) -> Optional[NewsArticle]:
        """
        url_hash 기준으로 이미 저장된 뉴스인지 확인합니다.
        """
        return (
            self.db.query(NewsArticle)
            .filter(NewsArticle.url_hash == url_hash)
            .first()
        )

    def create_article(self, article: NewsArticle) -> NewsArticle:
        """
        뉴스 기사 1건을 DB 세션에 추가합니다.

        주의:
        - 여기서는 commit하지 않습니다.
        - service에서 commit합니다.
        """
        self.db.add(article)
        self.db.flush()
        self.db.refresh(article)
        return article

    def list_economy_news(self, limit: int = 20) -> List[NewsArticle]:
        """
        경제 뉴스 목록 조회

        현재 모델에는 news_type 컬럼이 없기 때문에,
        1차 MVP에서는 stock_news_mappings에 연결되지 않은 뉴스를
        경제/일반 뉴스로 간주합니다.

        나중에 경제 뉴스와 종목 뉴스가 겹칠 수 있으면
        news_articles에 news_type 컬럼을 추가하는 것도 고려할 수 있습니다.
        """
        mapped_news_id_subquery = (
            self.db.query(StockNewsMapping.news_id)
            .subquery()
        )

        return (
            self.db.query(NewsArticle)
            .filter(NewsArticle.is_active == True)  # noqa: E712
            .filter(~NewsArticle.id.in_(mapped_news_id_subquery))
            .order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------
    # StockNewsMapping 조회/저장
    # ------------------------------------------------------------
    def get_stock_mapping(
        self,
        news_id: int,
        stock_id: int,
    ) -> Optional[StockNewsMapping]:
        """
        특정 뉴스와 특정 종목이 이미 연결되어 있는지 확인합니다.
        """
        return (
            self.db.query(StockNewsMapping)
            .filter(
                StockNewsMapping.news_id == news_id,
                StockNewsMapping.stock_id == stock_id,
            )
            .first()
        )

    def create_stock_mapping(
        self,
        mapping: StockNewsMapping,
    ) -> StockNewsMapping:
        """
        뉴스-종목 매핑을 생성합니다.

        주의:
        - 여기서는 commit하지 않습니다.
        - service에서 commit합니다.
        """
        self.db.add(mapping)
        self.db.flush()
        self.db.refresh(mapping)
        return mapping

    def list_stock_news(
        self,
        stock_id: int,
        limit: int = 20,
    ) -> List[Tuple[NewsArticle, StockNewsMapping]]:
        """
        특정 종목에 매핑된 뉴스를 최신순으로 조회합니다.

        반환:
        - NewsArticle
        - StockNewsMapping
        """
        return (
            self.db.query(NewsArticle, StockNewsMapping)
            .join(
                StockNewsMapping,
                StockNewsMapping.news_id == NewsArticle.id,
            )
            .filter(
                StockNewsMapping.stock_id == stock_id,
                NewsArticle.is_active == True,  # noqa: E712
            )
            .order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())
            .limit(limit)
            .all()
        )