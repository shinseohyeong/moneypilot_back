from typing import Any, TypedDict

from app.agent.schemas import AgentAction


class AgentState(TypedDict, total=False):
    user_id: int
    session_id: int

    message: str
    month: str | None
    history: list[dict[str, Any]]

    intent: AgentAction

    tool_result: dict[str, Any] | None
    rag_result: dict[str, Any] | None
    stock_rag_result: dict[str, Any] | None
    chat_rag_result: dict[str, Any] | None

    answer: str
    error: str | None