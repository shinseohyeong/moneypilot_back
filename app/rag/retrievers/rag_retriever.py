# app/rag/retrievers/rag_retriever.py

from app.rag.metadata import RagDomain
from app.rag.rag_service import search_rag_documents


async def search_user_spending_context(
    user_id: int,
    query: str,
    n_results: int = 5,
) -> dict:
    return await search_rag_documents(
        query=query,
        user_id=user_id,
        domain=RagDomain.SPENDING,
        n_results=n_results,
    )