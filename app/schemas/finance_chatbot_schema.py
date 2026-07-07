# ==========================================
# 파일 위치: app/schemas/finance_chatbot_schema.py
# 역할:
# - 소비 데이터 기반 투자 참고 챗봇 요청/응답 Schema 정의
# - API JSON 필드는 snake_case로 통일
# ==========================================

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class FinanceChatbotRequest(BaseModel):
    user_id: int = Field(..., description="사용자 ID")
    message: str = Field(..., min_length=1, description="사용자 질문")


class FinanceSpendingContextItem(BaseModel):
    category: str
    category_amount: str
    category_ratio: str
    transaction_count: int


class FinanceChatbotResponse(BaseModel):
    user_id: int
    chat_type: Literal["finance"] = "finance"
    user_message: str
    answer: str

    risk_type: str
    risk_label: str

    month: Optional[str] = None
    monthly_salary: Optional[str] = None
    fixed_expense: Optional[str] = None
    total_spending: Optional[str] = None
    estimated_available_amount: Optional[str] = None

    categories: List[FinanceSpendingContextItem] = Field(default_factory=list)

    disclaimer: str