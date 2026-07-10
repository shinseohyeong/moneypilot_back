# app/rag/ingestors/agent_chat_ingestor.py

from app.rag.metadata import RagCreatedBy, RagDomain, RagSourceType
from app.rag.rag_service import upsert_rag_document


def build_agent_chat_turn_text(
    user_message: str,
    assistant_answer: str,
    intent: str | None = None,
) -> str:
    """
    사용자 질문과 Agent 답변을 RAG 저장용 자연어 문서로 변환한다.
    """

    text = ""

    if intent:
        text += f"대화 의도는 {intent}입니다. "

    text += (
        f"사용자 질문: {user_message}\n"
        f"Agent 답변: {assistant_answer}"
    )

    return text


def should_store_chat_turn_to_rag(
    user_message: str,
    assistant_answer: str,
    intent: str | None = None,
) -> bool:
    """
    너무 짧거나 의미 없는 대화는 RAG 저장에서 제외한다.
    """

    if not user_message or not assistant_answer:
        return False

    normalized = user_message.strip()

    if len(normalized) < 5:
        return False

    skip_keywords = [
        "ㅇㅋ",
        "오케이",
        "고마워",
        "ㄱㅅ",
        "ㅋㅋ",
        "ㅎㅎ",
    ]

    if normalized in skip_keywords:
        return False

    if intent == "unknown":
        return False

    return True


def ingest_agent_chat_turn(
    user_id: int,
    session_id: int,
    user_message_id: int,
    assistant_message_id: int,
    user_message: str,
    assistant_answer: str,
    intent: str | None = None,
    chat_type: str = "consumption",
    used_tools: list[str] | None = None,
) -> dict | None:
    """
    Agent 대화 한 turn을 RAG에 저장한다.
    user 질문 + assistant 답변을 하나의 문서로 저장한다.
    """

    if not should_store_chat_turn_to_rag(
        user_message=user_message,
        assistant_answer=assistant_answer,
        intent=intent,
    ):
        return None

    content = build_agent_chat_turn_text(
        user_message=user_message,
        assistant_answer=assistant_answer,
        intent=intent,
    )

    document_key = (
        f"user:{user_id}:agent_chat:"
        f"session:{session_id}:turn:{assistant_message_id}"
    )

    return upsert_rag_document(
        user_id=user_id,
        domain=RagDomain.AGENT_CHAT,
        source_type=RagSourceType.CHAT_TURN,
        source_id=assistant_message_id,
        document_key=document_key,
        content=content,
        metadata={
            "session_id": str(session_id),
            "user_message_id": str(user_message_id),
            "assistant_message_id": str(assistant_message_id),
            "chat_type": chat_type,
            "intent": intent,
            "used_tools": ",".join(used_tools or []),
            "created_by": RagCreatedBy.AGENT,
        },
    )