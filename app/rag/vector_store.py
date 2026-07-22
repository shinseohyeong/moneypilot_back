# app/rag/vector_store.py

import os
from typing import Any

import chromadb

from app.rag.embeddings import embed_texts


CHROMA_DB_PATH = os.getenv(
    "CHROMA_DB_PATH",
    "./chroma_db",
)

FINANCIAL_PRODUCTS_COLLECTION_NAME = os.getenv(
    "FINANCIAL_PRODUCTS_COLLECTION_NAME",
    "financial_products",
)

COMMON_RAG_COLLECTION_NAME = os.getenv(
    "COMMON_RAG_COLLECTION_NAME",
    "finance_agent_rag_bge_m3_v1",
)


client = chromadb.PersistentClient(
    path=CHROMA_DB_PATH,
)


# ============================================================
# 금융상품 전용 컬렉션
# ============================================================

financial_products_collection = (
    client.get_or_create_collection(
        name=FINANCIAL_PRODUCTS_COLLECTION_NAME,
    )
)

# 기존 코드 호환용 별칭
collection = financial_products_collection


# ============================================================
# 공통 Agent RAG 컬렉션
# ============================================================

common_rag_collection = (
    client.get_or_create_collection(
        name=COMMON_RAG_COLLECTION_NAME,
    )
)


def save_documents(
    documents: list[dict[str, Any]],
    batch_size: int = 5,
) -> None:
    """
    금융상품 문서를 financial_products 컬렉션에 저장합니다.
    """

    print(
        "금융상품 컬렉션 기존 문서 수:",
        financial_products_collection.count(),
    )

    for start in range(
        0,
        len(documents),
        batch_size,
    ):
        print(f"배치 시작: {start}")

        batch = documents[
            start:start + batch_size
        ]

        contents = [
            doc["content"]
            for doc in batch
        ]

        embeddings = embed_texts(
            contents
        )

        financial_products_collection.upsert(
            ids=[
                str(start + index)
                for index in range(
                    len(batch)
                )
            ],
            documents=contents,
            embeddings=embeddings,
            metadatas=[
                doc["metadata"]
                for doc in batch
            ],
        )

        print(
            f"{start + len(batch)}"
            f"/{len(documents)} 저장 완료"
        )


def search_documents(
    query: str,
    top_k: int = 3,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    금융상품 문서를 financial_products 컬렉션에서 검색합니다.
    """

    embedding = embed_texts(
        [query]
    )[0]

    where_filter = None

    if metadata:
        conditions = [
            {
                key: value,
            }
            for key, value
            in metadata.items()
        ]

        if len(conditions) == 1:
            where_filter = conditions[0]

        else:
            where_filter = {
                "$and": conditions,
            }

    query_kwargs: dict[str, Any] = {
        "query_embeddings": [
            embedding,
        ],
        "n_results": top_k,
    }

    if where_filter is not None:
        query_kwargs["where"] = (
            where_filter
        )

    return financial_products_collection.query(
        **query_kwargs,
    )


def get_rag_collection():
    """
    기존 금융상품 코드 호환용 함수입니다.

    기존 코드가 기대하던 financial_products 컬렉션을 반환합니다.
    """

    return financial_products_collection


def get_common_rag_collection():
    """
    소비분석, Agent 대화, 주식 뉴스 등
    공통 금융 Agent RAG 컬렉션을 반환합니다.
    """

    return common_rag_collection