import json
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.agent.prompts import AGENT_ANSWER_SYSTEM_PROMPT


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def format_won(value: int | float | None) -> str:
    if value is None:
        value = 0

    return f"{int(value):,}원"


def build_rule_based_answer(
    action: str,
    tool_result: dict[str, Any],
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
        month = data.get("month")
        total_income = data.get("total_income")
        total_spending = data.get("total_spending")
        fixed_expense = data.get("fixed_expense")
        variable_expense = data.get("variable_expense")
        remaining_money = data.get("remaining_money")
        spending_diff = data.get("spending_diff")
        spending_change_rate = data.get("spending_change_rate")

        diff_text = "늘었어요" if spending_diff and spending_diff > 0 else "줄었어요"

        return (
            f"{month} 소비 요약을 알려줄게요.\n\n"
            f"총수입은 {format_won(total_income)}, "
            f"총지출은 {format_won(total_spending)}이에요.\n"
            f"고정비는 {format_won(fixed_expense)}, "
            f"변동비는 {format_won(variable_expense)}이고, "
            f"남은 금액은 {format_won(remaining_money)}입니다.\n\n"
            f"전월 대비 지출은 {format_won(abs(spending_diff or 0))} 정도 {diff_text} "
            f"변화율은 {spending_change_rate or 0:.2f}%예요."
        )

    if action == "spending_category":
        month = data.get("month")
        categories = data.get("categories", [])

        if not categories:
            return None

        top = categories[0]

        lines = [
            f"{month} 카테고리별 소비를 보면,",
            f"가장 많이 쓴 카테고리는 {top.get('category')}이고 "
            f"{format_won(top.get('category_amount'))}을 사용했어요.",
            "",
            "상위 카테고리는 다음과 같아요.",
        ]

        for item in categories[:5]:
            lines.append(
                f"- {item.get('category')}: "
                f"{format_won(item.get('category_amount'))} "
                f"({item.get('category_ratio', 0):.1f}%)"
            )

        return "\n".join(lines)

    return None


def build_llm_answer(
    message: str,
    action: str,
    tool_result: dict | None = None,
    rag_result: dict | None = None,
    history: list[dict] | None = None,
) -> str:
    """
    RAG 결과나 일반 질문은 LLM으로 자연어 답변을 생성한다.
    """

    user_prompt = f"""
사용자 질문:
{message}

action:
{action}

tool_result:
{json.dumps(tool_result, ensure_ascii=False, default=str)}

rag_result:
{json.dumps(rag_result, ensure_ascii=False, default=str)}

최근 대화:
{json.dumps(history or [], ensure_ascii=False, default=str)}

위 정보를 바탕으로 사용자에게 답변해줘.
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0.3,
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
    )

    return response.choices[0].message.content