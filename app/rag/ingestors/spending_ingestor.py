# app/rag/ingestors/spending_ingestor.py

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from app.rag.metadata import (
    RagCreatedBy,
    RagDomain,
    RagSourceType,
)
from app.rag.rag_service import upsert_rag_document


logger = logging.getLogger(__name__)


def safe_int(value: Any) -> int:
    """
    Decimal, 문자열, int, float 값을 안전하게 int로 변환한다.
    변환할 수 없는 값은 0을 반환한다.
    """

    if value is None:
        return 0

    try:
        return int(Decimal(str(value)))
    except (TypeError, ValueError, InvalidOperation):
        return 0


def safe_float(value: Any) -> float:
    """
    Decimal, 문자열, int, float 값을 안전하게 float로 변환한다.
    변환할 수 없는 값은 0.0을 반환한다.
    """

    if value is None:
        return 0.0

    try:
        return float(Decimal(str(value)))
    except (TypeError, ValueError, InvalidOperation):
        return 0.0


def clean_text(value: Any) -> str:
    """
    RAG 문서에 넣을 문자열을 정리한다.
    None 또는 빈 문자열은 빈 문자열로 반환한다.
    """

    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    return text


def build_category_text(
    categories: list | None,
) -> str:
    """
    카테고리별 소비 데이터를 자연어 문자열로 변환한다.
    """

    if not categories:
        return ""

    category_parts: list[str] = []

    for category in categories:
        category_name = clean_text(
            getattr(category, "category", None)
        )

        if not category_name:
            continue

        category_amount = safe_int(
            getattr(category, "category_amount", 0)
        )

        category_ratio = safe_float(
            getattr(category, "category_ratio", 0)
        )

        transaction_count = safe_int(
            getattr(category, "transaction_count", 0)
        )

        spending_diff = safe_int(
            getattr(category, "spending_diff", 0)
        )

        spending_change_rate = safe_float(
            getattr(category, "spending_change_rate", 0)
        )

        category_part = (
            f"{category_name} 카테고리는 "
            f"{category_amount:,}원을 사용했고, "
            f"전체 소비에서 {category_ratio:.2f}%를 차지했습니다."
        )

        if transaction_count > 0:
            category_part += (
                f" 거래 건수는 {transaction_count}건입니다."
            )

        if spending_diff != 0:
            category_part += (
                f" 전월 대비 지출 차이는 "
                f"{spending_diff:,}원입니다."
            )

        if spending_change_rate != 0:
            category_part += (
                f" 전월 대비 변화율은 "
                f"{spending_change_rate:.2f}%입니다."
            )

        category_parts.append(category_part)

    if not category_parts:
        return ""

    return " ".join(category_parts)


def build_report_text(
    report,
) -> str:
    """
    AnalysisReport 모델의 여러 텍스트 필드를
    하나의 RAG 문서용 문자열로 합친다.
    """

    if report is None:
        return ""

    field_labels = [
        ("report_title", "리포트 제목"),
        ("summary_text", "소비 요약"),
        ("category_text", "카테고리 분석"),
        ("overspending_text", "과소비 분석"),
        ("card_text", "카드 사용 분석"),
        ("compare_text", "전월 비교 분석"),
        ("recommendation_text", "소비 개선 추천"),
        ("agent_response", "AI 소비 코칭"),
    ]

    report_parts: list[str] = []

    for field_name, label in field_labels:
        field_value = clean_text(
            getattr(report, field_name, None)
        )

        if not field_value:
            continue

        report_parts.append(
            f"{label}: {field_value}"
        )

    return " ".join(report_parts)


