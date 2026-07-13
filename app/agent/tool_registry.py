from sqlalchemy.orm import Session

from app.agent.tools.spending_analysis_tool import (
    get_monthly_spending_categories_tool,
    get_monthly_spending_summary_tool,
)
from app.agent.tools.user_rag_search_tool import (
    search_user_agent_chat_rag_tool,
    search_user_spending_rag_tool,
)
from app.agent.tools.stock_price_tool import (
    get_stock_price_tool,
)


def run_registered_tool(
    db: Session,
    action: str,
    user_id: int,
    message: str,
    month: str | None = None,
) -> dict:
    """
    LLM Router가 결정한 action에 맞는 실제 Tool을 실행한다.

    구분:
    - spending_summary: 정확한 월별 요약 DB 조회
    - spending_category: 정확한 카테고리별 소비 DB 조회
    - spending_report: 소비 분석 RAG 검색
    - agent_chat_rag: 과거 Agent 대화 RAG 검색
    """

    if action == "spending_summary":
        if not month:
            return {
                "success": False,
                "data": None,
                "message": (
                    "어떤 월의 소비 요약인지 "
                    "알 수 없습니다."
                ),
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
                "message": (
                    "어떤 월의 카테고리별 소비인지 "
                    "알 수 없습니다."
                ),
            }

        return get_monthly_spending_categories_tool(
            db=db,
            user_id=user_id,
            month=month,
        )

    if action == "spending_report":
        # month가 있으면 해당 월만 검색하고,
        # month가 None이면 전체 소비 분석 문서에서 검색한다.
        return search_user_spending_rag_tool(
            user_id=user_id,
            query=message,
            month=month,
        )
    
    if action == "stock_price":
        return get_stock_price_tool(
            db=db,
            user_id=user_id,
            message=message,
        )

    if action == "agent_chat_rag":
        return search_user_agent_chat_rag_tool(
            user_id=user_id,
            query=message,
        )

    return {
        "success": False,
        "data": None,
        "message": (
            f"지원하지 않는 action입니다: {action}"
        ),
    }