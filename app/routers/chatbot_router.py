# ============================================================
# 파일 위치: app/routers/chatbot_router.py
# 역할:
#   - 주식 챗봇 / 소비 기반 금융 챗봇 API 엔드포인트를 정의합니다.
#   - 주식 챗봇 API는 JWT에서 인증된 사용자 ID를 사용합니다.
# ============================================================

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user_model import User

from app.schemas.stock_chatbot_schema import (
    StockChatbotRequest,
    StockChatbotResponse,
    StockChatHistoryResponse,
    StockChatConversationListResponse,
    StockChatConversationMessagesResponse,
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
    current_user: User = Depends(get_current_user),
    service: StockChatbotService = Depends(
        get_stock_chatbot_service
    ),
) -> StockChatbotResponse:
    return service.ask_stock_chatbot(
        request=request,
        user_id=current_user.id,
    )


# 기존 테스트 호환용 API입니다.
# 신규 프론트 대화 목록에서는 사용하지 않습니다.
@router.get(
    "/stock/history",
    response_model=StockChatHistoryResponse,
    summary="주식 챗봇 대화기록 조회",
)
def get_stock_chat_history(
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: StockChatbotService = Depends(
        get_stock_chatbot_service
    ),
) -> StockChatHistoryResponse:
    return service.get_stock_chat_history(
        user_id=current_user.id,
        limit=limit,
    )


@router.post(
    "/finance",
    response_model=FinanceChatbotResponse,
    summary="소비 데이터 기반 투자 참고 답변",
)
def ask_finance_chatbot(
    request: FinanceChatbotRequest,
    service: FinanceChatbotService = Depends(
        get_finance_chatbot_service
    ),
) -> FinanceChatbotResponse:
    # 금융 챗봇은 다른 담당자의 기능이므로
    # 이번 변경 범위에서는 기존 로직을 유지합니다.
    return service.create_finance_answer(request)


@router.get(
    "/stock/conversations",
    response_model=StockChatConversationListResponse,
    summary="주식 챗봇 대화방 목록 조회",
)
def get_stock_conversations(
    limit: int = Query(default=30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: StockChatbotService = Depends(
        get_stock_chatbot_service
    ),
) -> StockChatConversationListResponse:
    return service.get_stock_conversations(
        user_id=current_user.id,
        limit=limit,
    )


@router.get(
    "/stock/conversations/{conversation_id}/messages",
    response_model=StockChatConversationMessagesResponse,
    summary="주식 챗봇 대화방 메시지 조회",
)
def get_stock_conversation_messages(
    conversation_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    service: StockChatbotService = Depends(
        get_stock_chatbot_service
    ),
) -> StockChatConversationMessagesResponse:
    return service.get_stock_conversation_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )