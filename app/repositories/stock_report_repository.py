# ============================================================
# 파일 위치: app/repositories/stock_report_repository.py
# 역할:
#   - 관심종목 요약 리포트 생성/조회에 필요한 DB 접근을 담당합니다.
#   - commit/rollback은 하지 않습니다.
# ============================================================

from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.news_model import (
    NewsArticle,
    NewsSectorMapping,
    NewsSummary,
    SectorInsight,
    StockNewsMapping,
    StockReport,
    StockReportItem,
)
from app.models.stock_model import (
    Stock,
    StockPrice,
    StockSector,
    StockWatchlist,
)


class StockReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_user_watchlist_stocks(
        self,
        user_id: int,
    ) -> List[Tuple[StockWatchlist, Stock]]:
        """
        사용자의 관심종목 목록을 조회합니다.
        """
        return (
            self.db.query(StockWatchlist, Stock)
            .join(Stock, Stock.id == StockWatchlist.stock_id)
            .filter(
                StockWatchlist.user_id == user_id,
                Stock.is_active == True,  # noqa: E712
            )
            .order_by(StockWatchlist.created_at.desc())
            .all()
        )

    def get_latest_price(self, stock_id: int) -> Optional[StockPrice]:
        """
        특정 종목의 최신 시세를 조회합니다.
        """
        return (
            self.db.query(StockPrice)
            .filter(StockPrice.stock_id == stock_id)
            .order_by(StockPrice.price_date.desc())
            .first()
        )

    def list_recent_news_summaries_by_stock(
        self,
        stock_id: int,
        limit: int = 3,
    ) -> List[Tuple[NewsArticle, Optional[NewsSummary]]]:
        """
        특정 종목에 연결된 최근 뉴스와 요약을 조회합니다.
        """
        return (
            self.db.query(NewsArticle, NewsSummary)
            .join(StockNewsMapping, StockNewsMapping.news_id == NewsArticle.id)
            .outerjoin(NewsSummary, NewsSummary.news_id == NewsArticle.id)
            .filter(
                StockNewsMapping.stock_id == stock_id,
                NewsArticle.is_active == True,  # noqa: E712
            )
            .order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())
            .limit(limit)
            .all()
        )

    def list_sector_insights_by_stock(
        self,
        stock_id: int,
        limit: int = 3,
    ) -> List[Tuple[StockSector, SectorInsight]]:
        """
        특정 종목의 뉴스에 연결된 섹터 인사이트를 조회합니다.
        """
        return (
            self.db.query(StockSector, SectorInsight)
            .join(NewsSectorMapping, NewsSectorMapping.sector_id == StockSector.id)
            .join(StockNewsMapping, StockNewsMapping.news_id == NewsSectorMapping.news_id)
            .join(SectorInsight, SectorInsight.sector_id == StockSector.id)
            .filter(StockNewsMapping.stock_id == stock_id)
            .order_by(SectorInsight.insight_date.desc(), SectorInsight.issue_score.desc())
            .limit(limit)
            .all()
        )

    def create_report(self, report: StockReport) -> StockReport:
        """
        리포트 본문을 저장합니다.
        """
        self.db.add(report)
        self.db.flush()
        return report

    def create_report_item(self, item: StockReportItem) -> StockReportItem:
        """
        리포트 종목별 항목을 저장합니다.
        """
        self.db.add(item)
        self.db.flush()
        return item

    def get_report_by_id(self, report_id: int) -> Optional[StockReport]:
        """
        리포트 1건을 조회합니다.
        """
        return (
            self.db.query(StockReport)
            .filter(StockReport.id == report_id)
            .first()
        )

    def list_report_items(
        self,
        report_id: int,
    ) -> List[Tuple[StockReportItem, Stock]]:
        """
        리포트에 포함된 종목별 항목을 조회합니다.
        """
        return (
            self.db.query(StockReportItem, Stock)
            .join(Stock, Stock.id == StockReportItem.stock_id)
            .filter(StockReportItem.report_id == report_id)
            .order_by(StockReportItem.id.asc())
            .all()
        )

    def list_reports_by_user(
        self,
        user_id: int,
        limit: int = 20,
    ) -> List[StockReport]:
        """
        사용자의 리포트 목록을 조회합니다.
        """
        return (
            self.db.query(StockReport)
            .filter(StockReport.user_id == user_id)
            .order_by(StockReport.created_at.desc())
            .limit(limit)
            .all()
        )