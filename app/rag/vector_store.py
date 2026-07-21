# app/rag/vector_store.py

import chromadb

from app.rag.embeddings import embed_texts


client = chromadb.PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="financial_products"
)

def save_documents(
    documents,
    batch_size=5
):
    """
    금융상품 문서를 batch 단위로 ChromaDB 저장
    """

    print(collection.count())

    for start in range(0, len(documents), batch_size):

        print(f"배치 시작: {start}")

        batch = documents[start:start + batch_size]

        contents = [
            doc["content"]
            for doc in batch
        ]

        embeddings = embed_texts(contents)

        collection.upsert(
            ids=[
                str(start + i)
                for i in range(len(batch))
            ],
            documents=contents,
            embeddings=embeddings,
            metadatas=[
                doc["metadata"]
                for doc in batch
            ],
        )

        print(
            f"{start + len(batch)}/{len(documents)} 저장 완료"
        )


def search_documents(
    query: str,
    top_k: int = 3,
    metadata: dict | None = None
):
    """
    사용자 질문과 비슷한 금융상품 문서 검색
    """

    embedding = embed_texts([query])[0]

    where_filter = None

    if metadata:
        conditions = [
            {key: value}
            for key, value in metadata.items()
        ]

        if len(conditions) == 1:
            where_filter = conditions[0]
        else:
            where_filter = {
                "$and": conditions
            }

    result = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where_filter
    )

    return result

def get_rag_collection():
    return collection