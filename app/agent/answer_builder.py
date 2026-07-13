import json
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from ollama import Client, ResponseError

from app.agent.prompts import AGENT_ANSWER_SYSTEM_PROMPT
from app.core.config import settings


client = Client(
    host=settings.ollama_base_url.rstrip("/"),
    timeout=300.0,
)


def to_float(
    value: int | float | str | Decimal | None,
) -> float:
    """
    DB Decimal, 문자열 숫자, int, float를 안전하게 float로 변환한다.
    """

    if value is None:
        return 0.0

    try:
        return float(value)
    except (TypeError, ValueError, InvalidOperation):
        return 0.0


def format_won(
    value: int | float | str | Decimal | None,
) -> str:
    """
    금액 값을 쉼표가 포함된 원화 문자열로 변환한다.
    """

    return f"{int(to_float(value)):,}원"


def build_rule_based_answer(
    action: str,
    tool_result: dict[str, Any] | None,
) -> str | None:
    """
    정확한 수치가 중요한 답변은 LLM을 거치지 않고 직접 생성한다.
    """

    if not tool_result or not tool_result.get("success"):
        return None

    data = tool_result.get("data")

    if not data:
        return None

    if action == "spending_summary":
        month = data.get("month") or "해당 월"
        total_income = data.get("total_income")
        total_spending = data.get("total_spending")
        fixed_expense = data.get("fixed_expense")
        variable_expense = data.get("variable_expense")
        remaining_money = data.get("remaining_money")
        spending_diff = to_float(data.get("spending_diff"))
        spending_change_rate = to_float(
            data.get("spending_change_rate")
        )

        if spending_diff > 0:
            comparison_text = (
                f"전월보다 {format_won(abs(spending_diff))} "
                f"늘었어요. 변화율은 "
                f"{spending_change_rate:.2f}%예요."
            )
        elif spending_diff < 0:
            comparison_text = (
                f"전월보다 {format_won(abs(spending_diff))} "
                f"줄었어요. 변화율은 "
                f"{spending_change_rate:.2f}%예요."
            )
        else:
            comparison_text = (
                "전월과 지출 금액이 같아요. "
                f"변화율은 {spending_change_rate:.2f}%예요."
            )

        return (
            f"{month} 소비 요약을 알려드릴게요.\n\n"
            f"총수입은 {format_won(total_income)}, "
            f"총지출은 {format_won(total_spending)}이에요.\n"
            f"고정비는 {format_won(fixed_expense)}, "
            f"변동비는 {format_won(variable_expense)}이고, "
            f"남은 금액은 {format_won(remaining_money)}입니다.\n\n"
            f"{comparison_text}"
        )

    if action == "spending_category":
        month = data.get("month") or "해당 월"
        categories = data.get("categories", [])

        if not categories:
            return None

        top = categories[0]

        lines = [
            f"{month} 카테고리별 소비를 보면,",
            (
                f"가장 많이 쓴 카테고리는 "
                f"{top.get('category') or '미분류'}이고 "
                f"{format_won(top.get('category_amount'))}을 "
                f"사용했어요."
            ),
            "",
            "상위 카테고리는 다음과 같아요.",
        ]

        for item in categories[:5]:
            category = item.get("category") or "미분류"
            amount = format_won(item.get("category_amount"))
            ratio = to_float(item.get("category_ratio"))

            lines.append(
                f"- {category}: {amount} ({ratio:.1f}%)"
            )

        return "\n".join(lines)
    
    if action == "stock_price":
        stocks = data.get("stocks", [])

        if not stocks:
            return None

        lines = [
            "관심종목의 최근 시세를 알려드릴게요.",
            "",
        ]

        for stock in stocks:
            stock_name = (
                stock.get("stock_name")
                or "종목명 없음"
            )
            stock_code = (
                stock.get("stock_code")
                or "-"
            )

            lines.append(
                f"[{stock_name}({stock_code})]"
            )

            if not stock.get("has_price_data"):
                lines.append(
                    "- 최신 시세 데이터가 없습니다."
                )
                lines.append("")
                continue

            price_date = (
                stock.get("price_date")
                or "기준일 미확인"
            )
            close_price = stock.get(
                "close_price"
            )
            previous_close = stock.get(
                "previous_close"
            )
            change_rate = stock.get(
                "change_rate"
            )
            volume = stock.get("volume")

            lines.append(
                f"- 기준일: {price_date}"
            )

            if close_price is not None:
                lines.append(
                    f"- 종가: {format_won(close_price)}"
                )

            if previous_close is not None:
                lines.append(
                    f"- 전일 종가: "
                    f"{format_won(previous_close)}"
                )

            if change_rate is not None:
                lines.append(
                    f"- 등락률: "
                    f"{to_float(change_rate):.2f}%"
                )

            if volume is not None:
                lines.append(
                    f"- 거래량: "
                    f"{int(to_float(volume)):,}주"
                )

            lines.append("")

        return "\n".join(lines).strip()

    return None


def build_llm_answer(
    message: str,
    action: str,
    tool_result: dict | None = None,
    rag_result: dict | None = None,
    chat_rag_result: dict | None = None,
    history: list[dict] | None = None,
) -> str:
    """
    RAG 결과나 일반 질문은 Ollama 채팅 모델로 답변을 생성한다.
    """

    user_prompt = f"""
사용자 질문:
{message}

선택된 action:
{action}

정확한 DB Tool 결과:
{json.dumps(tool_result, ensure_ascii=False, default=str)}

소비 분석 RAG 결과:
{json.dumps(rag_result, ensure_ascii=False, default=str)}

과거 Agent 대화 RAG 결과:
{json.dumps(chat_rag_result, ensure_ascii=False, default=str)}

최근 대화:
{json.dumps(history or [], ensure_ascii=False, default=str)}

위 정보만 근거로 사용자에게 답변하세요.
정보가 없으면 추측하지 말고 데이터가 없다고 말하세요.
""".strip()

    try:
        response = client.chat(
            model=settings.ollama_llm_model,
            messages=[
                {
                    "role": "system",
                    "content": AGENT_ANSWER_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            stream=False,
            options={
                "temperature": 0.3,
            },
            keep_alive="30m",
        )

    except ResponseError as exc:
        raise RuntimeError(
            f"Ollama 모델 실행에 실패했습니다: {exc.error}"
        ) from exc

    except httpx.TimeoutException as exc:
        raise RuntimeError(
            "Ollama 서버 응답 시간이 초과되었습니다."
        ) from exc

    except httpx.ConnectError as exc:
        raise RuntimeError(
            "Ollama 서버에 연결할 수 없습니다. "
            f"주소를 확인해주세요: {settings.ollama_base_url}"
        ) from exc

    content = response.message.content

    if not content:
        return "답변을 생성하지 못했습니다."

    return content.strip()