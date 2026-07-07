# ==========================================
# 파일 위치: app/services/finance_chatbot_service.py
# 역할:
# - 소비 데이터 기반 투자 참고 챗봇 비즈니스 로직
# - 직접 투자 권유 금지
# - LLM 실패 시 DB 기반 fallback 답변 반환
# ==========================================

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.clients.llm_client import generate_text
from app.repositories.finance_chatbot_repository import FinanceChatbotRepository
from app.schemas.finance_chatbot_schema import (
    FinanceChatbotRequest,
    FinanceChatbotResponse,
    FinanceSpendingContextItem,
)
from app.services.user_risk_context_service import UserRiskContextService


ZERO = Decimal("0")
MONEY_QUANTIZE = Decimal("0.01")


class FinanceChatbotService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = FinanceChatbotRepository(db)
        self.user_risk_context_service = UserRiskContextService(db)

    def create_finance_answer(
        self,
        request: FinanceChatbotRequest,
    ) -> FinanceChatbotResponse:
        """
        소비 데이터 기반 투자 여력 참고 답변 생성
        """
        finance_profile = self.repository.get_finance_profile_by_user_id(
            user_id=request.user_id,
        )

        monthly_summary = self.repository.get_latest_monthly_spending_summary(
            user_id=request.user_id,
        )

        risk_context = self._get_risk_context(
            user_id=request.user_id,
            finance_profile=finance_profile,
        )

        disclaimer = self._get_investment_disclaimer()

        # 금융 프로필 또는 소비 요약이 부족한 경우
        if finance_profile is None or monthly_summary is None:
            answer = self._build_not_enough_data_answer(
                has_finance_profile=finance_profile is not None,
                has_monthly_summary=monthly_summary is not None,
                risk_context=risk_context,
                disclaimer=disclaimer,
            )

            return FinanceChatbotResponse(
                user_id=request.user_id,
                chat_type="finance",
                user_message=request.message,
                answer=answer,
                risk_type=risk_context["risk_type"],
                risk_label=risk_context["risk_label"],
                month=None,
                monthly_salary=self._decimal_to_money_string(
                    getattr(finance_profile, "monthly_salary", None)
                    if finance_profile
                    else None
                ),
                fixed_expense=self._decimal_to_money_string(
                    getattr(finance_profile, "fixed_expense", None)
                    if finance_profile
                    else None
                ),
                total_spending=None,
                estimated_available_amount=None,
                categories=[],
                disclaimer=disclaimer,
            )

        category_spendings = self.repository.get_category_spendings_by_summary_id(
            summary_id=monthly_summary.id,
        )

        analysis_report = self.repository.get_latest_analysis_report_by_summary_id(
            summary_id=monthly_summary.id,
        )

        spending_context = self._build_spending_context(
            finance_profile=finance_profile,
            monthly_summary=monthly_summary,
        )

        category_items = self._build_category_items(category_spendings)

        fallback_answer = self._build_fallback_answer(
            message=request.message,
            risk_context=risk_context,
            spending_context=spending_context,
            category_items=category_items,
            analysis_report=analysis_report,
            disclaimer=disclaimer,
        )

        answer = self._generate_llm_answer_or_fallback(
            user_message=request.message,
            risk_context=risk_context,
            spending_context=spending_context,
            category_items=category_items,
            analysis_report=analysis_report,
            fallback_answer=fallback_answer,
            disclaimer=disclaimer,
        )

        return FinanceChatbotResponse(
            user_id=request.user_id,
            chat_type="finance",
            user_message=request.message,
            answer=answer,
            risk_type=risk_context["risk_type"],
            risk_label=risk_context["risk_label"],
            month=spending_context["month"],
            monthly_salary=self._decimal_to_money_string(
                spending_context["monthly_salary"]
            ),
            fixed_expense=self._decimal_to_money_string(
                spending_context["fixed_expense"]
            ),
            total_spending=self._decimal_to_money_string(
                spending_context["total_spending"]
            ),
            estimated_available_amount=self._decimal_to_money_string(
                spending_context["estimated_available_amount"]
            ),
            categories=category_items,
            disclaimer=disclaimer,
        )

    def _build_spending_context(
        self,
        finance_profile,
        monthly_summary,
    ) -> Dict[str, Any]:
        """
        소비/소득 계산에 필요한 값을 하나의 dict로 정리

        계산 우선순위:
        1. monthly_spending_summaries.remaining_money 사용
        2. remaining_money가 없으면 monthly_salary - total_spending
        3. 음수면 0 처리
        """
        profile_monthly_salary = self._to_decimal(
            getattr(finance_profile, "monthly_salary", None)
        )
        profile_fixed_expense = self._to_decimal(
            getattr(finance_profile, "fixed_expense", None)
        )

        summary_monthly_salary = self._to_decimal(
            getattr(monthly_summary, "monthly_salary", None)
        )
        summary_fixed_expense = self._to_decimal(
            getattr(monthly_summary, "fixed_expense", None)
        )
        total_spending = self._to_decimal(
            getattr(monthly_summary, "total_spending", None)
        )
        remaining_money = self._to_decimal(
            getattr(monthly_summary, "remaining_money", None)
        )

        monthly_salary = (
            summary_monthly_salary
            if summary_monthly_salary > ZERO
            else profile_monthly_salary
        )

        fixed_expense = (
            summary_fixed_expense
            if summary_fixed_expense > ZERO
            else profile_fixed_expense
        )

        # summary에 remaining_money가 있으면 그 값을 우선 사용
        if remaining_money > ZERO:
            estimated_available_amount = remaining_money
        else:
            estimated_available_amount = monthly_salary - total_spending

        if estimated_available_amount < ZERO:
            estimated_available_amount = ZERO

        return {
            "month": monthly_summary.month,
            "monthly_salary": monthly_salary,
            "fixed_expense": fixed_expense,
            "total_spending": total_spending,
            "estimated_available_amount": estimated_available_amount,
        }

    def _build_category_items(
        self,
        category_spendings,
    ) -> List[FinanceSpendingContextItem]:
        """
        카테고리별 소비 정보를 응답 Schema에 맞게 변환
        """
        items: List[FinanceSpendingContextItem] = []

        for item in category_spendings:
            items.append(
                FinanceSpendingContextItem(
                    category=item.category,
                    category_amount=self._decimal_to_money_string(
                        item.category_amount
                    ),
                    category_ratio=self._decimal_to_ratio_string(
                        item.category_ratio
                    ),
                    transaction_count=item.transaction_count,
                )
            )

        return items

    def _build_fallback_answer(
        self,
        message: str,
        risk_context: Dict[str, str],
        spending_context: Dict[str, Any],
        category_items: List[FinanceSpendingContextItem],
        analysis_report,
        disclaimer: str,
    ) -> str:
        """
        LLM 호출 실패 시 사용할 DB 기반 규칙형 답변
        """
        monthly_salary = self._decimal_to_korean_money(
            spending_context["monthly_salary"]
        )
        fixed_expense = self._decimal_to_korean_money(
            spending_context["fixed_expense"]
        )
        total_spending = self._decimal_to_korean_money(
            spending_context["total_spending"]
        )
        available_amount = self._decimal_to_korean_money(
            spending_context["estimated_available_amount"]
        )

        risk_type = risk_context["risk_type"]
        risk_label = risk_context["risk_label"]

        risk_message = self._get_risk_based_message(
            risk_type=risk_type,
            available_amount=spending_context["estimated_available_amount"],
        )

        top_category_text = self._build_top_category_text(category_items)

        if spending_context["estimated_available_amount"] <= ZERO:
            main_message = (
                "현재 소비 흐름 기준으로는 투자 여력을 따로 보기보다 "
                "지출 관리, 고정비 점검, 비상금 확보를 먼저 고려하는 것이 좋아 보입니다."
            )
        else:
            main_message = (
                f"월 소득과 지출 흐름을 기준으로 보면, 무리하지 않는 범위에서 "
                f"참고 가능한 여유자금은 대략 {available_amount} 수준으로 볼 수 있습니다. "
                "다만 이 금액 전체를 투자하라는 의미는 아니며, 생활비·비상금·부채상환·고정비를 "
                "먼저 고려한 뒤 남는 범위에서 판단해야 합니다."
            )

        report_text = ""
        if analysis_report is not None and analysis_report.summary_text:
            report_text = f"\n\n최근 소비 분석 요약으로는 {analysis_report.summary_text}"

        return (
            f"{spending_context['month']} 기준으로 확인해봤습니다.\n\n"
            f"- 투자성향: {risk_label}({risk_type})\n"
            f"- 월급: {monthly_salary}\n"
            f"- 고정비: {fixed_expense}\n"
            f"- 총소비: {total_spending}\n"
            f"- 참고 가능한 여유자금: {available_amount}\n\n"
            f"{main_message}\n\n"
            f"{risk_message}"
            f"{top_category_text}"
            f"{report_text}\n\n"
            f"{disclaimer}"
        )

    def _generate_llm_answer_or_fallback(
        self,
        user_message: str,
        risk_context: Dict[str, str],
        spending_context: Dict[str, Any],
        category_items: List[FinanceSpendingContextItem],
        analysis_report,
        fallback_answer: str,
        disclaimer: str,
    ) -> str:
        """
        LLM 답변 생성
        - 실패하면 fallback_answer 반환
        - 금융 안전 문구는 system prompt에 강하게 제한
        """
        system_prompt = self._build_system_prompt(disclaimer)

        user_prompt = self._build_user_prompt(
            user_message=user_message,
            risk_context=risk_context,
            spending_context=spending_context,
            category_items=category_items,
            analysis_report=analysis_report,
            disclaimer=disclaimer,
        )

        try:
            llm_answer = generate_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

            if not llm_answer:
                return fallback_answer

            return str(llm_answer).strip()

        except Exception:
            # LLM 장애가 나도 서비스가 죽지 않도록 DB 기반 답변 반환
            return fallback_answer

    def _build_system_prompt(self, disclaimer: str) -> str:
        return f"""
너는 MoneyPilot의 소비 데이터 기반 투자 참고 챗봇이다.

반드시 지켜야 할 규칙:
1. 직접적인 투자 권유를 하지 않는다.
2. 특정 종목, ETF, 코인, 펀드, 금융상품을 사라고 추천하지 않는다.
3. "매수하세요", "투자하세요", "월 얼마를 넣으세요"처럼 단정적으로 말하지 않는다.
4. 수익률 보장, 목표 수익률, 목표가, 확정 수익을 제시하지 않는다.
5. 사용자의 월급, 고정비, 소비 요약, 여유자금, 투자성향을 바탕으로 참고용 설명만 제공한다.
6. 여유자금이 있더라도 생활비, 비상금, 부채상환, 고정비를 먼저 고려하도록 안내한다.
7. 답변에는 반드시 투자 권유가 아니라는 주의 문구를 포함한다.
8. 한국어로 자연스럽게 답변한다.

주의 문구:
{disclaimer}
""".strip()

    def _build_user_prompt(
        self,
        user_message: str,
        risk_context: Dict[str, str],
        spending_context: Dict[str, Any],
        category_items: List[FinanceSpendingContextItem],
        analysis_report,
        disclaimer: str,
    ) -> str:
        category_text = "\n".join(
            [
                f"- {item.category}: {item.category_amount}원, "
                f"{item.category_ratio}%, {item.transaction_count}건"
                for item in category_items[:5]
            ]
        )

        if not category_text:
            category_text = "- 카테고리별 소비 데이터 없음"

        report_text = "분석 리포트 없음"
        if analysis_report is not None:
            report_text = f"""
리포트 제목: {analysis_report.report_title}
요약: {analysis_report.summary_text}
카테고리 분석: {analysis_report.category_text}
과소비 분석: {analysis_report.overspending_text}
추천 문구: {analysis_report.recommendation_text}
""".strip()

        return f"""
사용자 질문:
{user_message}

사용자 투자성향:
- risk_type: {risk_context["risk_type"]}
- risk_label: {risk_context["risk_label"]}

소비/소득 데이터:
- 기준 월: {spending_context["month"]}
- 월급: {self._decimal_to_money_string(spending_context["monthly_salary"])}원
- 고정비: {self._decimal_to_money_string(spending_context["fixed_expense"])}원
- 총소비: {self._decimal_to_money_string(spending_context["total_spending"])}원
- 참고 가능한 여유자금: {self._decimal_to_money_string(spending_context["estimated_available_amount"])}원

상위 카테고리 소비:
{category_text}

소비 분석 리포트:
{report_text}

답변 작성 기준:
- 참고 가능한 여유자금을 설명하되, 이 금액을 투자하라고 말하지 말 것
- 투자성향별로 위험 안내 강도를 조절할 것
- SAFE는 비상금, 손실 가능성, 보수적 접근 강조
- NORMAL은 소비, 저축, 투자 균형 강조
- AGGRESSIVE는 성장 가능성을 언급할 수 있으나 변동성과 손실 가능성도 반드시 강조
- 특정 종목 추천 금지
- 직접 투자 권유 금지
- 마지막에 아래 주의 문구 포함

주의 문구:
{disclaimer}
""".strip()

    def _build_not_enough_data_answer(
        self,
        has_finance_profile: bool,
        has_monthly_summary: bool,
        risk_context: Dict[str, str],
        disclaimer: str,
    ) -> str:
        missing_items = []

        if not has_finance_profile:
            missing_items.append("금융 프로필")
        if not has_monthly_summary:
            missing_items.append("월별 소비 분석 데이터")

        missing_text = ", ".join(missing_items)

        return (
            f"아직 {missing_text}가 부족해서 투자 여력을 정확히 참고하기는 어렵습니다.\n\n"
            "카드 명세서 또는 거래 내역을 등록하고 월별 소비 분석이 생성되면, "
            "월급·고정비·총소비·카테고리별 소비 흐름을 바탕으로 "
            "무리하지 않는 범위의 여유자금을 참고용으로 안내할 수 있습니다.\n\n"
            f"현재 투자성향은 {risk_context['risk_label']}({risk_context['risk_type']}) 기준으로 해석됩니다.\n\n"
            f"{disclaimer}"
        )

    def _get_risk_context(
        self,
        user_id: int,
        finance_profile,
    ) -> Dict[str, str]:
        """
        UserRiskContextService를 우선 사용해서 투자성향 기준을 통일한다.

        만약 기존 service의 메서드명이 다르면,
        이 함수 내부만 네 프로젝트에 맞게 수정하면 된다.
        """
        try:
            if hasattr(self.user_risk_context_service, "get_user_risk_context"):
                context = self.user_risk_context_service.get_user_risk_context(user_id)

                if isinstance(context, dict):
                    return {
                        "risk_type": context.get("risk_type", "NORMAL"),
                        "risk_label": context.get("risk_label", "보통형"),
                    }

                return {
                    "risk_type": getattr(context, "risk_type", "NORMAL"),
                    "risk_label": getattr(context, "risk_label", "보통형"),
                }
        except Exception:
            pass

        raw_risk_type = getattr(finance_profile, "risk_type", None)

        risk_type = self._normalize_risk_type(raw_risk_type)
        risk_label = self._risk_type_to_label(risk_type)

        return {
            "risk_type": risk_type,
            "risk_label": risk_label,
        }

    def _normalize_risk_type(self, raw_risk_type: Optional[str]) -> str:
        if raw_risk_type is None:
            return "NORMAL"

        value = str(raw_risk_type).strip().lower()

        if value in ["conservative", "safe", "안전형"]:
            return "SAFE"

        if value in ["aggressive", "공격형", "위험형"]:
            return "AGGRESSIVE"

        return "NORMAL"

    def _risk_type_to_label(self, risk_type: str) -> str:
        if risk_type == "SAFE":
            return "안전형"

        if risk_type == "AGGRESSIVE":
            return "위험형"

        return "보통형"

    def _get_risk_based_message(
        self,
        risk_type: str,
        available_amount: Decimal,
    ) -> str:
        if available_amount <= ZERO:
            return (
                "현재는 투자 판단보다 소비 흐름을 먼저 안정화하는 것이 중요합니다. "
                "특히 고정비, 반복 지출, 과소비 카테고리를 먼저 점검하는 방향이 적절합니다."
            )

        if risk_type == "SAFE":
            return (
                "안전형 성향에서는 여유자금이 있더라도 손실 가능성을 크게 고려해야 합니다. "
                "비상금과 필수 생활비를 먼저 확보한 뒤, 아주 보수적인 기준으로 판단하는 것이 좋습니다."
            )

        if risk_type == "AGGRESSIVE":
            return (
                "위험형 성향에서는 성장 가능성이 있는 자산에 관심을 가질 수 있지만, "
                "여유자금 범위를 넘어서면 손실 발생 시 생활 안정성이 흔들릴 수 있습니다. "
                "변동성과 원금 손실 가능성을 반드시 함께 고려해야 합니다."
            )

        return (
            "보통형 성향에서는 소비, 저축, 투자 사이의 균형이 중요합니다. "
            "여유자금이 있더라도 전액을 투자 관점으로 보기보다는 비상금과 단기 지출 계획을 함께 고려하는 것이 좋습니다."
        )

    def _build_top_category_text(
        self,
        category_items: List[FinanceSpendingContextItem],
    ) -> str:
        if not category_items:
            return ""

        top_items = category_items[:3]

        category_lines = [
            f"{item.category} {item.category_amount}원"
            for item in top_items
        ]

        return (
            "\n\n소비 비중이 큰 카테고리는 "
            + ", ".join(category_lines)
            + " 순으로 확인됩니다. 이 항목들은 투자 여력을 판단하기 전에 먼저 점검해볼 만합니다."
        )

    def _get_investment_disclaimer(self) -> str:
        return (
            "본 서비스의 정보는 사용자의 소비 데이터에 기반한 참고용 안내이며, "
            "특정 금융상품 또는 종목에 대한 투자 권유가 아닙니다. "
            "투자 결정과 그에 따른 손익 책임은 본인에게 있으며, "
            "필요한 경우 전문가와 상담하시기 바랍니다."
        )

    def _to_decimal(self, value) -> Decimal:
        if value is None:
            return ZERO

        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return ZERO

    def _decimal_to_money_string(self, value) -> Optional[str]:
        if value is None:
            return None

        decimal_value = self._to_decimal(value)
        return str(decimal_value.quantize(MONEY_QUANTIZE))

    def _decimal_to_ratio_string(self, value) -> str:
        decimal_value = self._to_decimal(value)
        return str(decimal_value.quantize(MONEY_QUANTIZE))

    def _decimal_to_korean_money(self, value) -> str:
        decimal_value = self._to_decimal(value)
        rounded_value = int(decimal_value)

        return f"{rounded_value:,}원"