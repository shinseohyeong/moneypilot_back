# app/rag/rag_service.py

from typing import Any

from app.rag.chunkers import chunk_text
from app.rag.embeddings import embed_texts, embed_text
from app.rag.vector_store import get_rag_collection


async def upsert_rag_document(
    user_id: int | None,
    domain: str,
    source_type: str,
    source_id: int | str,
    document_key: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    collection = get_rag_collection()

    base_metadata = {
        "user_id": user_id,
        "domain": domain,
        "source_type": source_type,
        "source_id": str(source_id),
        "document_key": document_key,
    }

    if metadata:
        base_metadata.update(metadata)

    chunks = chunk_text(content)
    embeddings = embed_texts(chunks)

    ids = [
        f"{document_key}:chunk:{idx}"
        for idx in range(len(chunks))
    ]

    metadatas = [
        {
            **base_metadata,
            "chunk_index": idx,
        }
        for idx in range(len(chunks))
    ]

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


async def search_rag_documents(
    query: str,
    user_id: int | None = None,
    domain: str | None = None,
    n_results: int = 5,
) -> dict[str, Any]:
    collection = get_rag_collection()

    where = {}

    if user_id is not None:
        where["user_id"] = user_id

    if domain is not None:
        where["domain"] = domain

    query_embedding = embed_text(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where if where else None,
    )

    documents = []

    result_docs = results.get("documents", [[]])[0]
    result_metadatas = results.get("metadatas", [[]])[0]
    result_distances = results.get("distances", [[]])[0]

    for doc, metadata, distance in zip(result_docs, result_metadatas, result_distances):
        documents.append(
            {
                "content": doc,
                "metadata": metadata,
                "score": distance,
            }
        )

    return {
        "success": True,
        "documents": documents,
        "message": "RAG 검색 성공",
    }


async def delete_rag_document_by_key(document_key: str) -> dict[str, Any]:
    collection = get_rag_collection()

    collection.delete(
        where={"document_key": document_key}
    )

    return {
        "success": True,
        "document_key": document_key,
        "message": "RAG 문서 삭제 성공",
    }


async def delete_rag_documents_by_user(user_id: int) -> dict[str, Any]:
    collection = get_rag_collection()

    collection.delete(
        where={"user_id": user_id}
    )

    return {
        "success": True,
        "user_id": user_id,
        "message": "사용자 RAG 문서 삭제 성공",
    }