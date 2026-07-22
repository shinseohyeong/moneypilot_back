# app/services/spending_report_service.py

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.spending_analysis_model import AnalysisReport
from app.rag.ingestors.spending_ingestor import (
    ingest_spending_report,
)
from app.repositories.spending_report_repository import (
    AnalysisReportRepository,
)
from app.repositories.spending_repository import (
    SpendingRepository,
)
from app.services.spending_analysis_service import (
    SpendingAnalysisService,
    SpendingService,
)
from app.services.spending_llm_service import SpendingLLMService


logger = logging.getLogger(__name__)


class AnalysisReportService:
    """
    AI 소비 분석 리포트 비즈니스 로직 Service.

    역할:
    - 기존 소비 분석 데이터 조회
    - LLM에 전달할 report_context 생성
    - SpendingLLMService를 통한 LLM 리포트 생성
    - analysis_reports 테이블에 리포트 저장 또는 수정
    - 최종 소비 분석 데이터를 RAG에 저장 또는 갱신
    - 저장된 AI 리포트 조회
    """

    def __init__(
        self,
        db: Session,
    ):
        """
        AnalysisReportService 초기화
        """

        self.db = db

        # AI 리포트 저장 및 조회 Repository
        self.report_repository = (
            AnalysisReportRepository(db)
        )

        # 소비 요약, 카테고리, 카드 Repository
        self.spending_repository = (
            SpendingRepository(db)
        )

        # Ollama LLM 호출 Service
        self.llm_service = SpendingLLMService(db)

        # 기존 소비 분석 서비스 재사용
        self.spending_service = SpendingService(db)

        self.spending_analysis_service = (
            SpendingAnalysisService(db)
        )

    def generate_monthly_report(
        self,
        user_id: int,
        month: str,
    ) -> AnalysisReport:
        """
        특정 월의 AI 소비 분석 리포트를 생성하고 저장한다.

        처리 흐름:
        1. month 형식 검증
        2. 기존 월별 요약 데이터 조회
        3. 과소비 카테고리 데이터 조회
        4. 카드별 사용금액 데이터 조회
        5. LLM 전달용 report_context 생성
        6. Ollama를 통해 소비 코칭 리포트 생성
        7. analysis_reports 테이블에 저장 또는 수정
        8. 월별 요약, 카테고리, AI 리포트를 RAG에 저장
        9. 저장된 리포트 반환
        """

        self.spending_analysis_service.validate_month_format(
            month
        )

        # 1. 월별 소비 요약 조회
        summary = (
            self.spending_analysis_service
            .get_monthly_summary_by_month(
                user_id=user_id,
                month=month,
            )
        )

        # 2. 과소비 카테고리 조회
        overspending_data = (
            self.spending_service
            .get_monthly_overspending_categories(
                user_id=user_id,
                month=month,
            )
        )

        # 3. 카드별 사용금액 조회
        card_data = (
            self.spending_service
            .get_monthly_card_spendings(
                user_id=user_id,
                month=month,
            )
        )

        # 4. LLM 전달용 context 생성
        report_context = self.build_report_context(
            summary=summary,
            overspending_data=overspending_data,
            card_data=card_data,
        )

        # 5. Ollama LLM 호출
        llm_result = (
            self.llm_service.generate_spending_report(
                report_context=report_context,
                user_id=user_id,
            )
        )

        if not isinstance(llm_result, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "AI 소비 분석 결과 형식이 올바르지 "
                    "않습니다."
                ),
            )

        # 6. 리포트 저장 또는 기존 리포트 수정
        report = (
            self.report_repository.save_or_update_report(
                summary_id=summary.id,
                user_id=user_id,
                month=month,
                report_title=llm_result.get(
                    "report_title",
                    f"{month} AI 소비 코칭 리포트",
                ),
                summary_text=llm_result.get(
                    "summary_text",
                    "",
                ),
                category_text=llm_result.get(
                    "category_text",
                ),
                overspending_text=llm_result.get(
                    "overspending_text",
                ),
                card_text=llm_result.get(
                    "card_text",
                ),
                compare_text=llm_result.get(
                    "compare_text",
                ),
                recommendation_text=llm_result.get(
                    "recommendation_text",
                ),
                agent_response=llm_result.get(
                    "agent_response",
                ),
            )
        )

        # 7. 저장된 카테고리 데이터 조회
        categories = (
            self.spending_repository
            .get_category_spendings_by_user_and_month(
                user_id=user_id,
                month=month,
            )
        )

        # 8. 최종 소비 분석 데이터를 RAG에 저장
        #
        # RAG 저장이 실패해도 이미 생성된 소비 리포트와
        # DB 저장 결과는 정상 반환되도록 예외를 분리한다.
        try:
            rag_result = ingest_spending_report(
                user_id=user_id,
                summary=summary,
                categories=categories,
                report=report,
            )

            logger.info(
                (
                    "[SPENDING REPORT RAG SAVED] "
                    "user_id=%s, month=%s, "
                    "report_id=%s, chunk_count=%s"
                ),
                user_id,
                month,
                report.id,
                rag_result.get("chunk_count", 0),
            )

        except Exception:
            logger.exception(
                (
                    "[SPENDING REPORT RAG FAILED] "
                    "user_id=%s, month=%s, "
                    "report_id=%s"
                ),
                user_id,
                month,
                getattr(report, "id", None),
            )

        return report

    def get_monthly_report(
        self,
        user_id: int,
        month: str,
    ) -> AnalysisReport:
        """
        특정 월의 저장된 AI 소비 분석 리포트를 조회한다.

        GET 요청에서는 LLM을 호출하지 않고
        analysis_reports 테이블에 저장된 리포트만 조회한다.
        """

        self.spending_analysis_service.validate_month_format(
            month
        )

        # 사용자와 월에 해당하는 월별 소비 요약 조회
        summary = (
            self.spending_analysis_service
            .get_monthly_summary_by_month(
                user_id=user_id,
                month=month,
            )
        )

        # 월별 소비 요약에 연결된 AI 리포트 조회
        report = (
            self.report_repository
            .get_report_by_summary_id(
                summary_id=summary.id,
            )
        )

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "생성된 AI 소비 분석 리포트가 없습니다. "
                    "먼저 AI 소비 분석 리포트를 "
                    "생성해주세요."
                ),
            )

        return report

    def build_report_context(
        self,
        summary,
        overspending_data: dict,
        card_data: dict,
    ) -> dict:
        """
        LLM에 전달할 소비 분석 context를 생성한다.

        포함 데이터:
        - 월별 소비 요약
        - 이번 달 지출 금액이 큰 카테고리 TOP 3
        - 전월 대비 증가 카테고리 TOP 3
        - 가장 많이 사용한 카드
        """

        top_card = self.extract_top_card(
            card_data
        )

        return {
            "month": summary.month,
            "monthly_summary": {
                "monthly_salary": self.decimal_to_int(
                    summary.monthly_salary
                ),
                "total_income": self.decimal_to_int(
                    summary.total_income
                ),
                "total_spending": self.decimal_to_int(
                    summary.total_spending
                ),
                "fixed_expense": self.decimal_to_int(
                    summary.fixed_expense
                ),
                "variable_expense": self.decimal_to_int(
                    summary.variable_expense
                ),
                "remaining_money": self.decimal_to_int(
                    summary.remaining_money
                ),
                "spending_diff": self.decimal_to_int(
                    summary.spending_diff
                ),
                "spending_change_rate": (
                    self.decimal_to_float(
                        summary.spending_change_rate
                    )
                ),
            },
            "top_spending_categories": (
                overspending_data.get(
                    "top_spending_categories",
                    [],
                )
            ),
            "top_increased_categories": (
                overspending_data.get(
                    "top_increased_categories",
                    [],
                )
            ),
            "top_card": top_card,
        }

    def extract_top_card(
        self,
        card_data: dict,
    ) -> dict | None:
        """
        카드별 사용금액 데이터에서
        가장 많이 사용한 카드 한 개를 추출한다.
        """

        cards = card_data.get("cards", [])

        if not cards:
            return None

        return max(
            cards,
            key=lambda item: self.decimal_to_decimal(
                item.get("card_amount", 0)
            ),
        )

    def decimal_to_decimal(
        self,
        value: Any,
    ) -> Decimal:
        """
        값을 안전하게 Decimal로 변환한다.
        """

        if value is None:
            return Decimal("0")

        try:
            return Decimal(str(value))
        except (
            TypeError,
            ValueError,
            InvalidOperation,
        ):
            return Decimal("0")

    def decimal_to_int(
        self,
        value: Any,
    ) -> int:
        """
        Decimal 또는 None 값을 안전하게 int로 변환한다.
        """

        return int(
            self.decimal_to_decimal(value)
        )

    def decimal_to_float(
        self,
        value: Any,
    ) -> float:
        """
        Decimal 또는 None 값을 안전하게 float로 변환한다.
        """

        return float(
            self.decimal_to_decimal(value)
        )