def build_spending_report_text(
    summary,
    categories: list | None = None,
    report=None,
) -> str:
    """
    월별 소비 요약, 카테고리별 소비 데이터,
    AI 소비 리포트를 RAG 저장용 자연어 문서로 변환한다.
    """

    month = clean_text(
        getattr(summary, "month", None)
    )

    total_income = safe_int(
        getattr(summary, "total_income", 0)
    )

    monthly_salary = safe_int(
        getattr(summary, "monthly_salary", 0)
    )

    total_spending = safe_int(
        getattr(summary, "total_spending", 0)
    )

    fixed_expense = safe_int(
        getattr(summary, "fixed_expense", 0)
    )

    variable_expense = safe_int(
        getattr(summary, "variable_expense", 0)
    )

    remaining_money = safe_int(
        getattr(summary, "remaining_money", 0)
    )

    spending_diff = safe_int(
        getattr(summary, "spending_diff", 0)
    )

    spending_change_rate = safe_float(
        getattr(summary, "spending_change_rate", 0)
    )

    text_parts: list[str] = [
        (
            f"{month} 월별 소비 분석 결과입니다. "
            f"총수입은 {total_income:,}원이고, "
            f"월급은 {monthly_salary:,}원입니다. "
            f"총지출은 {total_spending:,}원입니다. "
            f"고정비는 {fixed_expense:,}원이고, "
            f"변동비는 {variable_expense:,}원입니다. "
            f"소비 후 남은 금액은 "
            f"{remaining_money:,}원입니다."
        )
    ]

    if spending_diff > 0:
        text_parts.append(
            f"전월보다 지출이 "
            f"{spending_diff:,}원 증가했습니다."
        )

    elif spending_diff < 0:
        text_parts.append(
            f"전월보다 지출이 "
            f"{abs(spending_diff):,}원 감소했습니다."
        )

    else:
        text_parts.append(
            "전월과 지출 금액 차이가 없습니다."
        )

    if spending_change_rate > 0:
        text_parts.append(
            f"전월 대비 지출 변화율은 "
            f"{spending_change_rate:.2f}% 증가입니다."
        )

    elif spending_change_rate < 0:
        text_parts.append(
            f"전월 대비 지출 변화율은 "
            f"{abs(spending_change_rate):.2f}% 감소입니다."
        )

    else:
        text_parts.append(
            "전월 대비 지출 변화율은 0%입니다."
        )

    category_text = build_category_text(categories)

    if category_text:
        text_parts.append(
            f"카테고리별 소비 분석입니다. {category_text}"
        )

    report_text = build_report_text(report)

    if report_text:
        text_parts.append(
            f"AI 소비 분석 리포트입니다. {report_text}"
        )

    return " ".join(text_parts).strip()


def ingest_spending_report(
    user_id: int,
    summary,
    categories: list | None = None,
    report=None,
) -> dict:
    """
    월별 소비 분석 데이터를 하나의 RAG 문서로 구성하고
    ChromaDB에 저장하거나 기존 문서를 갱신한다.

    같은 사용자와 같은 월의 문서는 동일한 document_key를
    사용하므로 기존 문서를 삭제한 뒤 최신 내용으로 교체된다.
    """

    summary_id = getattr(summary, "id", None)
    month = clean_text(
        getattr(summary, "month", None)
    )

    if summary_id is None:
        raise ValueError(
            "RAG 저장에 필요한 summary.id가 없습니다."
        )

    if not month:
        raise ValueError(
            "RAG 저장에 필요한 summary.month가 없습니다."
        )

    content = build_spending_report_text(
        summary=summary,
        categories=categories,
        report=report,
    )

    document_key = (
        f"user:{user_id}:spending:{month}"
    )

    logger.info(
        (
            "[SPENDING RAG INGEST START] "
            "user_id=%s, summary_id=%s, month=%s, "
            "category_count=%s, report_exists=%s, "
            "content_length=%s"
        ),
        user_id,
        summary_id,
        month,
        len(categories or []),
        report is not None,
        len(content),
    )

    result = upsert_rag_document(
        user_id=user_id,
        domain=RagDomain.SPENDING,
        source_type=RagSourceType.MONTHLY_REPORT,
        source_id=summary_id,
        document_key=document_key,
        content=content,
        metadata={
            "month": month,
            "summary_id": str(summary_id),
            "report_id": (
                str(report.id)
                if report is not None
                and getattr(report, "id", None) is not None
                else ""
            ),
            "total_income": str(
                getattr(summary, "total_income", 0)
            ),
            "monthly_salary": str(
                getattr(summary, "monthly_salary", 0)
            ),
            "total_spending": str(
                getattr(summary, "total_spending", 0)
            ),
            "remaining_money": str(
                getattr(summary, "remaining_money", 0)
            ),
            "fixed_expense": str(
                getattr(summary, "fixed_expense", 0)
            ),
            "variable_expense": str(
                getattr(summary, "variable_expense", 0)
            ),
            "category_count": len(categories or []),
            "has_report": report is not None,
            "created_by": RagCreatedBy.SYSTEM,
        },
    )

    logger.info(
        (
            "[SPENDING RAG INGEST SUCCESS] "
            "user_id=%s, month=%s, "
            "document_key=%s, chunk_count=%s"
        ),
        user_id,
        month,
        document_key,
        result.get("chunk_count", 0),
    )

    return result