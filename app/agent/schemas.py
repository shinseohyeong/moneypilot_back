from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    user_id: int = Field(default=1)
    session_id: int | None = None
    message: str


class AgentChatResponse(BaseModel):
    success: bool
    session_id: int
    intent: str | None = None
    answer: str

    tool_result: dict[str, Any] | None = None
    rag_result: dict[str, Any] | None = None
    chat_rag_result: dict[str, Any] | None = None

    history: list[dict[str, Any]] | None = None
    chat_rag_save_result: dict[str, Any] | None = None

    error: str | None = None


AgentAction = Literal[
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


class AgentDecision(BaseModel):
    action: AgentAction
    month: str | None = None
    reason: str | None = None


class AgentSessionResponse(BaseModel):
    id: int
    user_id: int
    title: str | None = None
    chat_type: str


class AgentMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    intent: str | None = None
    used_tools: str | None = None