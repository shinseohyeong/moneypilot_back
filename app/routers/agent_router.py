from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.runner import run_agent
from app.agent.schemas import AgentChatRequest, AgentChatResponse
from app.core.database import get_db
from app.repositories.agent_chat_repository import AgentChatRepository


router = APIRouter()


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    summary="통합 자산관리 Agent 질문 답변",
)
def ask_agent(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
) -> AgentChatResponse:
    return run_agent(
        db=db,
        user_id=request.user_id,
        session_id=request.session_id,
        message=request.message,
    )


@router.get(
    "/sessions",
    summary="사용자 Agent 대화방 목록 조회",
)
def list_agent_sessions(
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    repository = AgentChatRepository(db)

    sessions = repository.list_sessions_by_user(
        user_id=user_id,
        limit=20,
    )

    return {
        "success": True,
        "sessions": [
            {
                "id": int(session.id),
                "user_id": int(session.user_id),
                "title": session.title,
                "chat_type": session.chat_type,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
            }
            for session in sessions
        ],
    }


@router.get(
    "/sessions/{session_id}/messages",
    summary="특정 Agent 대화방 메시지 조회",
)
def list_agent_session_messages(
    session_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    repository = AgentChatRepository(db)

    session = repository.get_session_by_id(
        session_id=session_id,
        user_id=user_id,
    )

    if not session:
        return {
            "success": False,
            "message": "대화방을 찾을 수 없습니다.",
            "messages": [],
        }

    messages = repository.list_recent_messages(
        session_id=session_id,
        limit=50,
    )

    return {
        "success": True,
        "session": {
            "id": int(session.id),
            "title": session.title,
            "chat_type": session.chat_type,
        },
        "messages": [
            {
                "id": int(message.id),
                "role": message.role,
                "content": message.content,
                "intent": message.intent,
                "used_tools": message.used_tools,
                "referenced_summary_id": (
                    int(message.referenced_summary_id)
                    if message.referenced_summary_id
                    else None
                ),
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }