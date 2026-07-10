# ============================================================
# 파일 위치: app/services/stock_chatbot_service.py
# 역할:
#   - 주식 챗봇의 비즈니스 로직을 담당합니다.
#   - 관심종목, 현재가, 뉴스 요약, 섹터 인사이트, 투자성향을 조합해 답변합니다.
# ============================================================

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.disclaimer import get_investment_disclaimer
from app.repositories.stock_chatbot_repository import StockChatbotRepository
from app.schemas.stock_chatbot_schema import (
    StockChatbotRequest,
    StockChatbotResponse,
    StockChatbotStockBrief,
    StockChatHistoryItem,
    StockChatHistoryResponse,
)
from app.services.user_risk_context_service import UserRiskContextService
from app.clients.llm_client import get_llm_client

class StockChatbotService:
    """
    주식 챗봇 service입니다.

    현재 MVP 버전에서는 LLM 호출 없이
    DB에 저장된 데이터를 조합해 기본 답변을 생성합니다.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = StockChatbotRepository(db)
        self.user_risk_context_service = UserRiskContextService(db)

    def ask_stock_chatbot(
        self,
        request: StockChatbotRequest,
    ) -> StockChatbotResponse:
        """
        사용자 질문에 대해 주식 관련 답변을 생성하고
        최종 질문/답변을 chatbot_messages에 저장합니다.
        """
        user_id = request.user_id
        disclaimer = get_investment_disclaimer()

        risk_type = self.user_risk_context_service.get_user_risk_type(
            user_id=user_id,
        )
        risk_label = self.user_risk_context_service.get_risk_label(risk_type)
        risk_guide = self.user_risk_context_service.get_interpretation_guide(
            risk_type,
        )

        watchlist_rows = self.repository.list_user_watchlist_stocks(
            user_id=user_id,
        )

        if not watchlist_rows:
            answer = (
                "아직 등록된 관심종목이 없습니다. "
                "관심종목을 먼저 등록하면 현재가, 뉴스 요약, "
                "섹터 흐름을 바탕으로 답변할 수 있습니다. "
                f"[투자성향: {risk_label}] {risk_guide}"
            )

            self._save_chatbot_message(
                request=request,
                answer=answer,
                items=[],
                disclaimer=disclaimer,
                answer_source="rule_fallback",
                used_tools=[
                    "user_risk_context",
                    "watchlist",
                ],
            )

            return StockChatbotResponse(
                user_id=user_id,
                user_message=request.message,
                answer=answer,
                risk_type=risk_type,
                risk_label=risk_label,
                disclaimer=disclaimer,
                items=[],
            )

        items = []

        for _, stock in watchlist_rows:
            latest_price = self.repository.get_latest_price(stock_id=stock.id)

            news_summary = self._build_news_summary(stock_id=stock.id)
            sector_summary = self._build_sector_summary(stock_id=stock.id)
            risk_factors = self._build_risk_factors(stock_id=stock.id)

            items.append(
                StockChatbotStockBrief(
                    stock_id=stock.id,
                    stock_code=stock.stock_code,
                    stock_name=stock.stock_name,
                    current_price=(
                        str(latest_price.close_price)
                        if latest_price and latest_price.close_price is not None
                        else None
                    ),
                    change_rate=(
                        str(latest_price.change_rate)
                        if latest_price and latest_price.change_rate is not None
                        else None
                    ),
                    news_summary=news_summary,
                    sector_summary=sector_summary,
                    risk_factors=risk_factors,
                )
            )

        fallback_answer = self._build_answer(
            user_message=request.message,
            items=items,
            risk_label=risk_label,
            risk_guide=risk_guide,
        )

        context = self._build_llm_context(
            user_message=request.message,
            items=items,
            risk_type=risk_type,
            risk_label=risk_label,
            risk_guide=risk_guide,
        )

        ai_answer = self._generate_ai_answer_or_none(
            user_message=request.message,
            context=context,
        )

        answer = ai_answer if ai_answer else fallback_answer
        answer_source = "llm" if ai_answer else "rule_fallback"

        self._save_chatbot_message(
            request=request,
            answer=answer,
            items=items,
            disclaimer=disclaimer,
            answer_source=answer_source,
            used_tools=[
                "user_risk_context",
                "watchlist",
                "latest_price",
                "news_summary",
                "sector_insight",
            ],
        )

        return StockChatbotResponse(
            user_id=user_id,
            user_message=request.message,
            answer=answer,
            risk_type=risk_type,
            risk_label=risk_label,
            disclaimer=disclaimer,
            items=items,
        )
    
    def _save_chatbot_message(
        self,
        request: StockChatbotRequest,
        answer: str,
        items: list[StockChatbotStockBrief],
        disclaimer: str,
        answer_source: str,
        used_tools: list[str],
    ) -> None:
        """
        최종 사용자 질문과 챗봇 답변을 저장합니다.

        여러 종목을 참고한 경우:
        - 요청에서 특정 stock_id가 지정된 경우에만
        referenced_stock_id 컬럼에 저장합니다.
        - 전체 참고 종목 목록은 used_tools JSON에 저장합니다.
        """
        requested_stock_id = request.stock_id

        referenced_stock_id = (
            requested_stock_id
            if requested_stock_id is not None and requested_stock_id > 0
            else None
        )


        used_tools_payload = {
            "tools": used_tools,
            "answer_source": answer_source,
            "referenced_stock_ids": [
                item.stock_id
                for item in items
            ],
        }

        try:
            saved_message = self.repository.create_chatbot_message(
                user_id=request.user_id,
                chat_type="stock",
                user_message=request.message,
                agent_response=answer,
                referenced_stock_id=referenced_stock_id,
                used_tools=json.dumps(
                    used_tools_payload,
                    ensure_ascii=False,
                ),
                disclaimer=disclaimer,
            )

            self.db.commit()
            self.db.refresh(saved_message)

        except Exception as error:
            self.db.rollback()

            raise HTTPException(
                status_code=500,
                detail=(
                    "주식 챗봇 대화 저장 중 오류가 발생했습니다: "
                    f"{str(error)}"
                ),
            )
    def get_stock_chat_history(
        self,
        user_id: int,
        limit: int = 30,
    ) -> StockChatHistoryResponse:
        """
        사용자의 저장된 주식 챗봇 대화기록을 조회합니다.
        """
        rows = self.repository.list_stock_chat_history(
            user_id=user_id,
            limit=limit,
        )

        total_count = self.repository.count_stock_chat_history(
            user_id=user_id,
        )

        items = [
            StockChatHistoryItem(
                message_id=row.id,
                user_message=row.user_message,
                agent_response=row.agent_response,
                referenced_stock_id=row.referenced_stock_id,
                used_tools=row.used_tools,
                disclaimer=row.disclaimer,
                created_at=row.created_at,
            )
            for row in rows
        ]

        return StockChatHistoryResponse(
            user_id=user_id,
            total_count=total_count,
            items=items,
        )

    # ------------------------------------------------------------
    # 내부 조합 함수
    # ------------------------------------------------------------
    def _build_news_summary(self, stock_id: int) -> str:
        """
        종목별 최근 뉴스 요약 문장을 구성합니다.
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
        종목과 연결된 섹터 인사이트 요약 문장을 구성합니다.
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
        종목 관련 위험 요인 문장을 구성합니다.
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

    def _build_answer(
        self,
        user_message: str,
        items: list[StockChatbotStockBrief],
        risk_label: str,
        risk_guide: str,
    ) -> str:
        """
        최종 챗봇 답변 문장을 생성합니다.
        """
        lines = []

        lines.append("관심종목 기준으로 현재가, 뉴스 요약, 섹터 흐름을 정리해드릴게요.")
        lines.append(f"현재 투자성향은 {risk_label} 기준으로 반영했습니다.")
        lines.append("")

        for item in items:
            lines.append(f"[{item.stock_name}({item.stock_code})]")

            if item.current_price is not None:
                lines.append(f"- 최신 종가: {item.current_price}원")
            else:
                lines.append("- 최신 시세 데이터가 없습니다.")

            if item.change_rate is not None:
                lines.append(f"- 변동률: {item.change_rate}%")

            lines.append(f"- 최근 뉴스 요약: {item.news_summary}")
            lines.append(f"- 섹터 흐름: {item.sector_summary}")
            lines.append(f"- 위험 요인: {item.risk_factors}")
            lines.append("")

        lines.append(f"[투자성향 해석: {risk_label}] {risk_guide}")

        return "\n".join(lines)
    
    def _build_llm_context(
        self,
        user_message: str,
        items: list[StockChatbotStockBrief],
        risk_type: str,
        risk_label: str,
        risk_guide: str,
    ) -> str:
        """
        LLM에 전달할 DB 기반 context를 생성합니다.
        """
        lines = []

        lines.append(f"사용자 질문: {user_message}")
        lines.append(f"투자성향 코드: {risk_type}")
        lines.append(f"투자성향 라벨: {risk_label}")
        lines.append(f"투자성향 해석 기준: {risk_guide}")
        lines.append("")

        for item in items:
            lines.append(f"종목명: {item.stock_name}")
            lines.append(f"종목코드: {item.stock_code}")
            lines.append(f"최신 종가: {item.current_price}")
            lines.append(f"변동률: {item.change_rate}")
            lines.append(f"최근 뉴스 요약: {item.news_summary}")
            lines.append(f"섹터 흐름: {item.sector_summary}")
            lines.append(f"위험 요인: {item.risk_factors}")
            lines.append("---")


        return "\n".join(lines)

    def _generate_ai_answer_or_none(
        self,
        user_message: str,
        context: str,
    ) -> str | None:
        """
        LLM으로 자연어 답변을 생성합니다.

        LLM 호출이 실패하면 None을 반환하고,
        호출부에서는 기존 DB 기반 답변으로 fallback합니다.
        """
        system_prompt = (
            "너는 MoneyPilot의 주식 정보 챗봇이다. "
            "사용자에게 투자 권유를 하지 말고, 제공된 DB context 안의 정보만 바탕으로 답변한다. "
            "확정적인 매수/매도 추천, 수익 보장, 목표가 제시는 하지 않는다. "
            "뉴스, 시세, 섹터 흐름, 위험 요인을 균형 있게 설명한다. "
            "투자 유의 문구는 별도 응답 필드로 제공되므로 답변 본문에 반복하지 않는다. "
            "한국어로 답변한다."
        )

        user_prompt = (
            f"[사용자 질문]\n{user_message}\n\n"
            f"[DB context]\n{context}\n\n"
            "위 정보를 바탕으로 사용자가 이해하기 쉽게 답변해줘. "
            "투자 권유나 수익 보장 표현은 사용하지 마."
        )

        try:
            llm_client = get_llm_client()
            return llm_client.generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

        except Exception:
            return None