from sqlalchemy.orm import Session

from app.services.spending_analysis_service import SpendingAnalysisService


def get_monthly_spending_summary_tool(
    db: Session,
    user_id: int,
    month: str,
) -> dict:
    """
    월별 소비 요약을 DB에서 조회한다.
    정확한 총지출, 총수입, 고정비, 변동비, 남은 금액 질문에 사용한다.
    """

    service = SpendingAnalysisService(db)

    summary = service.get_monthly_summary_by_month(
        user_id=user_id,
        month=month,
    )

    if not summary:
        return {
            "success": False,
            "data": None,
            "message": f"{month} 소비 요약 데이터가 없습니다.",
        }

    return {
        "success": True,
        "data": {
            "summary_id": int(summary.id),
            "month": summary.month,
            "monthly_salary": int(summary.monthly_salary or 0),
            "total_income": int(summary.total_income or 0),
            "total_spending": int(summary.total_spending or 0),
            "fixed_expense": int(summary.fixed_expense or 0),
            "variable_expense": int(summary.variable_expense or 0),
            "remaining_money": int(summary.remaining_money or 0),
            "spending_diff": int(summary.spending_diff or 0),
            "spending_change_rate": float(summary.spending_change_rate or 0),
        },
        "message": "월별 소비 요약 조회 성공",
    }


def get_monthly_spending_categories_tool(
    db: Session,
    user_id: int,
    month: str,
) -> dict:
    """
    월별 카테고리별 소비를 DB에서 조회한다.
    정확한 카테고리 금액, 가장 많이 쓴 카테고리 질문에 사용한다.
    """

    service = SpendingAnalysisService(db)

    categories = service.get_category_spendings_by_user_and_month(
        user_id=user_id,
        month=month,
    )

    if not categories:
        return {
            "success": False,
            "data": None,
            "message": f"{month} 카테고리별 소비 데이터가 없습니다.",
        }

    return {
        "success": True,
        "data": {
            "month": month,
            "categories": [
                {
                    "category": item.category,
                    "category_amount": int(item.category_amount or 0),
                    "category_ratio": float(item.category_ratio or 0),
                    "transaction_count": int(item.transaction_count or 0),
                    "previous_category_amount": int(item.previous_category_amount or 0),
                    "spending_diff": int(item.spending_diff or 0),
                    "spending_change_rate": float(item.spending_change_rate or 0),
                }
                for item in categories
            ],
        },
        "message": "카테고리별 소비 조회 성공",
    }