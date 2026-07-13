# ============================================================
# 파일 위치: app/agent/tools/stock_price_tool.py
# 역할:
#   - 로그인 사용자의 관심종목을 기준으로 종목을 찾습니다.
#   - 해당 종목의 최신 시세를 조회합니다.
#   - 최종 답변을 만들지 않고 구조화된 데이터만 반환합니다.
# ============================================================

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.stock_chatbot_repository import (
    StockChatbotRepository,
)
from app.services.stock_chatbot_intent_service import (
    StockChatbotIntentService,
)


def _serialize_number(
    value: int | float | Decimal | None,
) -> float | None:
    """
    Decimal 등 DB 숫자 타입을 JSON 직렬화 가능한 float로 변환합니다.
    """

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_first_attribute(
    target: Any,
    *attribute_names: str,
) -> Any:
    """
    모델의 실제 컬럼명이 조금 다르더라도
    첫 번째로 존재하는 값을 반환합니다.
    """

    if target is None:
        return None

    for attribute_name in attribute_names:
        value = getattr(
            target,
            attribute_name,
            None,
        )

        if value is not None:
            return value

    return None


def _select_target_watchlist_rows(
    watchlist_rows: list,
    message: str,
) -> list:
    """
    질문에 포함된 종목명·종목코드를 기준으로
    관심종목 중 조회 대상 종목을 선택합니다.

    질문에서 특정 종목을 찾지 못하면
    관심종목 전체를 반환합니다.
    """

    intent_service = StockChatbotIntentService()

    intent_result = intent_service.classify(
        message=message,
        stock_id=None,
        watchlist_rows=watchlist_rows,
    )

    if not intent_result.target_stock_ids:
        return watchlist_rows

    target_stock_ids = set(
        intent_result.target_stock_ids
    )

    return [
        row
        for row in watchlist_rows
        if row[1].id in target_stock_ids
    ]


def get_stock_price_tool(
    db: Session,
    user_id: int,
    message: str,
) -> dict:
    """
    로그인 사용자의 관심종목 최신 시세를 조회합니다.

    Tool 공통 반환 형식:
    {
        "success": bool,
        "data": dict | None,
        "message": str
    }
    """

    repository = StockChatbotRepository(db)

    watchlist_rows = (
        repository.list_user_watchlist_stocks(
            user_id=user_id,
        )
    )

    if not watchlist_rows:
        return {
            "success": False,
            "data": None,
            "message": (
                "아직 등록된 관심종목이 없습니다. "
                "관심종목을 먼저 등록해주세요."
            ),
        }

    selected_rows = _select_target_watchlist_rows(
        watchlist_rows=watchlist_rows,
        message=message,
    )

    if not selected_rows:
        return {
            "success": False,
            "data": None,
            "message": (
                "질문한 종목을 현재 관심종목에서 "
                "찾지 못했습니다."
            ),
        }

    stock_items = []

    # 답변이 지나치게 길어지지 않도록 최대 5개까지만 조회
    for _, stock in selected_rows[:5]:
        latest_price = repository.get_latest_price(
            stock_id=stock.id,
        )

        if latest_price is None:
            stock_items.append(
                {
                    "stock_id": int(stock.id),
                    "stock_code": stock.stock_code,
                    "stock_name": stock.stock_name,
                    "market": getattr(
                        stock,
                        "market",
                        None,
                    ),
                    "price_date": None,
                    "close_price": None,
                    "previous_close": None,
                    "change_rate": None,
                    "volume": None,
                    "market_cap": None,
                    "has_price_data": False,
                }
            )
            continue

        price_date = _get_first_attribute(
            latest_price,
            "price_date",
            "date",
        )

        close_price = _get_first_attribute(
            latest_price,
            "close_price",
            "close",
        )

        previous_close = _get_first_attribute(
            latest_price,
            "previous_close",
        )

        change_rate = _get_first_attribute(
            latest_price,
            "change_rate",
        )

        volume = _get_first_attribute(
            latest_price,
            "volume",
        )

        market_cap = _get_first_attribute(
            latest_price,
            "market_cap",
        )

        stock_items.append(
            {
                "stock_id": int(stock.id),
                "stock_code": stock.stock_code,
                "stock_name": stock.stock_name,
                "market": getattr(
                    stock,
                    "market",
                    None,
                ),
                "price_date": (
                    price_date.isoformat()
                    if hasattr(
                        price_date,
                        "isoformat",
                    )
                    else (
                        str(price_date)
                        if price_date
                        else None
                    )
                ),
                "close_price": _serialize_number(
                    close_price
                ),
                "previous_close": _serialize_number(
                    previous_close
                ),
                "change_rate": _serialize_number(
                    change_rate
                ),
                "volume": _serialize_number(
                    volume
                ),
                "market_cap": _serialize_number(
                    market_cap
                ),
                "has_price_data": True,
            }
        )

    return {
        "success": True,
        "data": {
            "stocks": stock_items,
        },
        "message": (
            f"관심종목 {len(stock_items)}개의 "
            "최신 시세를 조회했습니다."
        ),
    }