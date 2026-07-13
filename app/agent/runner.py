import json
import logging

from sqlalchemy.orm import Session

from app.agent.graph import run_agent_graph
from app.models.agent_chat_model import AgentChatSession
from app.repositories.agent_chat_repository import AgentChatRepository
from app.rag.ingestors.agent_chat_ingestor import (
    ingest_agent_chat_turn,
)


logger = logging.getLogger(__name__)


def build_history_context(
    messages,
) -> list[dict]:
    """
    DB 메시지 목록을 Agent에 넘길 history 형태로 변환한다.
    """

    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]


def extract_used_tools(
    result: dict,
) -> list[str]:
    """
    Agent 실행 결과에서 사용된 Tool 이름 목록을 추출한다.
    """

    used_tools: list[str] = []
    intent = result.get("intent")

    if result.get("tool_result"):
        if intent == "spending_summary":
            used_tools.append(
                "monthly_spending_summary_tool"
            )

        elif intent == "spending_category":
            used_tools.append(
                "monthly_category_spending_tool"
            )

    if result.get("rag_result"):
        used_tools.append(
            "user_spending_rag_tool"
        )

    if result.get("chat_rag_result"):
        used_tools.append(
            "agent_chat_rag_tool"
        )

    return used_tools


def extract_referenced_summary_id(
    result: dict,
) -> int | None:
    """
    Tool 결과에서 참조한 monthly_spending_summary ID를 추출한다.
    """

    tool_result = result.get("tool_result")

    if not tool_result:
        return None

    data = tool_result.get("data")

    if not data:
        return None

    summary_id = data.get("summary_id")

    if summary_id is None:
        return None

    return int(summary_id)


def resolve_chat_type(
    intent: str | None,
) -> str:
    """
    Agent intent를 대화방 chat_type으로 변환한다.
    """

    if intent in {
        "spending_summary",
        "spending_category",
        "spending_report",
    }:
        return "consumption"

    return "general"


def merge_chat_type(
    current_type: str,
    new_type: str,
) -> str:
    """
    기존 대화방 유형과 새 질문 유형을 합친다.
    """

    if current_type == "general":
        return new_type

    if new_type == "general":
        return current_type

    if current_type == new_type:
        return current_type

    return "mixed"


def update_chat_session_type(
    repository: AgentChatRepository,
    chat_session: AgentChatSession,
    intent: str | None,
) -> AgentChatSession:
    """
    실행된 intent를 기준으로 대화방 유형을 갱신한다.
    """

    new_type = resolve_chat_type(intent)

    final_type = merge_chat_type(
        current_type=chat_session.chat_type,
        new_type=new_type,
    )

    if final_type == chat_session.chat_type:
        return chat_session

    return repository.update_session_chat_type(
        session=chat_session,
        chat_type=final_type,
    )


def build_failed_result(
    error: Exception,
) -> dict:
    """
    Agent Graph 실행 중 예외가 발생했을 때 사용할 결과를 만든다.
    """

    logger.exception(
        "Agent 실행 중 오류가 발생했습니다.",
        exc_info=error,
    )

    return {
        "intent": "general",
        "answer": (
            "답변을 처리하는 중 오류가 발생했습니다. "
            "Ollama 서버와 설정을 확인해주세요."
        ),
        "tool_result": None,
        "rag_result": None,
        "chat_rag_result": None,
        "error": str(error),
    }


def run_agent(
    db: Session,
    user_id: int,
    message: str,
    session_id: int | None = None,
) -> dict:
    """
    Agent 실행 진입점.

    처리 흐름:
    1. session_id가 없으면 새 대화방 생성
    2. session_id가 있으면 사용자 소유 대화방 조회
    3. 최근 대화 조회
    4. 사용자 메시지 저장
    5. Agent Graph 실행
    6. 대화방 chat_type 갱신
    7. Agent 답변 저장
    8. 정상 대화를 RAG에 저장
    """

    chat_repository = AgentChatRepository(db)

    if session_id is None:
        chat_session = chat_repository.create_session(
            user_id=user_id,
            title=message.strip()[:30] or "새 대화",
            chat_type="general",
        )

    else:
        chat_session = chat_repository.get_session_by_id(
            session_id=session_id,
            user_id=user_id,
        )

        if not chat_session:
            return {
                "success": False,
                "session_id": session_id,
                "chat_type": None,
                "intent": None,
                "answer": "대화방을 찾을 수 없습니다.",
                "assistant_message": None,
                "error": "대화방을 찾을 수 없습니다.",
            }

    current_session_id = int(chat_session.id)

    recent_messages = (
        chat_repository.list_recent_messages(
            session_id=current_session_id,
            limit=10,
        )
    )

    history = build_history_context(
        recent_messages
    )

    user_chat_message = (
        chat_repository.create_message(
            session_id=current_session_id,
            user_id=user_id,
            role="user",
            content=message,
        )
    )

    try:
        result = run_agent_graph(
            db=db,
            user_id=user_id,
            session_id=current_session_id,
            message=message,
            history=history,
        )

    except Exception as error:
        result = build_failed_result(error)

    answer = (
        result.get("answer")
        or "답변을 생성하지 못했습니다."
    )

    chat_session = update_chat_session_type(
        repository=chat_repository,
        chat_session=chat_session,
        intent=result.get("intent"),
    )

    used_tools = extract_used_tools(result)

    used_tools_json = (
        json.dumps(
            used_tools,
            ensure_ascii=False,
        )
        if used_tools
        else None
    )

    referenced_summary_id = (
        extract_referenced_summary_id(result)
    )

    assistant_chat_message = (
        chat_repository.create_message(
            session_id=current_session_id,
            user_id=user_id,
            role="assistant",
            content=answer,
            intent=result.get("intent"),
            used_tools=used_tools_json,
            referenced_summary_id=(
                referenced_summary_id
            ),
        )
    )

    if result.get("error") is None:
        try:
            ingest_agent_chat_turn(
                user_id=user_id,
                session_id=current_session_id,
                user_message_id=int(
                    user_chat_message.id
                ),
                assistant_message_id=int(
                    assistant_chat_message.id
                ),
                user_message=message,
                assistant_answer=answer,
                intent=result.get("intent"),
                chat_type=chat_session.chat_type,
                used_tools=used_tools,
            )

        except Exception:
            logger.exception(
                "Agent 대화 RAG 저장에 실패했습니다."
            )

    return {
        "success": result.get("error") is None,
        "session_id": current_session_id,
        "chat_type": chat_session.chat_type,
        "intent": result.get("intent"),
        "answer": answer,
        "assistant_message": {
            "id": int(assistant_chat_message.id),
            "session_id": int(
                assistant_chat_message.session_id
            ),
            "role": assistant_chat_message.role,
            "content": assistant_chat_message.content,
            "intent": assistant_chat_message.intent,
            "used_tools": (
                assistant_chat_message.used_tools
            ),
            "disclaimer": (
                assistant_chat_message.disclaimer
            ),
            "created_at": (
                assistant_chat_message.created_at
            ),
        },
        "error": result.get("error"),
    }