# ============================================================
# 파일 위치: app/rag/ingestors/stock_news_ingestor.py
# 역할:
#   - DB에 저장된 뉴스 요약과 섹터 인사이트를
#     팀 공통 RAG 컬렉션에 저장합니다.
#   - 주식/뉴스 문서는 사용자 공통 데이터이므로 user_id=None으로 저장합니다.
# ============================================================

from typing import Any

from sqlalchemy.orm import Session

from app.rag.metadata import (
    RagDomain,
    RagSourceType,
)
from app.rag.rag_service import (
    upsert_rag_document,
)
from app.repositories.stock_rag_repository import (
    StockRagRepository,
)


SECTOR_INSIGHT_SOURCE_TYPE = "sector_insight"


def _get_source_id(
    document: dict[str, Any],
) -> str:
    """
    RAG 문서의 source_id를 안전하게 가져옵니다.
    """

    metadata = document.get("metadata") or {}

    source_id = metadata.get("source_id")

    if source_id is not None:
        return str(source_id)

    return str(document.get("id"))


def _upsert_stock_rag_document(
    document: dict[str, Any],
    source_type: str,
) -> dict[str, Any]:
    """
    StockRagRepository에서 생성한 문서를
    팀 공통 RAG 구조로 저장합니다.
    """

    document_id = str(document["id"])
    content = document.get("content") or ""
    metadata = document.get("metadata") or {}

    return upsert_rag_document(
        # 뉴스와 섹터 정보는 모든 사용자가 공유하는 공용 데이터입니다.
        user_id=None,
        domain=RagDomain.STOCK_NEWS,
        source_type=source_type,
        source_id=_get_source_id(document),
        document_key=(
            f"{RagDomain.STOCK_NEWS}:{document_id}"
        ),
        content=content,
        metadata=metadata,
    )


def ingest_stock_news_documents(
    db: Session,
    news_limit: int = 100,
    sector_limit: int = 50,
) -> dict[str, Any]:
    """
    뉴스 요약과 섹터 인사이트를 공통 RAG 컬렉션에 저장합니다.

    기존 문서는 동일한 document_key 기준으로 갱신됩니다.
    """

    repository = StockRagRepository(db)

    news_documents = (
        repository.list_news_summary_documents(
            limit=news_limit,
        )
    )

    sector_documents = (
        repository.list_sector_insight_documents(
            limit=sector_limit,
        )
    )

    if not news_documents and not sector_documents:
        return {
            "success": False,
            "domain": RagDomain.STOCK_NEWS,
            "indexed_document_count": 0,
            "indexed_chunk_count": 0,
            "failed_document_keys": [],
            "message": (
                "RAG에 저장할 주식 뉴스 또는 "
                "섹터 인사이트 데이터가 없습니다."
            ),
        }

    indexed_document_count = 0
    indexed_chunk_count = 0
    failed_document_keys: list[str] = []

    # --------------------------------------------------------
    # 뉴스 요약 문서 저장
    # --------------------------------------------------------
    for document in news_documents:
        result = _upsert_stock_rag_document(
            document=document,
            source_type=RagSourceType.NEWS,
        )

        if result.get("success"):
            indexed_document_count += 1
            indexed_chunk_count += int(
                result.get("chunk_count") or 0
            )
        else:
            failed_document_keys.append(
                str(document.get("id"))
            )

    # --------------------------------------------------------
    # 섹터 인사이트 문서 저장
    # --------------------------------------------------------
    for document in sector_documents:
        result = _upsert_stock_rag_document(
            document=document,
            source_type=(
                SECTOR_INSIGHT_SOURCE_TYPE
            ),
        )

        if result.get("success"):
            indexed_document_count += 1
            indexed_chunk_count += int(
                result.get("chunk_count") or 0
            )
        else:
            failed_document_keys.append(
                str(document.get("id"))
            )

    success = indexed_document_count > 0

    return {
        "success": success,
        "domain": RagDomain.STOCK_NEWS,
        "news_document_count": len(
            news_documents
        ),
        "sector_document_count": len(
            sector_documents
        ),
        "indexed_document_count": (
            indexed_document_count
        ),
        "indexed_chunk_count": (
            indexed_chunk_count
        ),
        "failed_document_keys": (
            failed_document_keys
        ),
        "message": (
            "주식 뉴스 RAG 문서 저장을 완료했습니다."
            if success
            else "주식 뉴스 RAG 문서 저장에 실패했습니다."
        ),
    }