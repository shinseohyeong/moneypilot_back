# ============================================================
# 파일 위치: app/schemas/stock_chatbot_schema.py
# 역할:
#   - 주식 챗봇 요청/응답 schema를 정의합니다.
#   - 사용자의 질문과 챗봇 답변 구조를 관리합니다.
# ============================================================

from typing import Optional, List
from pydantic import BaseModel, Field


class StockChatbotRequest(BaseModel):
    """
    주식 챗봇 질문 요청 schema입니다.
    """

    user_id: int = Field(..., description="사용자 ID")
    message: str = Field(..., description="사용자 질문")
    stock_id: Optional[int] = Field(
        default=None,
        description="특정 종목에 대한 질문일 경우 종목 ID",
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

    user_id: int
    chat_type: str = "stock"
    user_message: str
    answer: str

    risk_type: str
    risk_label: str

    disclaimer: str

    items: List[StockChatbotStockBrief] = []