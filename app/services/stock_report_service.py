# ============================================================
# 파일 위치: app/services/stock_report_service.py
# 역할:
#   - 관심종목 요약 리포트 생성/조회 비즈니스 로직을 담당합니다.
#   - 관심종목, 현재가, 뉴스 요약, 섹터 인사이트, 위험 요인을 조합합니다.
# ============================================================

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.news_model import StockReport, StockReportItem
from app.repositories.stock_report_repository import StockReportRepository
from app.schemas.stock_report_schema import (
    StockReportItemResponse,
    StockReportListItemResponse,
    StockReportListResponse,
    StockReportResponse,
)
from app.core.disclaimer import get_investment_disclaimer



class StockReportService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = StockReportRepository(db)

    def generate_stock_report(self, user_id: int) -> StockReportResponse:
        """
        사용자의 관심종목 요약 리포트를 생성합니다.
        """
        watchlist_rows = self.repository.list_user_watchlist_stocks(user_id=user_id)

        if not watchlist_rows:
            raise HTTPException(
                status_code=404,
                detail="관심종목이 없습니다. 관심종목을 먼저 등록해주세요.",
            )

        today = date.today()

        try:
            report = StockReport(
                user_id=user_id,
                report_date=today,
                report_title=f"{today} 관심종목 요약 리포트",
                market_summary="사용자의 관심종목을 기준으로 현재가, 관련 뉴스, 섹터 흐름을 종합한 리포트입니다.",
                sector_summary=None,
                watchlist_summary=f"총 {len(watchlist_rows)}개의 관심종목을 기준으로 리포트를 생성했습니다.",
                risk_summary=None,
                disclaimer=get_investment_disclaimer(),
            )

            self.repository.create_report(report)

            created_items = []

            sector_summary_parts = []
            risk_summary_parts = []

            for _, stock in watchlist_rows:
                latest_price = self.repository.get_latest_price(stock_id=stock.id)
                news_summary_text = self._build_news_summary(stock_id=stock.id)
                sector_summary_text = self._build_sector_summary(stock_id=stock.id)
                risk_factors_text = self._build_risk_factors(stock_id=stock.id)

                if sector_summary_text:
                    sector_summary_parts.append(f"{stock.stock_name}: {sector_summary_text}")

                if risk_factors_text:
                    risk_summary_parts.append(f"{stock.stock_name}: {risk_factors_text}")

                item = StockReportItem(
                    report_id=report.id,
                    stock_id=stock.id,
                    current_price=(
                        latest_price.close_price
                        if latest_price
                        else Decimal("0")
                    ),
                    change_rate=(
                        latest_price.change_rate
                        if latest_price
                        else Decimal("0")
                    ),
                    news_summary=news_summary_text,
                    sector_summary=sector_summary_text,
                    risk_factors=risk_factors_text,
                )

                self.repository.create_report_item(item)

                created_items.append(
                    {
                        "item": item,
                        "stock": stock,
                    }
                )

            report.sector_summary = (
                " ".join(sector_summary_parts)
                if sector_summary_parts
                else "연결된 섹터 인사이트가 아직 없습니다."
            )

            report.risk_summary = (
                " ".join(risk_summary_parts)
                if risk_summary_parts
                else "현재 리포트 기준으로 뚜렷한 위험 요인은 확인되지 않았습니다."
            )

            self.db.commit()
            self.db.refresh(report)

            return StockReportResponse(
                report_id=report.id,
                user_id=report.user_id,
                report_date=report.report_date,
                report_title=report.report_title,
                market_summary=report.market_summary,
                sector_summary=report.sector_summary,
                watchlist_summary=report.watchlist_summary,
                risk_summary=report.risk_summary,
                disclaimer=report.disclaimer or get_investment_disclaimer(),
                created_at=report.created_at,
                items=[
                    self._to_item_response(
                        item=data["item"],
                        stock=data["stock"],
                    )
                    for data in created_items
                ],
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"관심종목 리포트 생성 중 오류가 발생했습니다: {str(e)}",
            )

    def get_stock_report(self, report_id: int) -> StockReportResponse:
        """
        저장된 리포트 상세를 조회합니다.
        """
        report = self.repository.get_report_by_id(report_id=report_id)

        if not report:
            raise HTTPException(
                status_code=404,
                detail="해당 리포트를 찾을 수 없습니다.",
            )

        item_rows = self.repository.list_report_items(report_id=report_id)

        return StockReportResponse(
            report_id=report.id,
            user_id=report.user_id,
            report_date=report.report_date,
            report_title=report.report_title,
            market_summary=report.market_summary,
            sector_summary=report.sector_summary,
            watchlist_summary=report.watchlist_summary,
            risk_summary=report.risk_summary,
            disclaimer=report.disclaimer or get_investment_disclaimer(),
            created_at=report.created_at,
            items=[
                self._to_item_response(
                    item=item,
                    stock=stock,
                )
                for item, stock in item_rows
            ],
        )

    def list_stock_reports(
        self,
        user_id: int,
        limit: int = 20,
    ) -> StockReportListResponse:
        """
        사용자의 리포트 목록을 조회합니다.
        """
        reports = self.repository.list_reports_by_user(
            user_id=user_id,
            limit=limit,
        )

        return StockReportListResponse(
            user_id=user_id,
            total_count=len(reports),
            items=[
                StockReportListItemResponse(
                    report_id=report.id,
                    user_id=report.user_id,
                    report_date=report.report_date,
                    report_title=report.report_title,
                    created_at=report.created_at,
                )
                for report in reports
            ],
        )

    # ------------------------------------------------------------
    # 내부 조합 함수
    # ------------------------------------------------------------
    def _build_news_summary(self, stock_id: int) -> str:
        """
        종목별 최근 뉴스 요약을 구성합니다.
        """
        rows = self.repository.list_recent_news_summaries_by_stock(
            stock_id=stock_id,
            limit=3,
        )

        if not rows:
            return "최근 연결된 뉴스 요약이 없습니다."

        summaries = []

        for article, summary in rows:
            if summary and summary.one_line_summary:
                summaries.append(summary.one_line_summary)
            elif summary and summary.summary_text:
                summaries.append(summary.summary_text[:150])
            else:
                summaries.append(article.title)

        return " / ".join(summaries)

    def _build_sector_summary(self, stock_id: int) -> str:
        """
        종목과 연결된 섹터 인사이트 요약을 구성합니다.
        """
        rows = self.repository.list_sector_insights_by_stock(
            stock_id=stock_id,
            limit=2,
        )

        if not rows:
            return "연결된 섹터 인사이트가 없습니다."

        parts = []

        seen_sector_ids = set()

        for sector, insight in rows:
            if sector.id in seen_sector_ids:
                continue

            seen_sector_ids.add(sector.id)

            if insight.insight_summary:
                parts.append(insight.insight_summary)
            else:
                parts.append(
                    f"{sector.sector_name} 섹터의 이슈점수는 "
                    f"{insight.issue_score}점입니다."
                )

        return " ".join(parts)

    def _build_risk_factors(self, stock_id: int) -> str:
        """
        종목 관련 뉴스 요약의 위험 요인을 구성합니다.
        """
        rows = self.repository.list_recent_news_summaries_by_stock(
            stock_id=stock_id,
            limit=3,
        )

        risk_factors = []

        for _, summary in rows:
            if not summary:
                continue

            if summary.sentiment == "NEGATIVE":
                risk_factors.append("부정 감성 뉴스가 확인되었습니다.")

            if summary.risk_factors:
                if isinstance(summary.risk_factors, list):
                    risk_factors.extend([str(item) for item in summary.risk_factors])
                else:
                    risk_factors.append(str(summary.risk_factors))

        unique_risks = list(dict.fromkeys(risk_factors))

        if not unique_risks:
            return "최근 뉴스 요약 기준 뚜렷한 위험 요인은 확인되지 않았습니다."

        return " / ".join(unique_risks[:5])

    def _to_item_response(
        self,
        item: Any,
        stock: Any,
    ) -> StockReportItemResponse:
        """
        StockReportItem + Stock을 응답 schema로 변환합니다.
        """
        return StockReportItemResponse(
            item_id=item.id,
            stock_id=stock.id,
            stock_code=stock.stock_code,
            stock_name=stock.stock_name,
            current_price=(
                str(item.current_price)
                if item.current_price is not None
                else None
            ),
            change_rate=(
                str(item.change_rate)
                if item.change_rate is not None
                else None
            ),
            news_summary=item.news_summary,
            sector_summary=item.sector_summary,
            risk_factors=item.risk_factors,
            created_at=item.created_at,
        )