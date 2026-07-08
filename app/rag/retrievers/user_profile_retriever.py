"""
유저 프로필 RAG 문서를 검색하는 retriever 모듈
UserProfileRetriever가 검색 로직을 감싸줌
5번 담당이 에이전트 graph.py의 tool 리스트에 등록하여 사용할 예정
"""
from app.rag.rag_constants import RagDomain, RagFeature
from app.rag.rag_service import RagService


class UserProfileRetriever:
    """ 유저 프로필 RAG 문서 검색 전용 Retriever """

    def __init__(self):
        self.rag_service = RagService()

    def search_user_profile_docs(
        self,
        user_id: int,
        query: str,
        n_results: int = 3,
    ) -> list[dict]:
        """
        mp_rag_002 — 유저 프로필 문서 RAG 검색.
        user_id 필터 + 쿼리 유사도 검색, 상위 3개 반환.
        """
        where_filter = self._build_profile_filter(user_id=user_id)

        return self.rag_service.search(
            query=query,
            where=where_filter,
            n_results=n_results,
        )

    def _build_profile_filter(
        self,
        user_id: int,
    ) -> dict:
        """유저 프로필 검색용 Chroma metadata filter 생성"""
        filters = [
            {"user_id": user_id},
            {"domain": RagDomain.USER_PROFILE},
            {"feature": RagFeature.FINANCE_PROFILE},
        ]

        return {
            "$and": filters,
        }
