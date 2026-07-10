from typing import Any, Literal, TypedDict


AgentIntent = Literal[
    "spending_summary",
    "spending_category",
    "spending_report",
    "agent_chat_rag",
    "finance_profile",
    "stock_price",
    "stock_news",
    "product_recommend",
    "disclaimer",
    "general",
]


class AgentState(TypedDict, total=False):
    user_id: int
    session_id: int

    message: str
    month: str | None
    history: list[dict[str, Any]]

    intent: AgentIntent

    tool_result: dict[str, Any] | None
    rag_result: dict[str, Any] | None
    chat_rag_result: dict[str, Any] | None

    answer: str
    error: str | None