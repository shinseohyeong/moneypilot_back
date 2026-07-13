# app/rag/ingestors/spending_ingestor.py

from app.rag.metadata import RagDomain, RagSourceType, RagCreatedBy
from app.rag.rag_service import upsert_rag_document


def safe_int(value) -> int:
    if value is None:
        return 0
    return int(value)


def safe_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)


def build_spending_report_text(
    summary,
    categories: list | None = None,
    report=None,
) -> str:
    """
    월별 소비 요약 + 카테고리 + AI 리포트를 RAG 저장용 문서로 변환한다.
    """

    text = (
        f"{summary.month} 소비 분석 결과입니다. "
        f"총수입은 {safe_int(summary.total_income)}원이고, "
        f"총지출은 {safe_int(summary.total_spending)}원입니다. "
        f"고정비는 {safe_int(summary.fixed_expense)}원, "
        f"변동비는 {safe_int(summary.variable_expense)}원이며, "
        f"남은 금액은 {safe_int(summary.remaining_money)}원입니다. "
    )

    if getattr(summary, "monthly_salary", None) is not None:
        text += f"월급은 {safe_int(summary.monthly_salary)}원입니다. "

    if getattr(summary, "spending_diff", None) is not None:
        text += f"전월 대비 지출 차이는 {safe_int(summary.spending_diff)}원입니다. "

    if getattr(summary, "spending_change_rate", None) is not None:
        text += f"전월 대비 지출 변화율은 {safe_float(summary.spending_change_rate)}%입니다. "

    if categories:
        category_text = ", ".join(
            [
                (
                    f"{category.category} {safe_int(category.category_amount)}원 "
                    f"비율 {safe_float(category.category_ratio)}%"
                )
                for category in categories
            ]
        )

        text += f"카테고리별 주요 지출은 {category_text}입니다. "

    if report:
        report_content = (
            getattr(report, "content", None)
            or getattr(report, "report_content", None)
            or getattr(report, "llm_summary", None)
        )

        if report_content:
            text += f"AI 소비 리포트 내용은 다음과 같습니다. {report_content}"

    return text


def ingest_spending_report(
    user_id: int,
    summary,
    categories: list | None = None,
    report=None,
) -> dict:
    """
    월별 소비 분석 결과를 RAG에 저장한다.
    """

    content = build_spending_report_text(
        summary=summary,
        categories=categories,
        report=report,
    )

    document_key = f"user:{user_id}:spending:{summary.month}"

    return upsert_rag_document(
        user_id=user_id,
        domain=RagDomain.SPENDING,
        source_type=RagSourceType.MONTHLY_REPORT,
        source_id=summary.id,
        document_key=document_key,
        content=content,
        metadata={
            "month": summary.month,
            "summary_id": str(summary.id),
            "total_spending": str(summary.total_spending),
            "remaining_money": str(summary.remaining_money),
            "fixed_expense": str(summary.fixed_expense),
            "variable_expense": str(summary.variable_expense),
            "created_by": RagCreatedBy.SYSTEM,
        },
    )