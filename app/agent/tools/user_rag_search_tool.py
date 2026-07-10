from app.rag.metadata import RagDomain
from app.rag.rag_service import search_rag_documents


def search_user_spending_rag_tool(
    user_id: int,
    query: str,
) -> dict:
    """
    사용자의 소비 분석 RAG 문서를 검색한다.
    """

    return search_rag_documents(
        query=query,
        user_id=user_id,
        domain=RagDomain.SPENDING,
        n_results=5,
    )


def search_user_agent_chat_rag_tool(
    user_id: int,
    query: str,
) -> dict:
    """
    사용자의 과거 Agent 대화 RAG 문서를 검색한다.
    """

    return search_rag_documents(
        query=query,
        user_id=user_id,
        domain=RagDomain.AGENT_CHAT,
        n_results=5,
    )