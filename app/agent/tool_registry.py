from sqlalchemy.orm import Session

from app.agent.tools.spending_analysis_tool import (
    get_monthly_spending_summary_tool,
    get_monthly_spending_categories_tool,
)
from app.agent.tools.user_rag_search_tool import (
    search_user_spending_rag_tool,
    search_user_agent_chat_rag_tool,
)


def run_registered_tool(
    db: Session,
    action: str,
    user_id: int,
    message: str,
    month: str | None = None,
) -> dict:
    """
    LLM Router가 결정한 action에 맞는 실제 tool을 실행한다.
    """

    if action == "spending_summary":
        if not month:
            return {
                "success": False,
                "data": None,
                "message": "어떤 월의 소비 요약인지 알 수 없습니다.",
            }

        return get_monthly_spending_summary_tool(
            db=db,
            user_id=user_id,
            month=month,
        )

    if action == "spending_category":
        if not month:
            return {
                "success": False,
                "data": None,
                "message": "어떤 월의 카테고리별 소비인지 알 수 없습니다.",
            }

        return get_monthly_spending_categories_tool(
            db=db,
            user_id=user_id,
            month=month,
        )

    if action == "spending_report":
        return search_user_spending_rag_tool(
            user_id=user_id,
            query=message,
        )

    if action == "agent_chat_rag":
        return search_user_agent_chat_rag_tool(
            user_id=user_id,
            query=message,
        )

    return {
        "success": False,
        "data": None,
        "message": f"아직 지원하지 않는 action입니다: {action}",
    }