from enum import Enum
from typing import Any

from app.rag.chunkers import chunk_text
from app.rag.embeddings import embed_text, embed_texts
from app.rag.vector_store import get_rag_collection


def normalize_metadata_value(
    value: Any,
) -> str | int | float | bool:
    """
    ChromaDB metadata에 저장할 수 있는 형태로 값을 변환한다.

    Enum은 value 값을 사용하고,
    지원하지 않는 객체는 문자열로 변환한다.
    """

    if isinstance(value, Enum):
        value = value.value

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    return str(value)


def clean_metadata(
    metadata: dict[str, Any],
) -> dict[str, str | int | float | bool]:
    """
    ChromaDB metadata에서 None 값을 제거하고,
    각 값을 저장 가능한 타입으로 변환한다.
    """

    return {
        key: normalize_metadata_value(value)
        for key, value in metadata.items()
        if value is not None
    }


def build_rag_where(
    user_id: int | None = None,
    domain: str | Enum | None = None,
    month: str | None = None,
    extra_filters: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    ChromaDB 검색용 where 조건을 동적으로 생성한다.

    조건이 한 개이면:
    {
        "user_id": 1
    }

    조건이 여러 개이면:
    {
        "$and": [
            {"user_id": 1},
            {"domain": "spending"}
        ]
    }

    month가 None이면 검색 조건에 포함하지 않는다.
    """

    conditions: list[dict[str, Any]] = []

    if user_id is not None:
        conditions.append(
            {
                "user_id": user_id,
            }
        )

    if domain is not None:
        conditions.append(
            {
                "domain": normalize_metadata_value(
                    domain
                ),
            }
        )

    # 월이 있는 경우에만 필터에 추가한다.
    if month:
        conditions.append(
            {
                "month": month,
            }
        )

    if extra_filters:
        for key, value in extra_filters.items():
            if value is None:
                continue

            conditions.append(
                {
                    key: normalize_metadata_value(
                        value
                    ),
                }
            )

    if not conditions:
        return None

    if len(conditions) == 1:
        return conditions[0]

    return {
        "$and": conditions,
    }


def upsert_rag_document(
    user_id: int | None,
    domain: str | Enum,
    source_type: str,
    source_id: int | str,
    document_key: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    문서를 청크로 분할하고 임베딩한 뒤
    ChromaDB에 저장하거나 갱신한다.

    동일한 document_key가 존재하면 기존 청크를 삭제하고
    새로운 청크로 교체한다.
    """

    collection = get_rag_collection()

    base_metadata: dict[str, Any] = {
        "user_id": user_id,
        "domain": domain,
        "source_type": source_type,
        "source_id": str(source_id),
        "document_key": document_key,
    }

    merged_metadata = {
        **(metadata or {}),
        **base_metadata,
    }

    cleaned_metadata = clean_metadata(
        merged_metadata
    )

    chunks = chunk_text(content)

    if not chunks:
        return {
            "success": False,
            "document_key": document_key,
            "chunk_count": 0,
            "message": (
                "저장할 RAG 문서 내용이 없습니다."
            ),
        }

    embeddings = embed_texts(chunks)

    ids = [
        f"{document_key}:chunk:{index}"
        for index in range(len(chunks))
    ]

    metadatas = [
        {
            **cleaned_metadata,
            "chunk_index": index,
        }
        for index in range(len(chunks))
    ]

    # 이전 문서가 더 많은 청크를 가지고 있었을 수 있으므로,
    # 기존 document_key 문서를 먼저 제거한다.
    collection.delete(
        where={
            "document_key": document_key,
        }
    )

    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return {
        "success": True,
        "document_key": document_key,
        "chunk_count": len(chunks),
        "message": "RAG 문서 저장 성공",
    }


def search_rag_documents(
    query: str,
    user_id: int | None = None,
    domain: str | Enum | None = None,
    month: str | None = None,
    n_results: int = 5,
    extra_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    사용자 질문과 유사한 RAG 문서를 검색한다.

    month가 있으면 해당 월만 검색하고,
    month가 없으면 월 조건 없이 전체 문서에서 검색한다.
    """

    collection = get_rag_collection()

    where = build_rag_where(
        user_id=user_id,
        domain=domain,
        month=month,
        extra_filters=extra_filters,
    )

    query_embedding = embed_text(query)

    query_kwargs: dict[str, Any] = {
        "query_embeddings": [
            query_embedding,
        ],
        "n_results": n_results,
        "include": [
            "documents",
            "metadatas",
            "distances",
        ],
    }

    # where가 존재할 때만 ChromaDB에 전달한다.
    if where is not None:
        query_kwargs["where"] = where

    results = collection.query(
        **query_kwargs,
    )

    result_docs = (
        results.get("documents", [[]])[0]
        or []
    )

    result_metadatas = (
        results.get("metadatas", [[]])[0]
        or []
    )

    result_distances = (
        results.get("distances", [[]])[0]
        or []
    )

    documents: list[dict[str, Any]] = []

    for index, document in enumerate(result_docs):
        metadata = (
            result_metadatas[index]
            if index < len(result_metadatas)
            else {}
        )

        distance = (
            result_distances[index]
            if index < len(result_distances)
            else None
        )

        documents.append(
            {
                "content": document,
                "metadata": metadata,
                # Chroma distance는 낮을수록 유사하다.
                "distance": distance,
            }
        )

    if not documents:
        if month:
            message = (
                f"{month}의 관련 소비 분석 문서를 "
                "찾지 못했습니다."
            )

        else:
            message = (
                "관련 RAG 문서를 찾지 못했습니다."
            )

        return {
            "success": False,
            "documents": [],
            "data": None,
            "message": message,
        }

    return {
        "success": True,
        "documents": documents,
        "data": {
            "query": query,
            "month": month,
            "documents": documents,
        },
        "message": "RAG 검색 성공",
    }


def delete_rag_document_by_key(
    document_key: str,
) -> dict[str, Any]:
    """
    document_key에 해당하는 모든 청크를 삭제한다.
    """

    collection = get_rag_collection()

    collection.delete(
        where={
            "document_key": document_key,
        }
    )

    return {
        "success": True,
        "document_key": document_key,
        "message": "RAG 문서 삭제 성공",
    }


def delete_rag_documents_by_user(
    user_id: int,
) -> dict[str, Any]:
    """
    특정 사용자의 모든 RAG 문서를 삭제한다.
    """

    collection = get_rag_collection()

    collection.delete(
        where={
            "user_id": user_id,
        }
    )

    return {
        "success": True,
        "user_id": user_id,
        "message": "사용자 RAG 문서 삭제 성공",
    }