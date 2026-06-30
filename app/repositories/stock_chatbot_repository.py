# ============================================================
# 파일 위치: app/repositories/stock_chatbot_repository.py
# 역할:
#   - 주식 챗봇 답변 생성에 필요한 DB 데이터를 조회합니다.
#   - 기존 StockReportRepository의 조회 메서드를 재사용합니다.
#   - repository 단에서는 commit/rollback을 처리하지 않습니다.
# ============================================================

from sqlalchemy.orm import Session

from app.repositories.stock_report_repository import StockReportRepository


class StockChatbotRepository:
    """
    주식 챗봇 전용 repository입니다.
    """

    def __init__(self, db: Session):
        self.db = db
        self.stock_report_repository = StockReportRepository(db)

    def list_user_watchlist_stocks(self, user_id: int):
        """
        사용자의 관심종목 목록을 조회합니다.
        """
        return self.stock_report_repository.list_user_watchlist_stocks(
            user_id=user_id,
        )

    def get_latest_price(self, stock_id: int):
        """
        종목의 최신 시세를 조회합니다.
        """
        return self.stock_report_repository.get_latest_price(
            stock_id=stock_id,
        )

    def list_recent_news_summaries_by_stock(
        self,
        stock_id: int,
        limit: int = 3,
    ):
        """
        종목과 연결된 최근 뉴스 요약을 조회합니다.
        """
        return self.stock_report_repository.list_recent_news_summaries_by_stock(
            stock_id=stock_id,
            limit=limit,
        )

    def list_sector_insights_by_stock(
        self,
        stock_id: int,
        limit: int = 2,
    ):
        """
        종목과 연결된 섹터 인사이트를 조회합니다.
        """
        return self.stock_report_repository.list_sector_insights_by_stock(
            stock_id=stock_id,
            limit=limit,
        )