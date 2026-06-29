# ============================================================
# 파일 위치: app/services/sector_insight_service.py
# 역할:
#   - 섹터 인사이트 생성/조회 비즈니스 로직을 담당합니다.
#   - 뉴스 섹터 분류 결과와 뉴스 요약 감성값을 기반으로
#     섹터별 뉴스 수, 감성 카운트, 주요 키워드, 이슈점수를 계산합니다.
# ============================================================

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.news_model import SectorInsight
from app.repositories.sector_insight_repository import SectorInsightRepository
from app.schemas.sector_insight_schema import (
    SectorInsightGenerateResponse,
    SectorInsightItemResponse,
    SectorInsightListResponse,
)


class SectorInsightService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SectorInsightRepository(db)

    def generate_sector_insights(
        self,
        period_days: int = 7,
    ) -> SectorInsightGenerateResponse:
        """
        섹터 인사이트를 생성합니다.

        흐름:
        1. 최근 N일간 뉴스-섹터 매핑 조회
        2. 섹터별로 뉴스 수 집계
        3. news_summaries.sentiment 기준 감성 카운트 집계
        4. news_sector_mappings.matched_keywords 기준 주요 키워드 집계
        5. issue_score 계산
        6. sector_insights에 저장 또는 갱신
        """
        if period_days <= 0:
            raise HTTPException(
                status_code=400,
                detail="period_days는 1 이상이어야 합니다.",
            )

        insight_date = date.today()
        start_date = insight_date - timedelta(days=period_days - 1)

        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(insight_date, time.max)

        try:
            rows = self.repository.list_sector_news_rows(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )

            grouped = self._group_by_sector(rows)

            saved_items = []

            for sector_id, data in grouped.items():
                sector = data["sector"]
                news_count = data["news_count"]
                positive_count = data["positive_count"]
                neutral_count = data["neutral_count"]
                negative_count = data["negative_count"]

                main_keywords = [
                    keyword
                    for keyword, _ in data["keyword_counter"].most_common(5)
                ]

                issue_score = self._calculate_issue_score(
                    news_count=news_count,
                    positive_count=positive_count,
                    neutral_count=neutral_count,
                    negative_count=negative_count,
                    keyword_count=len(main_keywords),
                )

                insight_summary = self._build_insight_summary(
                    sector_name=sector.sector_name,
                    period_days=period_days,
                    news_count=news_count,
                    positive_count=positive_count,
                    neutral_count=neutral_count,
                    negative_count=negative_count,
                    main_keywords=main_keywords,
                )

                risk_summary = self._build_risk_summary(
                    sector_name=sector.sector_name,
                    risk_level=sector.risk_level,
                    negative_count=negative_count,
                    main_keywords=main_keywords,
                )

                existing_insight = self.repository.get_insight(
                    sector_id=sector_id,
                    insight_date=insight_date,
                    period_days=period_days,
                )

                if existing_insight:
                    insight = existing_insight
                    insight.news_count = news_count
                    insight.positive_count = positive_count
                    insight.neutral_count = neutral_count
                    insight.negative_count = negative_count
                    insight.main_keywords = main_keywords
                    insight.issue_score = issue_score
                    insight.insight_summary = insight_summary
                    insight.risk_summary = risk_summary

                else:
                    insight = SectorInsight(
                        sector_id=sector_id,
                        insight_date=insight_date,
                        period_days=period_days,
                        news_count=news_count,
                        positive_count=positive_count,
                        neutral_count=neutral_count,
                        negative_count=negative_count,
                        main_keywords=main_keywords,
                        issue_score=issue_score,
                        insight_summary=insight_summary,
                        risk_summary=risk_summary,
                    )
                    self.repository.create_insight(insight)

                saved_items.append(
                    {
                        "insight": insight,
                        "sector": sector,
                    }
                )

            self.db.commit()

            return SectorInsightGenerateResponse(
                insight_date=insight_date,
                period_days=period_days,
                generated_count=len(saved_items),
                items=[
                    self._to_item_response(
                        insight=item["insight"],
                        sector=item["sector"],
                    )
                    for item in sorted(
                        saved_items,
                        key=lambda item: item["insight"].issue_score or Decimal("0"),
                        reverse=True,
                    )
                ],
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"섹터 인사이트 생성 중 오류가 발생했습니다: {str(e)}",
            )

    def get_sector_insights(
        self,
        period_days: int = 7,
    ) -> SectorInsightListResponse:
        """
        저장된 섹터 인사이트를 조회합니다.
        """
        if period_days <= 0:
            raise HTTPException(
                status_code=400,
                detail="period_days는 1 이상이어야 합니다.",
            )

        insight_date = date.today()

        rows = self.repository.list_insights(
            insight_date=insight_date,
            period_days=period_days,
        )

        return SectorInsightListResponse(
            insight_date=insight_date,
            period_days=period_days,
            total_count=len(rows),
            items=[
                self._to_item_response(
                    insight=insight,
                    sector=sector,
                )
                for insight, sector in rows
            ],
        )

    # ------------------------------------------------------------
    # 내부 집계 함수
    # ------------------------------------------------------------
    def _group_by_sector(self, rows: List) -> Dict[int, Dict]:
        """
        뉴스-섹터 매핑 rows를 섹터별로 묶습니다.
        """
        grouped = defaultdict(
            lambda: {
                "sector": None,
                "news_ids": set(),
                "news_count": 0,
                "positive_count": 0,
                "neutral_count": 0,
                "negative_count": 0,
                "keyword_counter": Counter(),
            }
        )

        for mapping, sector, article in rows:
            data = grouped[sector.id]
            data["sector"] = sector

            if article.id not in data["news_ids"]:
                data["news_ids"].add(article.id)
                data["news_count"] += 1

                summary = self.repository.get_latest_summary_by_news_id(article.id)
                sentiment = self._normalize_sentiment(
                    summary.sentiment if summary else None
                )

                if sentiment == "POSITIVE":
                    data["positive_count"] += 1
                elif sentiment == "NEGATIVE":
                    data["negative_count"] += 1
                else:
                    data["neutral_count"] += 1

            matched_keywords = self._normalize_keywords(mapping.matched_keywords)

            for keyword in matched_keywords:
                data["keyword_counter"][keyword] += 1

        return grouped

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

    def _normalize_keywords(self, value: Any) -> List[str]:
        """
        matched_keywords JSON 값을 list[str]로 정리합니다.
        """
        if value is None:
            return []

        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]

        return [str(value)]

    def _calculate_issue_score(
        self,
        news_count: int,
        positive_count: int,
        neutral_count: int,
        negative_count: int,
        keyword_count: int,
    ) -> Decimal:
        """
        mp_sector_score_018 섹터 이슈점수 계산

        1차 MVP 공식:
        - 뉴스 수 점수: 최대 50점
        - 감성 신호 점수: 최대 30점
          긍정 뉴스는 관심 증가 신호, 부정 뉴스는 위험 이슈 신호로 반영
        - 키워드 집중도 점수: 최대 20점
        """
        if news_count <= 0:
            return Decimal("0.00")

        news_score = min(Decimal(news_count) * Decimal("12.00"), Decimal("50.00"))

        positive_ratio = Decimal(positive_count) / Decimal(news_count)
        negative_ratio = Decimal(negative_count) / Decimal(news_count)

        sentiment_score = (
            positive_ratio * Decimal("18.00")
            + negative_ratio * Decimal("12.00")
        )

        keyword_score = min(
            Decimal(keyword_count) * Decimal("4.00"),
            Decimal("20.00"),
        )

        total_score = news_score + sentiment_score + keyword_score

        if total_score > Decimal("100.00"):
            total_score = Decimal("100.00")

        return total_score.quantize(Decimal("0.01"))

    def _build_insight_summary(
        self,
        sector_name: str,
        period_days: int,
        news_count: int,
        positive_count: int,
        neutral_count: int,
        negative_count: int,
        main_keywords: List[str],
    ) -> str:
        """
        섹터 인사이트 요약 문구를 생성합니다.
        """
        keyword_text = ", ".join(main_keywords) if main_keywords else "주요 키워드 없음"

        return (
            f"최근 {period_days}일간 {sector_name} 섹터 관련 뉴스는 {news_count}건입니다. "
            f"감성 분포는 긍정 {positive_count}건, 중립 {neutral_count}건, "
            f"부정 {negative_count}건으로 집계되었습니다. "
            f"주요 키워드는 {keyword_text}입니다."
        )

    def _build_risk_summary(
        self,
        sector_name: str,
        risk_level: str | None,
        negative_count: int,
        main_keywords: List[str],
    ) -> str:
        """
        섹터 위험 요약 문구를 생성합니다.
        """
        keyword_text = ", ".join(main_keywords) if main_keywords else "관련 키워드"

        if negative_count > 0:
            return (
                f"{sector_name} 섹터에서 부정 뉴스가 {negative_count}건 확인되었습니다. "
                f"{keyword_text} 관련 이슈는 변동성 요인으로 작용할 수 있으므로 "
                f"뉴스 흐름을 추가로 확인할 필요가 있습니다."
            )

        if risk_level == "HIGH":
            return (
                f"{sector_name} 섹터는 변동성이 큰 고위험 섹터로 분류되어 있습니다. "
                f"부정 뉴스가 많지 않더라도 단기 가격 변동 가능성을 함께 고려해야 합니다."
            )

        return (
            f"{sector_name} 섹터에서 뚜렷한 부정 뉴스 집중은 확인되지 않았습니다. "
            f"다만 본 내용은 뉴스 기반 참고 정보이므로 투자 판단에는 추가 확인이 필요합니다."
        )

    def _to_item_response(
        self,
        insight: SectorInsight,
        sector: Any,
    ) -> SectorInsightItemResponse:
        """
        SectorInsight + StockSector를 응답 schema로 변환합니다.
        """
        return SectorInsightItemResponse(
            insight_id=insight.id,
            sector_id=sector.id,
            sector_name=sector.sector_name,
            risk_level=sector.risk_level,
            insight_date=insight.insight_date,
            period_days=int(insight.period_days),
            news_count=int(insight.news_count or 0),
            positive_count=int(insight.positive_count or 0),
            neutral_count=int(insight.neutral_count or 0),
            negative_count=int(insight.negative_count or 0),
            main_keywords=insight.main_keywords or [],
            issue_score=(
                str(insight.issue_score)
                if insight.issue_score is not None
                else None
            ),
            insight_summary=insight.insight_summary,
            risk_summary=insight.risk_summary,
            created_at=insight.created_at,
            updated_at=insight.updated_at,
        )