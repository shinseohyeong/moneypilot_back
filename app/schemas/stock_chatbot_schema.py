# ============================================================
# 파일 위치: app/schemas/stock_chatbot_schema.py
# 역할:
#   - 주식 챗봇 요청/응답 schema를 정의합니다.
#   - 주식 챗봇 대화기록 조회 schema를 정의합니다.
# ============================================================

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class StockChatbotRequest(BaseModel):
    """
    주식 챗봇 질문 요청 schema입니다.
    """

    user_id: int = Field(
        ...,
        ge=1,
        description="사용자 ID",
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="사용자 질문",
    )

    stock_id: Optional[int] = Field(
        default=None,
        ge=0,
        description=(
            "특정 종목에 대한 질문일 경우 종목 ID. "
            "0 또는 null이면 관심종목 전체 기준 질문"
        ),
    )

    conversation_id: Optional[int] = Field(
        default=None,
        ge=1,
        description=(
            "기존 대화방 ID입니다. "
            "값이 없으면 첫 질문을 기준으로 새 대화방을 생성합니다."
        ),
    )


class StockChatbotStockBrief(BaseModel):
    """
    챗봇 답변에 포함할 종목별 요약 정보입니다.
    """

    stock_id: int
    stock_code: str
    stock_name: str

    current_price: Optional[str] = None
    change_rate: Optional[str] = None

    news_summary: str
    sector_summary: str
    risk_factors: str


class StockChatbotResponse(BaseModel):
    """
    주식 챗봇 응답 schema입니다.
    """

    conversation_id: int
    message_id: int
    intent: str

    user_id: int
    chat_type: str = "stock"

    user_message: str
    answer: str

    risk_type: str
    risk_label: str

    disclaimer: str

    items: List[StockChatbotStockBrief] = Field(default_factory=list)
    


class StockChatHistoryItem(BaseModel):
    """
    저장된 주식 챗봇 대화 1건입니다.
    """

    message_id: int

    user_message: str
    agent_response: str

    referenced_stock_id: Optional[int] = None
    used_tools: Optional[str] = None
    disclaimer: Optional[str] = None

    created_at: datetime


class StockChatHistoryResponse(BaseModel):
    """
    사용자의 주식 챗봇 대화기록 응답입니다.
    """

    user_id: int
    chat_type: str = "stock"

    total_count: int
    items: List[StockChatHistoryItem] = Field(default_factory=list)

class StockChatConversationItem(BaseModel):
    conversation_id: int
    title: str
    chat_type: str
    created_at: datetime
    updated_at: datetime


class StockChatConversationListResponse(BaseModel):
    user_id: int
    total_count: int
    items: List[StockChatConversationItem] = Field(
        default_factory=list,
    )


class StockChatConversationMessageItem(BaseModel):
    message_id: int
    user_message: str
    agent_response: str
    referenced_stock_id: Optional[int] = None
    used_tools: Optional[str] = None
    disclaimer: Optional[str] = None
    created_at: datetime


class StockChatConversationMessagesResponse(BaseModel):
    conversation_id: int
    title: str
    total_count: int
    items: List[StockChatConversationMessageItem] = Field(
        default_factory=list,
    )