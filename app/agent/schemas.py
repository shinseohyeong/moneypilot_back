from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AgentAction = Literal[
    "spending_summary",
    "spending_category",
    "spending_report",
    "stock_price",
    "stock_news",
    "agent_chat_rag",
    "finance_profile",
    "risk_profile",
    "general",
]

AgentChatType = Literal[
    "general",
    "consumption",
    "finance",
    "stock",
    "mixed",
]

AgentMessageRole = Literal[
    "user",
    "assistant",
    "system",
    "tool",
]


class AgentChatRequest(BaseModel):
    session_id: int | None = Field(
        default=None,
        description="기존 대화방 ID. 새 대화라면 생략하거나 null",
    )

    message: str = Field(
        min_length=1,
        max_length=5000,
    )


class AgentDecision(BaseModel):
    action: AgentAction

    month: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )

    reason: str | None = None


class AgentMessageResponse(BaseModel):
    id: int
    session_id: int

    role: AgentMessageRole
    content: str

    intent: str | None = None
    used_tools: str | None = None
    disclaimer: str | None = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentChatResponse(BaseModel):
    success: bool

    session_id: int | None = None
    chat_type: AgentChatType | None = None
    intent: str | None = None

    answer: str
    assistant_message: AgentMessageResponse | None = None

    error: str | None = None


class AgentSessionResponse(BaseModel):
    id: int
    title: str | None = None
    chat_type: AgentChatType

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentSessionListItemResponse(BaseModel):
    id: int
    title: str | None = None
    chat_type: AgentChatType

    last_message: str | None = None
    last_message_at: datetime | None = None

    created_at: datetime
    updated_at: datetime


class AgentSessionListResponse(BaseModel):
    success: bool

    sessions: list[AgentSessionListItemResponse] = Field(
        default_factory=list,
    )


class AgentSessionMessagesResponse(BaseModel):
    success: bool

    session: AgentSessionResponse | None = None
    messages: list[AgentMessageResponse] = Field(
        default_factory=list,
    )

    message: str | None = None