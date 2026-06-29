# ============================================================
# 파일 위치: app/services/stock_alert_service.py
# 역할:
#   - 관심종목 뉴스 알림 생성/조회/읽음 처리 비즈니스 로직을 담당합니다.
#   - 관심종목 관련 뉴스의 감정분석, 위험요인, 섹터 인사이트를 기반으로 알림을 생성합니다.
# ============================================================

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.alert_model import StockAlert
from app.repositories.stock_alert_repository import StockAlertRepository
from app.schemas.stock_alert_schema import (
    StockAlertGenerateResponse,
    StockAlertListResponse,
    StockAlertReadResponse,
    StockAlertResponse,
)
from app.core.disclaimer import get_investment_disclaimer


class StockAlertService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = StockAlertRepository(db)

    def generate_stock_alerts(
        self,
        user_id: int,
        days: int = 7,
    ) -> StockAlertGenerateResponse:
        """
        사용자의 관심종목 관련 뉴스 알림을 생성합니다.

        생성 조건:
        - 관심종목에 연결된 최근 뉴스
        - 뉴스 요약 sentiment가 NEGATIVE인 경우 RISK 알림
        - risk_factors가 있는 경우 RISK 알림
        - 고위험 섹터 또는 issue_score가 높은 경우 SECTOR 성격의 RISK 알림
        - 그 외 최근 관심종목 뉴스는 NEWS 알림
        """
        if days <= 0:
            raise HTTPException(
                status_code=400,
                detail="days는 1 이상이어야 합니다.",
            )

        watchlist_rows = self.repository.list_user_watchlist_stocks(user_id=user_id)

        if not watchlist_rows:
            raise HTTPException(
                status_code=404,
                detail="관심종목이 없습니다. 관심종목을 먼저 등록해주세요.",
            )

        stock_ids = list({stock.id for _, stock in watchlist_rows})
        start_datetime = datetime.now() - timedelta(days=days)

        try:
            recent_news_rows = self.repository.list_recent_stock_news(
                stock_ids=stock_ids,
                start_datetime=start_datetime,
                limit=50,
            )

            generated_alerts = []
            duplicated_count = 0

            for stock, article in recent_news_rows:
                summary = self.repository.get_latest_summary_by_news_id(article.id)
                sector_id, sector_name, sector_risk_reason = self._find_sector_risk(
                    news_id=article.id,
                )

                alert_type = self._decide_alert_type(
                    summary=summary,
                    sector_risk_reason=sector_risk_reason,
                )

                title = self._build_title(
                    alert_type=alert_type,
                    stock_name=stock.stock_name,
                )

                message = self._build_message(
                    stock_name=stock.stock_name,
                    article_title=article.title,
                    summary=summary,
                    sector_risk_reason=sector_risk_reason,
                )

                existing_alert = self.repository.get_existing_alert(
                    user_id=user_id,
                    alert_type=alert_type,
                    stock_id=stock.id,
                    news_id=article.id,
                )

                if existing_alert:
                    duplicated_count += 1
                    continue

                alert = StockAlert(
                    user_id=user_id,
                    stock_id=stock.id,
                    news_id=article.id,
                    sector_id=sector_id,
                    alert_type=alert_type,
                    title=title,
                    message=message,
                    is_read=False,
                )

                self.repository.create_alert(alert)

                generated_alerts.append(
                    {
                        "alert": alert,
                        "stock": stock,
                        "sector_name": sector_name,
                    }
                )

            self.db.commit()

            return StockAlertGenerateResponse(
                user_id=user_id,
                checked_news_count=len(recent_news_rows),
                generated_count=len(generated_alerts),
                duplicated_count=duplicated_count,
                items=[
                    self._to_response(
                        alert=data["alert"],
                        stock=data["stock"],
                        sector_name=data["sector_name"],
                    )
                    for data in generated_alerts
                ],
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"관심종목 뉴스 알림 생성 중 오류가 발생했습니다: {str(e)}",
            )

    def list_stock_alerts(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
    ) -> StockAlertListResponse:
        """
        사용자 알림 목록을 조회합니다.
        """
        rows = self.repository.list_alerts(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit,
        )

        unread_count = self.repository.count_unread_alerts(user_id=user_id)

        return StockAlertListResponse(
            user_id=user_id,
            total_count=len(rows),
            unread_count=unread_count,
            items=[
                self._to_response(
                    alert=alert,
                    stock=stock,
                    sector_name=sector.sector_name if sector else None,
                )
                for alert, stock, sector in rows
            ],
        )

    def mark_alert_as_read(self, alert_id: int) -> StockAlertReadResponse:
        """
        알림 1건을 읽음 처리합니다.
        """
        alert = self.repository.get_alert_by_id(alert_id=alert_id)

        if not alert:
            raise HTTPException(
                status_code=404,
                detail="해당 알림을 찾을 수 없습니다.",
            )

        alert.is_read = True
        alert.read_at = datetime.now()

        self.db.commit()
        self.db.refresh(alert)

        return StockAlertReadResponse(
            alert_id=alert.id,
            is_read=alert.is_read,
            read_at=alert.read_at,
        )

    # ------------------------------------------------------------
    # 내부 판단 함수
    # ------------------------------------------------------------
    def _decide_alert_type(
        self,
        summary: Any,
        sector_risk_reason: Optional[str],
    ) -> str:
        """
        알림 유형을 결정합니다.
        """
        sentiment = self._normalize_sentiment(
            getattr(summary, "sentiment", None)
        )

        risk_factors = self._safe_list(
            getattr(summary, "risk_factors", None)
        )

        if sentiment == "NEGATIVE" or risk_factors or sector_risk_reason:
            return "RISK"

        return "NEWS"

    def _find_sector_risk(
        self,
        news_id: int,
    ) -> tuple[Optional[int], Optional[str], Optional[str]]:
        """
        뉴스에 연결된 섹터 위험 요인을 확인합니다.
        """
        sector_rows = self.repository.list_news_sectors(news_id=news_id)

        for _, sector in sector_rows:
            insight = self.repository.get_latest_sector_insight(sector_id=sector.id)

            if sector.risk_level == "HIGH":
                return (
                    sector.id,
                    sector.sector_name,
                    f"{sector.sector_name} 섹터는 고위험 섹터로 분류되어 있습니다.",
                )

            if insight and insight.issue_score is not None:
                issue_score = Decimal(str(insight.issue_score))

                if issue_score >= Decimal("70.00"):
                    return (
                        sector.id,
                        sector.sector_name,
                        f"{sector.sector_name} 섹터의 이슈점수가 {issue_score}점으로 높게 집계되었습니다.",
                    )

        return None, None, None

    def _build_title(
        self,
        alert_type: str,
        stock_name: str,
    ) -> str:
        """
        알림 제목을 생성합니다.
        """
        if alert_type == "RISK":
            return f"{stock_name} 관련 위험 뉴스 알림"

        return f"{stock_name} 관련 새 뉴스 알림"

    def _build_message(
        self,
        stock_name: str,
        article_title: str,
        summary: Any,
        sector_risk_reason: Optional[str],
    ) -> str:
        """
        알림 메시지를 생성합니다.
        """
        sentiment = self._normalize_sentiment(
            getattr(summary, "sentiment", None)
        )

        risk_factors = self._safe_list(
            getattr(summary, "risk_factors", None)
        )

        parts = [
            f"{stock_name} 관련 뉴스가 확인되었습니다.",
            f"뉴스 제목: {article_title}",
        ]

        if summary and getattr(summary, "one_line_summary", None):
            parts.append(f"요약: {summary.one_line_summary}")

        parts.append(f"감정분석: {self._to_korean_label(sentiment)}")

        if risk_factors:
            parts.append(f"위험 요인: {', '.join(risk_factors[:3])}")

        if sector_risk_reason:
            parts.append(f"섹터 참고: {sector_risk_reason}")

        parts.append("본 알림은 투자 권유가 아니며, 뉴스 기반 참고 정보입니다.")

        return " ".join(parts)

    def _normalize_sentiment(self, sentiment: Any) -> str:
        """
        sentiment 값을 POSITIVE / NEUTRAL / NEGATIVE 중 하나로 정리합니다.
        """
        if not sentiment:
            return "NEUTRAL"

        normalized = str(sentiment).upper()

        if normalized not in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
            return "NEUTRAL"

        return normalized

    def _to_korean_label(self, sentiment: str) -> str:
        labels = {
            "POSITIVE": "긍정",
            "NEUTRAL": "중립",
            "NEGATIVE": "부정",
        }
        return labels.get(sentiment, "중립")

    def _safe_list(self, value: Any) -> List[str]:
        """
        JSON/list/string 값을 list[str]로 정리합니다.
        """
        if value is None:
            return []

        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]

        return [str(value)] if str(value).strip() else []

    def _to_response(
        self,
        alert: StockAlert,
        stock: Any = None,
        sector_name: Optional[str] = None,
    ) -> StockAlertResponse:
        """
        StockAlert를 응답 schema로 변환합니다.
        """
        return StockAlertResponse(
            alert_id=alert.id,
            user_id=alert.user_id,
            stock_id=alert.stock_id,
            stock_name=stock.stock_name if stock else None,
            news_id=alert.news_id,
            sector_id=alert.sector_id,
            sector_name=sector_name,
            alert_type=alert.alert_type,
            title=alert.title,
            message=alert.message,
            is_read=alert.is_read,
            created_at=alert.created_at,
            updated_at=alert.updated_at,
            read_at=alert.read_at,
        )