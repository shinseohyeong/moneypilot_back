import json

from sqlalchemy.orm import Session

from app.agent.graph import run_agent_graph
from app.repositories.agent_chat_repository import AgentChatRepository
from app.rag.ingestors.agent_chat_ingestor import ingest_agent_chat_turn


def build_history_context(messages) -> list[dict]:
    """
    DB 메시지 목록을 Agent에 넘길 history 형태로 변환한다.
    """

    history = []

    for message in messages:
        history.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    return history


def extract_used_tools(result: dict) -> list[str]:
    """
    Agent 실행 결과에서 사용된 Tool 이름 목록을 추출한다.
    """

    used_tools = []

    intent = result.get("intent")

    if result.get("tool_result"):
        if intent == "spending_summary":
            used_tools.append("monthly_spending_summary_tool")
        elif intent == "spending_category":
            used_tools.append("monthly_category_spending_tool")
        elif intent == "spending_expense_type":
            used_tools.append("monthly_expense_type_tool")
        elif intent == "spending_report":
            used_tools.append("monthly_spending_report_tool")
        else:
            used_tools.append("spending_analysis_tool")

    if result.get("rag_result"):
        used_tools.append("user_spending_rag_tool")

    if result.get("chat_rag_result"):
        used_tools.append("agent_chat_rag_tool")

    return used_tools


def extract_referenced_summary_id(result: dict) -> int | None:
    """
    Tool 결과에서 참조한 monthly_spending_summary id를 추출한다.
    """

    tool_result = result.get("tool_result")

    if not tool_result:
        return None

    data = tool_result.get("data")

    if not data:
        return None

    return data.get("summary_id")


def run_agent(
    db: Session,
    user_id: int,
    message: str,
    session_id: int | None = None,
) -> dict:
    """
    Agent 실행 진입점.
    session 생성/조회, history 조회, 메시지 저장, Agent 실행, 대화 RAG 저장을 담당한다.
    """

    chat_repository = AgentChatRepository(db)

    if session_id:
        chat_session = chat_repository.get_session_by_id(
            session_id=session_id,
            user_id=user_id,
        )

        if not chat_session:
            chat_session = chat_repository.create_session(
                user_id=user_id,
                title=message[:30],
                chat_type="consumption",
            )
    else:
        chat_session = chat_repository.create_session(
            user_id=user_id,
            title=message[:30],
            chat_type="consumption",
        )

    recent_messages = chat_repository.list_recent_messages(
        session_id=chat_session.id,
        limit=10,
    )

    history = build_history_context(recent_messages)

    user_chat_message = chat_repository.create_message(
        session_id=chat_session.id,
        user_id=user_id,
        role="user",
        content=message,
    )

    result = run_agent_graph(
        db=db,
        user_id=user_id,
        session_id=int(chat_session.id),
        message=message,
        history=history,
    )

    answer = result.get("answer", "")
    used_tools = extract_used_tools(result)
    referenced_summary_id = extract_referenced_summary_id(result)

    assistant_chat_message = chat_repository.create_message(
        session_id=chat_session.id,
        user_id=user_id,
        role="assistant",
        content=answer,
        intent=result.get("intent"),
        used_tools=json.dumps(used_tools, ensure_ascii=False),
        referenced_summary_id=referenced_summary_id,
    )

    chat_rag_save_result = None

    try:
        chat_rag_save_result = ingest_agent_chat_turn(
            user_id=user_id,
            session_id=int(chat_session.id),
            user_message_id=int(user_chat_message.id),
            assistant_message_id=int(assistant_chat_message.id),
            user_message=message,
            assistant_answer=answer,
            intent=result.get("intent"),
            chat_type=chat_session.chat_type,
            used_tools=used_tools,
        )
    except Exception as e:
        print(f"Agent 대화 RAG 저장 실패: {e}")

    return {
        "success": result.get("error") is None,
        "session_id": int(chat_session.id),
        "intent": result.get("intent"),
        "answer": answer,
        "tool_result": result.get("tool_result"),
        "rag_result": result.get("rag_result"),
        "chat_rag_result": result.get("chat_rag_result"),
        "history": history,
        "chat_rag_save_result": chat_rag_save_result,
        "error": result.get("error"),
    }