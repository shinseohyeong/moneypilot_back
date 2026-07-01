# ============================================================
# 파일 위치: app/routers/chatbot_router.py
# 역할:
#   - 주식 챗봇 / 소비 기반 금융 챗봇 API 엔드포인트를 정의합니다.
# ============================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.schemas.stock_chatbot_schema import (
    StockChatbotRequest,
    StockChatbotResponse,
)
from app.services.stock_chatbot_service import StockChatbotService

from app.schemas.finance_chatbot_schema import (
    FinanceChatbotRequest,
    FinanceChatbotResponse,
)
from app.services.finance_chatbot_service import FinanceChatbotService


router = APIRouter()


def get_stock_chatbot_service(
    db: Session = Depends(get_db),
) -> StockChatbotService:
    return StockChatbotService(db)


def get_finance_chatbot_service(
    db: Session = Depends(get_db),
) -> FinanceChatbotService:
    return FinanceChatbotService(db)


@router.post(
    "/stock",
    response_model=StockChatbotResponse,
    summary="주식 챗봇 질문 답변",
)
def ask_stock_chatbot(
    request: StockChatbotRequest,
    service: StockChatbotService = Depends(get_stock_chatbot_service),
) -> StockChatbotResponse:
    return service.ask_stock_chatbot(request)


@router.post(
    "/finance",
    response_model=FinanceChatbotResponse,
    summary="소비 데이터 기반 투자 참고 답변",
)
def ask_finance_chatbot(
    request: FinanceChatbotRequest,
    service: FinanceChatbotService = Depends(get_finance_chatbot_service),
) -> FinanceChatbotResponse:
    return service.create_finance_answer(request)