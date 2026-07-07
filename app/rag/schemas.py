# app/rag/schemas.py

from typing import Any
from pydantic import BaseModel, Field


class RagDocumentCreate(BaseModel):
    user_id: int | None = None
    domain: str
    source_type: str
    source_id: int | str
    document_key: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagSearchResult(BaseModel):
    content: str
    metadata: dict[str, Any]
    score: float | None = None


class RagSearchResponse(BaseModel):
    success: bool
    documents: list[RagSearchResult]
    message: str = "RAG 검색 성공"