from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from app.services.spending_analysis_service import (
    SpendingAnalysisService,
    SpendingService,
)


def to_int(
    value: int | float | str | Decimal | None,
) -> int:
    """
    Decimal, 문자열, 숫자 값을 안전하게 int로 변환한다.
    """

    if value is None:
        return 0

    try:
        return int(Decimal(str(value)))

    except (
        TypeError,
        ValueError,
        InvalidOperation,
    ):
        return 0


def to_float(
    value: int | float | str | Decimal | None,
) -> float:
    """
    Decimal, 문자열, 숫자 값을 안전하게 float로 변환한다.
    """

    if value is None:
        return 0.0

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
        InvalidOperation,
    ):
        return 0.0


def get_item_value(
    item: Any,
    *keys: str,
    default: Any = None,
) -> Any:
    """
    dict, Pydantic 객체, SQLAlchemy 객체에서
    여러 후보 이름 중 존재하는 값을 가져온다.
    """

    for key in keys:
        if isinstance(item, dict):
            value = item.get(key)

        else:
            value = getattr(
                item,
                key,
                None,
            )

        if value is not None:
            return value

    return default


def normalize_result_dict(
    result: Any,
) -> dict:
    """
    Service 반환값을 dict 형태로 정규화한다.
    """

    if result is None:
        return {}

    if isinstance(result, dict):
        return result

    if hasattr(result, "model_dump"):
        return result.model_dump()

    if hasattr(result, "dict"):
        return result.dict()

    return {}


def get_monthly_spending_summary_tool(
    db: Session,
    user_id: int,
    month: str,
) -> dict:
    """
    월별 소비 요약을 DB에서 조회한다.

    총지출, 총수입, 고정비, 변동비,
    남은 금액 등의 정확한 수치 질문에 사용한다.
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
            "message": (
                f"{month} 소비 요약 데이터가 없습니다."
            ),
        }

    return {
        "success": True,
        "data": {
            "summary_id": int(summary.id),
            "month": summary.month,
            "monthly_salary": to_int(
                summary.monthly_salary
            ),
            "total_income": to_int(
                summary.total_income
            ),
            "total_spending": to_int(
                summary.total_spending
            ),
            "fixed_expense": to_int(
                summary.fixed_expense
            ),
            "variable_expense": to_int(
                summary.variable_expense
            ),
            "remaining_money": to_int(
                summary.remaining_money
            ),
            "spending_diff": to_int(
                summary.spending_diff
            ),
            "spending_change_rate": to_float(
                summary.spending_change_rate
            ),
        },
        "message": "월별 소비 요약 조회 성공",
    }


def get_monthly_spending_categories_tool(
    db: Session,
    user_id: int,
    month: str,
) -> dict:
    """
    월별 카테고리별 소비 데이터를 조회한다.

    현재 SpendingService에 이미 구현된
    get_monthly_overspending_categories() 결과 중
    top_spending_categories를 재사용한다.
    """

    summary_service = SpendingAnalysisService(db)
    spending_service = SpendingService(db)

    # 비율 계산과 summary_id 추적을 위해 월별 요약도 조회한다.
    summary = summary_service.get_monthly_summary_by_month(
        user_id=user_id,
        month=month,
    )

    if not summary:
        return {
            "success": False,
            "data": None,
            "message": (
                f"{month} 소비 요약 데이터가 없습니다."
            ),
        }

    overspending_result = (
        spending_service.get_monthly_overspending_categories(
            user_id=user_id,
            month=month,
        )
    )

    result_data = normalize_result_dict(
        overspending_result
    )

    # Service 응답이 {"data": {...}} 형태인 경우도 대응한다.
    nested_data = result_data.get("data")

    if isinstance(nested_data, dict):
        result_data = nested_data

    raw_categories = (
        result_data.get("top_spending_categories")
        or result_data.get("categories")
        or []
    )

    if not raw_categories:
        return {
            "success": False,
            "data": None,
            "message": (
                f"{month} 카테고리별 소비 데이터가 없습니다."
            ),
        }

    total_spending = to_float(
        summary.total_spending
    )

    categories: list[dict[str, Any]] = []

    for item in raw_categories:
        category = get_item_value(
            item,
            "category",
            "category_name",
            default="미분류",
        )

        category_amount = to_int(
            get_item_value(
                item,
                "category_amount",
                "current_category_amount",
                "current_amount",
                "amount",
                "total_amount",
                default=0,
            )
        )

        raw_ratio = get_item_value(
            item,
            "category_ratio",
            "ratio",
            "spending_ratio",
            default=None,
        )

        if raw_ratio is None:
            category_ratio = (
                category_amount
                / total_spending
                * 100
                if total_spending > 0
                else 0.0
            )

        else:
            category_ratio = to_float(
                raw_ratio
            )

        previous_category_amount = to_int(
            get_item_value(
                item,
                "previous_category_amount",
                "previous_amount",
                "previous_month_amount",
                default=0,
            )
        )

        spending_diff = to_int(
            get_item_value(
                item,
                "spending_diff",
                "change_amount",
                "amount_diff",
                default=(
                    category_amount
                    - previous_category_amount
                ),
            )
        )

        spending_change_rate = to_float(
            get_item_value(
                item,
                "spending_change_rate",
                "change_rate",
                default=0,
            )
        )

        transaction_count = to_int(
            get_item_value(
                item,
                "transaction_count",
                "count",
                default=0,
            )
        )

        categories.append(
            {
                "category": category,
                "category_amount": category_amount,
                "category_ratio": category_ratio,
                "transaction_count": transaction_count,
                "previous_category_amount": (
                    previous_category_amount
                ),
                "spending_diff": spending_diff,
                "spending_change_rate": (
                    spending_change_rate
                ),
            }
        )

    # 가장 많이 쓴 카테고리가 첫 번째가 되도록 정렬한다.
    categories.sort(
        key=lambda item: item["category_amount"],
        reverse=True,
    )

    return {
        "success": True,
        "data": {
            "summary_id": int(summary.id),
            "month": month,
            "categories": categories,
        },
        "message": "카테고리별 소비 조회 성공",
    }