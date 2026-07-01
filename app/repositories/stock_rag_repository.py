# ============================================================
# 파일 위치: app/repositories/stock_rag_repository.py
# 역할:
#   - RAG 인덱싱에 사용할 뉴스 요약, 섹터 인사이트 데이터를 조회합니다.
#   - repository 단에서는 commit/rollback을 처리하지 않습니다.
# ============================================================

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.news_model import NewsArticle, NewsSummary, SectorInsight


class StockRagRepository:
    """
    주식/경제 RAG용 repository입니다.
    """

    def __init__(self, db: Session):
        self.db = db

    def list_news_summary_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        news_articles + news_summaries 데이터를 RAG 문서 형태로 변환합니다.
        """
        rows = (
            self.db.query(NewsArticle, NewsSummary)
            .join(NewsSummary, NewsArticle.id == NewsSummary.news_id)
            .order_by(NewsSummary.created_at.desc())
            .limit(limit)
            .all()
        )

        documents = []

        for article, summary in rows:
            content = self._build_news_content(article, summary)

            documents.append(
                {
                    "id": f"news_summary_{summary.id}",
                    "content": content,
                    "metadata": {
                        "source_type": "news_summary",
                        "source_id": str(summary.id),
                        "news_id": str(article.id),
                        "title": article.title,
                        "provider": article.provider,
                        "search_keyword": article.search_keyword,
                        "sentiment": summary.sentiment,
                        "published_at": (
                            article.published_at.isoformat()
                            if article.published_at
                            else None
                        ),
                    },
                }
            )

        return documents

    def list_sector_insight_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        sector_insights 데이터를 RAG 문서 형태로 변환합니다.
        """
        rows = (
            self.db.query(SectorInsight)
            .order_by(SectorInsight.created_at.desc())
            .limit(limit)
            .all()
        )

        documents = []

        for insight in rows:
            content = self._build_sector_insight_content(insight)

            documents.append(
                {
                    "id": f"sector_insight_{insight.id}",
                    "content": content,
                    "metadata": {
                        "source_type": "sector_insight",
                        "source_id": str(insight.id),
                        "sector_id": str(insight.sector_id),
                        "period_days": str(insight.period_days),
                        "issue_score": str(insight.issue_score),
                        "insight_date": (
                            insight.insight_date.isoformat()
                            if insight.insight_date
                            else None
                        ),
                    },
                }
            )

        return documents

    def _build_news_content(
        self,
        article: NewsArticle,
        summary: NewsSummary,
    ) -> str:
        """
        뉴스 요약 RAG 문서 본문을 생성합니다.
        """
        return f"""
[뉴스 요약]
제목: {article.title}
검색 키워드: {article.search_keyword}
제공자: {article.provider}
감성: {summary.sentiment}

한 줄 요약:
{summary.one_line_summary or ""}

상세 요약:
{summary.summary_text or ""}

긍정 요인:
{summary.positive_factors or []}

위험 요인:
{summary.risk_factors or []}

투자 참고 메모:
{summary.investment_note or ""}
""".strip()

    def _build_sector_insight_content(
        self,
        insight: SectorInsight,
    ) -> str:
        """
        섹터 인사이트 RAG 문서 본문을 생성합니다.
        """
        return f"""
[섹터 인사이트]
섹터 ID: {insight.sector_id}
기준일: {insight.insight_date}
분석 기간: 최근 {insight.period_days}일
뉴스 수: {insight.news_count}
긍정 뉴스 수: {insight.positive_count}
중립 뉴스 수: {insight.neutral_count}
부정 뉴스 수: {insight.negative_count}
이슈 점수: {insight.issue_score}

주요 키워드:
{insight.main_keywords or []}

인사이트 요약:
{insight.insight_summary or ""}

위험 요약:
{insight.risk_summary or ""}
""".strip()