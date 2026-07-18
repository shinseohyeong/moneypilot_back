"""
금융 프로필을 RAG 문서로 저장하는 ingestor 모듈 (mp_rag_001)
"""
from app.rag.rag_service import upsert_rag_document
from app.rag.builders.finance_profile_builder import build_finance_profile_documents


def ingest_finance_profile(user_id: int, profile) -> None:
    """
    금융 프로필을 RAG에 저장한다. 프로필 등록/수정 시 호출한다.
    """
    documents = build_finance_profile_documents(profile)
    for doc in documents:
        upsert_rag_document(
            user_id=user_id,
            domain=doc["metadata"]["domain"],
            source_type=doc["metadata"]["source_type"],
            source_id=doc["metadata"]["source_id"],
            document_key=doc["id"],
            content=doc["content"],
            metadata=doc["metadata"],
        )
