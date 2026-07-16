# ============================================================
# 파일 위치: app/repositories/stock_alert_repository.py
# 역할:
#   - 관심종목 뉴스 알림 생성/조회에 필요한 DB 접근을 담당합니다.
#   - commit/rollback은 하지 않습니다.
# ============================================================

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.news_model import (
    NewsArticle,
    NewsSectorMapping,
    NewsSummary,
    SectorInsight,
    StockNewsMapping,
)
from app.models.stock_model import Stock, StockSector, StockWatchlist

# StockAlert 모델 파일명에 맞춰 import 경로를 조정하세요.
from app.models.alert_model import StockAlert


class StockAlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_user_watchlist_stocks(
        self,
        user_id: int,
    ) -> List[Tuple[StockWatchlist, Stock]]:
        """
        사용자의 관심종목을 조회합니다.
        """
        return (
            self.db.query(StockWatchlist, Stock)
            .join(Stock, Stock.id == StockWatchlist.stock_id)
            .filter(
                StockWatchlist.user_id == user_id,
                Stock.is_active == True,  # noqa: E712
            )
            .all()
        )

    def list_recent_stock_news(
        self,
        stock_ids: List[int],
        start_datetime: datetime,
        limit: int = 50,
    ) -> List[Tuple[Stock, NewsArticle]]:
        """
        관심종목에 연결된 최근 뉴스를 조회합니다.
        """
        if not stock_ids:
            return []

        return (
            self.db.query(Stock, NewsArticle)
            .join(StockNewsMapping, StockNewsMapping.stock_id == Stock.id)
            .join(NewsArticle, NewsArticle.id == StockNewsMapping.news_id)
            .filter(
                Stock.id.in_(stock_ids),
                NewsArticle.is_active == True,  # noqa: E712
                or_(
                    and_(
                        NewsArticle.published_at.isnot(None),
                        NewsArticle.published_at >= start_datetime,
                    ),
                    and_(
                        NewsArticle.published_at.is_(None),
                        NewsArticle.collected_at >= start_datetime,
                    ),
                ),
            )
            .order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())
            .limit(limit)
            .all()
        )

    def get_latest_summary_by_news_id(
        self,
        news_id: int,
    ) -> Optional[NewsSummary]:
        """
        뉴스의 최신 요약/감정분석 결과를 조회합니다.
        """
        return (
            self.db.query(NewsSummary)
            .filter(NewsSummary.news_id == news_id)
            .order_by(NewsSummary.id.desc())
            .first()
        )

    def list_news_sectors(
        self,
        news_id: int,
    ) -> List[Tuple[NewsSectorMapping, StockSector]]:
        """
        뉴스에 연결된 섹터 분류 결과를 조회합니다.
        """
        return (
            self.db.query(NewsSectorMapping, StockSector)
            .join(StockSector, StockSector.id == NewsSectorMapping.sector_id)
            .filter(NewsSectorMapping.news_id == news_id)
            .all()
        )

    def get_latest_sector_insight(
        self,
        sector_id: int,
    ) -> Optional[SectorInsight]:
        """
        섹터의 최신 인사이트를 조회합니다.
        """
        return (
            self.db.query(SectorInsight)
            .filter(SectorInsight.sector_id == sector_id)
            .order_by(SectorInsight.insight_date.desc(), SectorInsight.id.desc())
            .first()
        )

    def get_existing_alert(
        self,
        user_id: int,
        alert_type: str,
        stock_id: int,
        news_id: int,
    ) -> Optional[StockAlert]:
        """
        같은 사용자/종목/뉴스/알림유형으로 이미 생성된 알림이 있는지 확인합니다.
        """
        return (
            self.db.query(StockAlert)
            .filter(
                StockAlert.user_id == user_id,
                StockAlert.alert_type == alert_type,
                StockAlert.stock_id == stock_id,
                StockAlert.news_id == news_id,
            )
            .first()
        )

    def create_alert(self, alert: StockAlert) -> StockAlert:
        """
        알림을 저장합니다.
        """
        self.db.add(alert)
        self.db.flush()
        return alert

    def list_alerts(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Tuple[StockAlert, Optional[Stock], Optional[StockSector]]]:
        """
        사용자 알림 목록을 조회합니다.
        """
        query = (
            self.db.query(StockAlert, Stock, StockSector)
            .outerjoin(Stock, Stock.id == StockAlert.stock_id)
            .outerjoin(StockSector, StockSector.id == StockAlert.sector_id)
            .filter(StockAlert.user_id == user_id)
        )

        if unread_only:
            query = query.filter(StockAlert.is_read == False)  # noqa: E712

        return (
            query.order_by(StockAlert.created_at.desc())
            .limit(limit)
            .all()
        )

    def count_unread_alerts(self, user_id: int) -> int:
        """
        읽지 않은 알림 수를 조회합니다.
        """
        return (
            self.db.query(StockAlert)
            .filter(
                StockAlert.user_id == user_id,
                StockAlert.is_read == False,  # noqa: E712
            )
            .count()
        )

    def get_user_alert_by_id(
        self,
        alert_id: int,
        user_id: int,
    ) -> Optional[StockAlert]:
        """
        특정 사용자의 알림 1건을 조회합니다.

        alert_id와 user_id를 함께 검사하여
        다른 사용자의 알림에 접근하지 못하도록 합니다.
        """
        return (
            self.db.query(StockAlert)
            .filter(
                StockAlert.id == alert_id,
                StockAlert.user_id == user_id,
            )
            .first()
        )