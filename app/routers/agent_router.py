from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.agent.runner import run_agent
from app.agent.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    AgentSessionListResponse,
    AgentSessionMessagesResponse,
)
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user_model import User
from app.repositories.agent_chat_repository import AgentChatRepository


router = APIRouter()

# # JWT 인증 적용 전 프론트 테스트용
# TEMP_USER_ID = 1


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="통합 자산관리 Agent 질문 답변",
)
def ask_agent(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentChatResponse:
    result = run_agent(
        db=db,
        user_id=current_user.id,
        session_id=request.session_id,
        message=request.message,
    )

    return AgentChatResponse.model_validate(result)


@router.get(
    "/sessions",
    response_model=AgentSessionListResponse,
    summary="사용자 Agent 대화방 목록 조회",
)
def list_agent_sessions(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentSessionListResponse:
    repository = AgentChatRepository(db)

    sessions = repository.list_sessions_by_user(
        user_id=current_user.id,
        limit=limit,
    )

    session_items = []

    for session in sessions:
        last_message = repository.get_last_message(
            session_id=int(session.id)
        )

        session_items.append(
            {
                "id": int(session.id),
                "title": session.title,
                "chat_type": session.chat_type,
                "last_message": (
                    last_message.content
                    if last_message
                    else None
                ),
                "last_message_at": (
                    last_message.created_at
                    if last_message
                    else None
                ),
                "created_at": session.created_at,
                "updated_at": session.updated_at,
            }
        )

    return AgentSessionListResponse(
        success=True,
        sessions=session_items,
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=AgentSessionMessagesResponse,
    summary="특정 Agent 대화방 메시지 조회",
)
def list_agent_session_messages(
    session_id: int,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentSessionMessagesResponse:
    repository = AgentChatRepository(db)

    session = repository.get_session_by_id(
        session_id=session_id,
        user_id=current_user.id,
    )

    if not session:
        return AgentSessionMessagesResponse(
            success=False,
            session=None,
            messages=[],
            message="대화방을 찾을 수 없습니다.",
        )

    messages = repository.list_recent_messages(
        session_id=session_id,
        limit=limit,
    )

    return AgentSessionMessagesResponse(
        success=True,
        session={
            "id": int(session.id),
            "title": session.title,
            "chat_type": session.chat_type,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        },
        messages=[
            {
                "id": int(message.id),
                "session_id": int(
                    message.session_id
                ),
                "role": message.role,
                "content": message.content,
                "intent": message.intent,
                "used_tools": message.used_tools,
                "disclaimer": message.disclaimer,
                "created_at": message.created_at,
            }
            for message in messages
        ],
        message=None,
    )