# app/rag/vector_store.py

import chromadb

from app.rag.metadata import CHROMA_DB_PATH, RAG_COLLECTION_NAME


_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)


def get_rag_collection():
    return _client.get_or_create_collection(
        name=RAG_COLLECTION_NAME,
        metadata={"description": "Finance Agent RAG Collection"},
    )