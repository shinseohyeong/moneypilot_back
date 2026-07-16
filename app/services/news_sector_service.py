# ============================================================
# 파일 위치: app/services/news_sector_service.py
# 역할:
#   - 뉴스 산업/테마 분류 비즈니스 로직을 담당합니다.
#   - 뉴스 제목/설명/요약 내용을 기준으로 sector_keywords를 매칭합니다.
#   - 매칭 결과를 news_sector_mappings에 저장합니다.
# ============================================================

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.news_model import NewsSectorMapping
from app.repositories.news_sector_repository import NewsSectorRepository
from app.schemas.news_sector_schema import (
    NewsSectorClassifyResponse,
    NewsSectorItemResponse,
    NewsSectorListResponse,
)


class NewsSectorService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NewsSectorRepository(db)

    def classify_news_sectors(self, news_id: int) -> NewsSectorClassifyResponse:
        """
        뉴스 1건의 산업/테마를 분류합니다.

        흐름:
        1. 뉴스 조회
        2. 뉴스 요약 조회
        3. 제목/설명/본문/요약 텍스트 결합
        4. sector_keywords 기준 키워드 매칭
        5. news_sector_mappings 저장
        6. 응답 반환
        """
        article = self.repository.get_article_by_id(news_id)

        if not article:
            raise HTTPException(
                status_code=404,
                detail="해당 뉴스를 찾을 수 없습니다.",
            )

        try:
            summary = self.repository.get_latest_summary_by_news_id(news_id)
            source_text = self._build_source_text(article, summary)

            if not source_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="섹터 분류에 사용할 뉴스 텍스트가 없습니다.",
                )

            sector_keyword_rows = self.repository.list_active_sector_keywords()

            if not sector_keyword_rows:
                raise HTTPException(
                    status_code=400,
                    detail="등록된 섹터 키워드가 없습니다. sector_keywords 데이터를 먼저 확인해주세요.",
                )

            matched_result = self._match_sectors(
                source_text=source_text,
                sector_keyword_rows=sector_keyword_rows,
            )

            saved_items = []

            for sector_id, data in matched_result.items():
                matched_keywords = data["matched_keywords"]
                relevance_score = data["relevance_score"]

                mapping = self.repository.upsert_mapping(
                    news_id=news_id,
                    sector_id=sector_id,
                    matched_keywords=matched_keywords,
                    relevance_score=relevance_score,
                )

                saved_items.append(
                    {
                        "mapping": mapping,
                        "sector": data["sector"],
                    }
                )

            self.db.commit()

            return NewsSectorClassifyResponse(
                news_id=news_id,
                matched_count=len(saved_items),
                items=[
                    self._to_item_response(
                        mapping=item["mapping"],
                        sector=item["sector"],
                    )
                    for item in saved_items
                ],
            )

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"뉴스 섹터 분류 중 오류가 발생했습니다: {str(e)}",
            )

    def get_news_sectors(self, news_id: int) -> NewsSectorListResponse:
        """
        뉴스 1건의 섹터 분류 결과를 조회합니다.
        """
        article = self.repository.get_article_by_id(news_id)

        if not article:
            raise HTTPException(
                status_code=404,
                detail="해당 뉴스를 찾을 수 없습니다.",
            )

        rows = self.repository.list_news_sector_mappings(news_id=news_id)

        return NewsSectorListResponse(
            news_id=news_id,
            total_count=len(rows),
            items=[
                self._to_item_response(
                    mapping=mapping,
                    sector=sector,
                )
                for mapping, sector in rows
            ],
        )

    # ------------------------------------------------------------
    # 내부 함수
    # ------------------------------------------------------------
    def _build_source_text(self, article: Any, summary: Any) -> str:
        """
        섹터 분류에 사용할 텍스트를 하나로 합칩니다.

        뉴스 원문 전체가 없을 수 있으므로:
        - title
        - description
        - content
        - one_line_summary
        - summary_text
        - positive_factors
        - risk_factors

        를 함께 사용합니다.
        """
        parts = [
            article.title or "",
            article.description or "",
            article.content or "",
        ]

        if summary:
            parts.append(summary.one_line_summary or "")
            parts.append(summary.summary_text or "")

            if summary.positive_factors:
                parts.append(str(summary.positive_factors))

            if summary.risk_factors:
                parts.append(str(summary.risk_factors))

        return " ".join(parts)

    def _match_sectors(
        self,
        source_text: str,
        sector_keyword_rows: List,
    ) -> Dict[int, Dict]:
        """
        sector_keywords 기반으로 섹터를 매칭합니다.
        """
        lowered_text = source_text.lower()

        sector_matches = defaultdict(
            lambda: {
                "sector": None,
                "matched_keywords": [],
                "weight_sum": Decimal("0.00"),
            }
        )

        for sector, sector_keyword in sector_keyword_rows:
            keyword = sector_keyword.keyword

            if not keyword:
                continue

            if keyword.lower() in lowered_text:
                data = sector_matches[sector.id]
                data["sector"] = sector
                data["matched_keywords"].append(keyword)

                weight = sector_keyword.weight or Decimal("1.00")
                data["weight_sum"] += Decimal(str(weight))

        result = {}

        for sector_id, data in sector_matches.items():
            matched_keywords = list(dict.fromkeys(data["matched_keywords"]))
            relevance_score = self._calculate_relevance_score(
                matched_count=len(matched_keywords),
                weight_sum=data["weight_sum"],
            )

            result[sector_id] = {
                "sector": data["sector"],
                "matched_keywords": matched_keywords,
                "relevance_score": relevance_score,
            }

        return result

    def _calculate_relevance_score(
        self,
        matched_count: int,
        weight_sum: Decimal,
    ) -> Decimal:
        """
        1차 MVP용 관련도 점수 계산

        - 키워드 1개: 최소 60점
        - 키워드 2개: 약 80점
        - 키워드 3개 이상: 최대 100점에 가깝게
        - weight가 높으면 조금 더 높게 반영
        """
        if matched_count <= 0:
            return Decimal("0.00")

        base_score = Decimal("50.00")
        keyword_score = Decimal(matched_count) * Decimal("15.00")
        weight_bonus = weight_sum * Decimal("5.00")

        score = base_score + keyword_score + weight_bonus

        if score > Decimal("100.00"):
            score = Decimal("100.00")

        return score.quantize(Decimal("0.01"))

    def _to_item_response(
        self,
        mapping: NewsSectorMapping,
        sector: Any,
    ) -> NewsSectorItemResponse:
        """
        NewsSectorMapping + StockSector를 응답 schema로 변환합니다.
        """
        matched_keywords = mapping.matched_keywords or []

        return NewsSectorItemResponse(
            sector_id=sector.id,
            sector_name=sector.sector_name,
            risk_level=sector.risk_level,
            matched_keywords=matched_keywords,
            relevance_score=(
                str(mapping.relevance_score)
                if mapping.relevance_score is not None
                else None
            ),
            created_at=mapping.created_at,
        )