"""
유저 프로필 RAG 문서를 검색/삭제하는 retriever 모듈
"""
from app.rag.metadata import RagDomain
from app.rag.rag_service import (
    search_rag_documents,
    delete_rag_documents_by_user,
)


class UserProfileRetriever:
    """유저 프로필 RAG 문서 검색/삭제 전용 Retriever"""

    def search_user_profile_docs(
        self,
        user_id: int,
        query: str,
        n_results: int = 3,
    ) -> dict:
        """mp_rag_002 — 유저 프로필 문서 RAG 검색"""
        return search_rag_documents(
            query=query,
            user_id=user_id,
            domain=RagDomain.FINANCE_PROFILE,
            n_results=n_results,
        )

    def delete_user_profile_docs(
        self,
        user_id: int,
    ) -> dict:
        """mp_rag_003 — 유저 RAG 문서 삭제 (탈퇴 시)"""
        return delete_rag_documents_by_user(user_id=user_id)
